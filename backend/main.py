from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import httpx
import uuid
import os
from dotenv import load_dotenv
import io
import logging
import time

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found!")

app = FastAPI()

# CORS Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChromaDB and Embedding Settings
chroma_client = chromadb.PersistentClient("./chroma_db")

try:
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    logger.info("Default embedding function loaded successfully.")

    # Create the collection
    collection = chroma_client.get_or_create_collection(
        name="csv_chunks",
        embedding_function=default_ef
    )
    logger.info("ChromaDB collection created successfully.")

except Exception as e:
    logger.error(f"Embedding model or collection could not be initialized: {str(e)}")
    raise RuntimeError(f"Embedding model or collection could not be initialized: {str(e)}")

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="File not found")

    try:
        logger.info(f"Uploading CSV: {file.filename}")

        # Process CSV in memory
        contents = await file.read()

        # Check file content
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        # Read from memory with Pandas, support various formats
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
        except Exception as csv_error:
            logger.warning(f"Failed to read as CSV: {str(csv_error)}")
            try:
                df = pd.read_excel(io.BytesIO(contents))
                logger.info("File read as Excel successfully.")
            except Exception as excel_error:
                logger.error(f"File format not recognized: {str(excel_error)}")
                raise HTTPException(
                    status_code=400,
                    detail="File format not supported. Please upload a valid CSV or Excel file."
                )

        if df.empty:
            raise HTTPException(status_code=400, detail="DataFrame is empty")

        logger.info(f"DataFrame created: {len(df)} rows, {len(df.columns)} columns")

        chunks = []
        metadatas = []
        ids = []

        for i, row in df.iterrows():
            row_values = [str(x) if x is not None else "" for x in row.values]
            row_text = " | ".join(row_values)
            chunks.append(row_text)
            metadatas.append({"row_index": int(i), "source": file.filename})
            ids.append(str(uuid.uuid4()))

        if not chunks:
            raise HTTPException(status_code=400, detail="No data to process found")

        logger.info(f"Adding {len(chunks)} chunks to ChromaDB...")

        batch_size = 500
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            collection.add(
                documents=chunks[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
            logger.info(f"Batch {i//batch_size + 1} added: {i}-{end_idx}")

        return {"status": "success", "chunks_indexed": len(chunks)}

    except HTTPException as he:
        logger.error(f"HTTP Error: {str(he.detail)}")
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    if not question or question.strip() == "":
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        logger.info(f"Question received: {question}")

        results = collection.query(
            query_texts=[question],
            n_results=5
        )

        if not results['documents'] or len(results['documents'][0]) == 0:
            return JSONResponse({"answer": "No information related to this question was found in the database.", "context": []})

        context_chunks = results['documents'][0]
        context = "\n".join(context_chunks)

        logger.info(f"Found context chunks: {len(context_chunks)}")

        if not GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not defined")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        body = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Use the context to answer accurately."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            "temperature": 0.3
        }

        logger.info("Sending request to Groq API...")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=body
                    )

                    if response.status_code != 200:
                        logger.error(f"Groq API error (Attempt {attempt+1}/{max_retries}): {response.status_code} - {response.text}")
                        if attempt == max_retries - 1:
                            return JSONResponse(
                                status_code=response.status_code,
                                content={"status": "error", "message": f"Groq API error: {response.text}"}
                            )
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                    data = response.json()
                    break

            except httpx.ConnectTimeout:
                logger.warning(f"Groq API connection timeout (Attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.warning("Could not connect to Groq API, trying alternative solution...")

                    answer = f"Sorry, there was a problem connecting to Groq API. However, I found the following information related to your query:\n\n"
                    answer += "\n".join([f"- {chunk.split(' | ')[0]}" for chunk in context_chunks[:3]])
                    answer += "\n\nFor more information, please try again or contact your system administrator."

                    return JSONResponse({"answer": answer, "context": context_chunks})

                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            except Exception as e:
                logger.error(f"Groq API error: {str(e)}")
                if attempt == max_retries - 1:
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": f"Groq API error: {str(e)}"}
                    )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

        answer = data["choices"][0]["message"]["content"]
        logger.info("Answer received successfully")

        return JSONResponse({"answer": answer, "context": context_chunks})

    except HTTPException as he:
        logger.error(f"HTTP Error: {str(he.detail)}")
        raise
    except Exception as e:
        logger.error(f"Ask question error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/")
async def root():
    return {"message": "CSV RAG API active. Use /upload or /ask endpoints."}

@app.get("/health")
async def health_check():
    try:
        collection_count = len(chroma_client.list_collections())
        return {
            "status": "ok",
            "collections_count": collection_count,
            "collection_items": collection.count()
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
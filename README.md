# CSVBot

CSVBot is a full-stack application for examining CSV files using AI-powered features. This project includes a Python backend and a React frontend.

## Features

- **CSV Upload & Management**: Upload CSV files.
- **AI-Powered Query**: Ask questions about CSV data in natural language and get    intelligent answers.
- **RESTful API**: Backend exposes endpoints for file management and AI queries.
- **Frontend**: Modern React app with Vite, supporting fast development and hot reloading.
- **Dockerized**: Easily run the whole stack with Docker Compose.

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- Or, for manual setup:
  - Python 3.11+
  - Node.js 18+

### Running with Docker Compose (Recommended)

1. Clone the repository:
   ```sh
   git clone <repo_url>
   cd CSVBot
   ```
2. Create the required `.env` file for the backend (see below).
3. Start all services:
   ```sh
   docker-compose up --build
   ```
4. Access the frontend at [http://localhost:5173](http://localhost:5173)
   and the backend API at [http://localhost:8000](http://localhost:8000)

### Manual Local Development

#### Backend
```sh
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Or create your .env as below
python main.py
```

#### Frontend
```sh
cd frontend
npm install
npm run dev
```

### .env file Example (backend/.env)
```
GROQ_API_KEY=your_groq_key_here
```

- `GROQ_API_KEY`: Your Groq API key for AI features


## Project Structure
```
CSVBot/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── LICENSE
```

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

Feel free to contribute or open issues for improvements!

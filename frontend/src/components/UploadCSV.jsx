import React, { useState } from 'react'
import axios from 'axios'

export default function UploadCSV() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    
    setStatus('Uploading...')
    try {
      const res = await axios.post('http://localhost:8000/upload', formData)
      setStatus(`Success: Uploaded ${res.data.chunks_indexed} chunks.`)
    } catch (error) {
      console.error('Upload error:', error)
      setStatus(`Error: ${error.response?.data?.message || error.message}`)
    }
  }

  return (
    <div className="mb-6">
      <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} />
      <button onClick={handleUpload} className="ml-2 px-4 py-1 bg-blue-600 text-white rounded">Upload</button>
      <p className="text-sm mt-1 text-gray-500">{status}</p>
    </div>
  )
}
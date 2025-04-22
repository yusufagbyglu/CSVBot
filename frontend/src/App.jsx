import React, { useState } from 'react'
import UploadCSV from './components/UploadCSV'

import Chat from './components/Chat'

export default function App() {
  const [messages, setMessages] = useState([])

  const handleNewMessage = (question, answer, context) => {
    setMessages(prev => [...prev, { question, answer, context }])
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">🧠 CSV RAG Chatbot</h1>
      <UploadCSV />
      <Chat messages={messages} onNewMessage={handleNewMessage} />
    </div>
  )
}
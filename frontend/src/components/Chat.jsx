import React, { useState } from 'react'
import axios from 'axios'

export default function Chat({ messages, onNewMessage }) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAsk = async () => {
    if (!question.trim()) return
    setLoading(true)
    const formData = new FormData()
    formData.append('question', question)
    const res = await axios.post('http://localhost:8000/ask', formData)
    onNewMessage(question, res.data.answer, res.data.context)
    setQuestion('')
    setLoading(false)
  }

  return (
    <div>
      <div className="flex mb-4">
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 p-2 border rounded"
        />
        <button onClick={handleAsk} className="ml-2 px-4 py-1 bg-green-600 text-white rounded" disabled={loading}>
          {loading ? 'Asking...' : 'Ask'}
        </button>
      </div>
      <div className="space-y-4">
        {messages.map((m, idx) => (
          <div key={idx} className="p-4 border rounded bg-white shadow">
            <p><strong>Q:</strong> {m.question}</p>
            <p><strong>A:</strong> {m.answer}</p>
            <details>
              <summary className="cursor-pointer text-sm text-gray-600 mt-2">Context</summary>
              <pre className="text-xs text-gray-500 whitespace-pre-wrap">{m.context.join('\n')}</pre>
            </details>
          </div>
        ))}
      </div>
    </div>
  )
}

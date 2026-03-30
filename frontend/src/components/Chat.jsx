import { useState } from 'react'
import axios from 'axios'
import { API_BASE } from '../api'

export default function Chat({ isAuthenticated }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const text = input
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await axios.post(`${API_BASE}/api/chat`, {
        message: text,
      })
      const assistantMessage = { role: 'assistant', content: response.data.response }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const msg = err?.response?.data?.error || 'Unable to send message.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return <div className="mt-8 text-center text-gray-500">Connect Google to start chatting.</div>
  }

  return (
    <div className="mx-auto max-w-3xl p-4">
      <div className="mb-4 h-96 overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
        {messages.length === 0 && (
          <div className="text-gray-500">
            Ask about recent emails, meetings, or upcoming schedule.
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div
              className={`inline-block rounded-lg p-3 ${
                msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && <div className="text-gray-500">Thinking...</div>}
      </div>

      {error && <div className="mb-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask Echo..."
          className="flex-1 rounded-lg border p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="rounded-lg bg-blue-500 px-6 py-3 text-white hover:bg-blue-600 disabled:bg-gray-400"
        >
          Send
        </button>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import axios from 'axios'

export default function OAuth({ onAuthSuccess }) {
  const [syncing, setSyncing] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const syncData = async () => {
    setSyncing(true)
    setStatus('Syncing data...')
    setError('')
    try {
      const response = await axios.post('http://localhost:5000/api/sync')
      setStatus(`Synced ${response.data.synced_emails} emails and ${response.data.synced_events} events.`)
    } catch (err) {
      const msg = err?.response?.data?.error || 'Failed to sync data.'
      setError(msg)
      setStatus('')
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    const listener = (event) => {
      if (event?.data?.type === 'auth_success') {
        onAuthSuccess()
        syncData()
      }
    }
    window.addEventListener('message', listener)
    return () => window.removeEventListener('message', listener)
  }, [onAuthSuccess])

  const handleGoogleLogin = async () => {
    setError('')
    setStatus('')
    try {
      const response = await axios.get('http://localhost:5000/auth/google/login')
      window.open(response.data.auth_url, '_blank', 'width=500,height=650')
    } catch (err) {
      const msg = err?.response?.data?.error || 'Google login failed.'
      setError(msg)
    }
  }

  return (
    <div className="p-6 text-center">
      <button
        onClick={handleGoogleLogin}
        disabled={syncing}
        className="rounded-lg bg-green-500 px-6 py-3 text-lg text-white hover:bg-green-600 disabled:bg-gray-400"
      >
        Connect Google Account
      </button>
      {status && <p className="mt-4 text-gray-700">{status}</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { API_BASE } from '../api'

export default function OAuth({ onGoogleConnected }) {
  const [error, setError] = useState('')

  const handleMessage = useCallback(
    (event) => {
      if (event?.data?.type === 'auth_success') {
        onGoogleConnected?.()
      }
    },
    [onGoogleConnected]
  )

  useEffect(() => {
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [handleMessage])

  const handleGoogleLogin = async () => {
    setError('')
    try {
      const response = await axios.get(`${API_BASE}/auth/google/login`)
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
        className="rounded-lg bg-green-500 px-6 py-3 text-lg text-white hover:bg-green-600"
      >
        Connect Google Account
      </button>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      <p className="mx-auto mt-3 max-w-md text-sm text-gray-500">
        After you sign in, we will sync your recent mail and calendar into the
        Echo assistant automatically.
      </p>
    </div>
  )
}

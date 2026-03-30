import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { API_BASE } from '../api'

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
    </svg>
  )
}

function TwinAILogo() {
  return (
    <div className="flex items-center gap-2">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="white"/>
        </svg>
      </div>
      <span className="text-lg font-semibold text-gray-900">TwinAI</span>
    </div>
  )
}

export default function Landing({ onGoogleConnected }) {
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)

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

  useEffect(() => {
    if (!polling) return
    let cancelled = false
    let attempts = 0

    const tick = async () => {
      if (cancelled || attempts > 20) return
      attempts += 1
      try {
        const res = await axios.get(`${API_BASE}/api/auth/status`)
        if (res.data?.authenticated) {
          onGoogleConnected?.()
          return
        }
      } catch {
        // ignore and keep polling
      }
      if (!cancelled) {
        setTimeout(tick, 2000)
      }
    }

    tick()
    return () => {
      cancelled = true
    }
  }, [polling, onGoogleConnected])

  const handleGoogleLogin = async () => {
    setError('')
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE}/auth/google/login`)
      window.open(response.data.auth_url, '_blank', 'width=500,height=650')
      setPolling(true)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to start Google sign-in. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-white">
      {/* Dot grid background */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage: 'radial-gradient(circle, #d1d5db 1.5px, transparent 1.5px)',
          backgroundSize: '28px 28px',
        }}
      />
      {/* Soft gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/60 via-white/40 to-purple-50/40" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-10 py-6">
        <TwinAILogo />
        <a
          href="https://github.com"
          className="text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors"
        >
          GitHub
        </a>
      </nav>

      {/* Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center px-6 pt-24 pb-32 text-center">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
          <span className="text-xs font-medium text-indigo-700">Powered by OpenAI + Google APIs</span>
        </div>

        <h1 className="max-w-2xl text-5xl font-bold tracking-tight text-gray-900 leading-tight">
          Your AI-powered<br />
          <span className="text-indigo-600">second brain</span>
        </h1>

        <p className="mt-5 max-w-lg text-lg text-gray-500 leading-relaxed">
          TwinAI connects to your Gmail and Google Calendar to build a personal
          AI assistant that knows your schedule, emails, and context — so you
          can ask it anything about your own life.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="flex items-center gap-3 rounded-xl border border-gray-300 bg-white px-7 py-3.5 text-sm font-semibold text-gray-700 shadow-sm transition-all hover:shadow-md hover:border-gray-400 disabled:opacity-60"
          >
            <GoogleIcon />
            {loading ? 'Opening Google…' : 'Sign in with Google'}
          </button>
          <p className="text-xs text-gray-400">
            We only request read-only access to Gmail & Calendar
          </p>
        </div>

        {error && (
          <div className="mt-5 max-w-sm rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Feature highlights */}
        <div className="mt-20 grid max-w-3xl grid-cols-3 gap-6 text-left">
          {[
            {
              icon: '📧',
              title: 'Gmail Integration',
              desc: 'Indexes your recent inbox so your twin can answer questions about emails.',
            },
            {
              icon: '📅',
              title: 'Calendar Awareness',
              desc: 'Knows your schedule — past and upcoming — down to the day.',
            },
            {
              icon: '🤖',
              title: 'Ask Anything',
              desc: 'Ask in plain English. Your twin answers from your actual data, not guesswork.',
            },
          ].map((f) => (
            <div key={f.title} className="rounded-2xl border border-gray-200 bg-white/80 p-5 shadow-sm backdrop-blur">
              <div className="mb-2 text-2xl">{f.icon}</div>
              <div className="text-sm font-semibold text-gray-900">{f.title}</div>
              <div className="mt-1 text-sm text-gray-500">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

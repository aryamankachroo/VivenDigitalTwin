import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { API_BASE } from './api'
import Chat from './components/Chat'
import ConnectionPanel from './components/ConnectionPanel'
import OAuth from './components/OAuth'

axios.defaults.withCredentials = true

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [lastSyncedAt, setLastSyncedAt] = useState(null)
  const [syncError, setSyncError] = useState('')

  const refreshStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/auth/status`)
      setIsAuthenticated(Boolean(response.data.authenticated))
      setLastSyncedAt(response.data.last_synced_at ?? null)
    } catch {
      setIsAuthenticated(false)
      setLastSyncedAt(null)
    }
  }, [])

  const runSync = useCallback(async () => {
    setSyncError('')
    try {
      const response = await axios.post(`${API_BASE}/api/sync`)
      setLastSyncedAt(response.data.last_synced_at ?? null)
      return { ok: true, data: response.data }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Sync failed'
      setSyncError(msg)
      return { ok: false, error: msg }
    }
  }, [])

  useEffect(() => {
    refreshStatus()
  }, [refreshStatus])

  const handleGoogleConnected = useCallback(async () => {
    await refreshStatus()
    await runSync()
  }, [runSync, refreshStatus])

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <h1 className="mb-8 text-center text-4xl font-bold">My Digital Twin</h1>

        {isAuthenticated && (
          <ConnectionPanel
            lastSyncedAt={lastSyncedAt}
            syncError={syncError}
            onSync={runSync}
          />
        )}

        {!isAuthenticated && (
          <OAuth onGoogleConnected={handleGoogleConnected} />
        )}

        <Chat isAuthenticated={isAuthenticated} />
      </div>
    </div>
  )
}

export default App

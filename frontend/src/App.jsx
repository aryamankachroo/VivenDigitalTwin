import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { API_BASE } from './api'
import Landing from './components/Landing'
import Onboarding from './components/Onboarding'
import Sidebar from './components/Sidebar'
import DashboardHome from './components/DashboardHome'
import Integrations from './components/Integrations'
import Settings from './components/Settings'

axios.defaults.withCredentials = true

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const [booted, setBooted] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  // tab inside 'app': 'home' | 'integrations' | 'settings'
  const [activeTab, setActiveTab] = useState('home')

  const [userEmail, setUserEmail] = useState('')
  const [syncStats, setSyncStats] = useState(null)
  const [lastSyncedAt, setLastSyncedAt] = useState(null)
  const [syncError, setSyncError] = useState('')
  const [upcomingEvents, setUpcomingEvents] = useState([])

  // ── data fetchers ──────────────────────────────────────────────────────────

  const refreshStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/auth/status`)
      if (res.data.authenticated) {
        setIsAuthenticated(true)
        setUserEmail(res.data.user_email || '')
        setLastSyncedAt(res.data.last_synced_at ?? null)
        return true
      }
      setIsAuthenticated(false)
      return false
    } catch {
      setIsAuthenticated(false)
      return false
    }
  }, [])

  const fetchUpcoming = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/calendar/upcoming`)
      setUpcomingEvents(res.data.events || [])
    } catch {
      setUpcomingEvents([])
    }
  }, [])

  const runSync = useCallback(async () => {
    setSyncError('')
    try {
      const res = await axios.post(`${API_BASE}/api/sync`)
      setLastSyncedAt(res.data.last_synced_at ?? null)
      setSyncStats(res.data)
      if (res.data.user_email) setUserEmail(res.data.user_email)
      return { ok: true, data: res.data }
    } catch (err) {
      if (err?.response?.status === 401) {
        setIsAuthenticated(false)
        setUserEmail('')
        navigate('/signin', { replace: true, state: { from: location.pathname } })
        return { ok: false, error: 'Not authenticated' }
      }
      const msg = err?.response?.data?.error || 'Sync failed'
      setSyncError(msg)
      return { ok: false, error: msg }
    }
  }, [navigate, location.pathname])

  // ── boot: check if already authenticated ──────────────────────────────────

  useEffect(() => {
    refreshStatus().then((authenticated) => {
      if (authenticated) {
        fetchUpcoming()
      }
      setBooted(true)
    })
  }, [refreshStatus, fetchUpcoming])

  // ── oauth success → onboarding ─────────────────────────────────────────────

  const handleGoogleConnected = useCallback(async () => {
    const ok = await refreshStatus()
    if (ok) {
      navigate('/onboarding', { replace: true })
    }
  }, [refreshStatus, navigate])

  // ── onboarding "build" → run sync then open dashboard ─────────────────────

  const handleBuildTwin = useCallback(async () => {
    const result = await runSync()
    if (result.ok) await fetchUpcoming()
    navigate('/', { replace: true })
  }, [runSync, fetchUpcoming])

  // ── sync again (from dashboard) ────────────────────────────────────────────

  const handleSyncAgain = useCallback(async () => {
    const result = await runSync()
    if (result.ok) await fetchUpcoming()
    return result
  }, [runSync, fetchUpcoming])

  // ── render ─────────────────────────────────────────────────────────────────

  if (!booted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    )
  }

  const AppShell = (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userEmail={userEmail}
        onAccountClick={() => {
          if (!isAuthenticated) navigate('/signin')
        }}
      />

      <main className="flex-1 overflow-hidden">
        {activeTab === 'home' && (
          <DashboardHome
            userEmail={userEmail}
            syncStats={syncStats}
            lastSyncedAt={lastSyncedAt}
            syncError={syncError}
            upcomingEvents={upcomingEvents}
            onSync={handleSyncAgain}
          />
        )}
        {activeTab === 'integrations' && (
          <div className="h-full overflow-y-auto">
            <Integrations
              lastSyncedAt={lastSyncedAt}
              syncStats={syncStats}
              onSync={handleSyncAgain}
            />
          </div>
        )}
        {activeTab === 'settings' && (
          <div className="h-full overflow-y-auto">
            <Settings userEmail={userEmail} />
          </div>
        )}
      </main>
    </div>
  )

  return (
    <Routes>
      <Route
        path="/signin"
        element={<Landing onGoogleConnected={handleGoogleConnected} />}
      />
      <Route
        path="/onboarding"
        element={
          isAuthenticated ? (
            <Onboarding onBuildTwin={handleBuildTwin} />
          ) : (
            <Navigate to="/signin" replace />
          )
        }
      />
      <Route
        path="/"
        element={isAuthenticated ? AppShell : <Navigate to="/signin" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

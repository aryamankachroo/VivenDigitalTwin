import { useState } from 'react'
import ChatPanel from './ChatPanel'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function formatSyncedAt(iso) {
  if (!iso) return 'Not synced yet'
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function formatEventTime(iso) {
  if (!iso) return ''
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
      return new Date(iso + 'T00:00:00').toLocaleDateString(undefined, {
        weekday: 'short', month: 'short', day: 'numeric',
      })
    }
    return new Date(iso).toLocaleString(undefined, {
      weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className={`mt-1.5 text-3xl font-bold ${accent || 'text-gray-900'}`}>{value ?? '—'}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

function EventBadge({ start }) {
  const today = new Date()
  const d = new Date(start)
  const isToday = d.toDateString() === today.toDateString()
  const isTomorrow = d.toDateString() === new Date(today.getTime() + 86400000).toDateString()
  if (isToday) return <span className="shrink-0 rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">Today</span>
  if (isTomorrow) return <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">Tomorrow</span>
  return null
}

function RightSidebar({ upcomingEvents, lastSyncedAt, syncError, onSync, syncing }) {
  return (
    <aside className="w-72 shrink-0 border-l border-gray-200 bg-white px-5 py-6 overflow-y-auto">
      <div className="mb-6">
        <div className="mb-1 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Data sync</p>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            <span className="text-xs text-gray-400">Connected</span>
          </span>
        </div>
        <p className="mb-3 text-xs text-gray-500">
          {lastSyncedAt ? `Last synced ${formatSyncedAt(lastSyncedAt)}` : 'Not synced yet'}
        </p>
        <button
          onClick={onSync}
          disabled={syncing}
          className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100 disabled:opacity-50"
        >
          {syncing ? 'Syncing…' : '↻ Sync again'}
        </button>
        {syncError && <p className="mt-2 text-xs text-red-500">{syncError}</p>}
      </div>

      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Upcoming events
        </p>
        {upcomingEvents.length === 0 ? (
          <p className="text-xs text-gray-400">No upcoming events. Try syncing first.</p>
        ) : (
          <div className="space-y-2">
            {upcomingEvents.map((ev, i) => (
              <div key={i} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-semibold leading-snug text-gray-800">{ev.summary}</p>
                  <EventBadge start={ev.start} />
                </div>
                <p className="mt-1 text-xs text-gray-400">{formatEventTime(ev.start)}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}

export default function DashboardHome({
  userEmail,
  syncStats,
  lastSyncedAt,
  syncError,
  upcomingEvents,
  onSync,
}) {
  const name = userEmail ? userEmail.split('@')[0] : 'there'
  const [syncing, setSyncing] = useState(false)

  const handleSync = async () => {
    setSyncing(true)
    await onSync()
    setSyncing(false)
  }

  return (
    <div className="flex h-screen">
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden px-8 py-7">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {greeting()}, {name}.
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here's what your twin knows about you.
          </p>
        </div>

        <div className="mb-6 grid grid-cols-3 gap-4">
          <StatCard
            label="Emails indexed"
            value={syncStats?.index_email_documents ?? '—'}
            sub="in search index"
            accent="text-indigo-600"
          />
          <StatCard
            label="Calendar events"
            value={syncStats?.index_calendar_documents ?? '—'}
            sub="±14 day window"
            accent="text-indigo-600"
          />
          <StatCard
            label="Last updated"
            value={
              lastSyncedAt
                ? new Date(lastSyncedAt).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
                : '—'
            }
            sub={
              lastSyncedAt
                ? new Date(lastSyncedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
                : 'Never synced'
            }
          />
        </div>

        {/* Chat panel fills remaining height */}
        <div className="flex-1 min-h-0">
          <ChatPanel />
        </div>
      </div>

      <RightSidebar
        upcomingEvents={upcomingEvents}
        lastSyncedAt={lastSyncedAt}
        syncError={syncError}
        onSync={handleSync}
        syncing={syncing}
      />
    </div>
  )
}

function formatSyncedAt(iso) {
  if (!iso) return 'Not synced yet'
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch { return iso }
}

function GmailIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <path fill="#EA4335" d="M6 40h6V23.8L4 18v18c0 2.2 1.8 4 2 4z" />
      <path fill="#34A853" d="M36 40h6c.2 0 4-1.8 4-4V18l-8 5.8" />
      <path fill="#4285F4" d="M36 8H12L24 17.2 36 8z" />
      <path fill="#FBBC05" d="M12 23.8V8L4 18l8 5.8z" />
      <path fill="#EA4335" d="M36 8l8 10-8 5.8V8z" />
      <path fill="#C5221F" d="M12 23.8l12 8.6 12-8.6V8L24 17.2 12 8v15.8z" />
    </svg>
  )
}

function CalendarIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <path fill="#1976D2" d="M38 6H10C7.8 6 6 7.8 6 10v28c0 2.2 1.8 4 4 4h28c2.2 0 4-1.8 4-4V10c0-2.2-1.8-4-4-4z"/>
      <path fill="#fff" d="M10 20h28v18H10z"/>
      <path fill="#1976D2" d="M14 8c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2s2-.9 2-2v-4c0-1.1-.9-2-2-2zm20 0c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2s2-.9 2-2v-4c0-1.1-.9-2-2-2z"/>
      <rect fill="#E53935" x="17" y="24" width="14" height="3" rx="1.5"/>
    </svg>
  )
}

function DriveIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <path fill="#0F9D58" d="M16 6h16l10 18H26z" />
      <path fill="#F4B400" d="M6 30l10-18 10 18-10 18z" />
      <path fill="#4285F4" d="M32 30H12l10-18h20z" />
    </svg>
  )
}

const CONNECTED = [
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Read-only access to your inbox. Indexes your 100 most recent emails for semantic search.',
    icon: <GmailIcon />,
    dataNote: '100 most recent inbox messages',
  },
  {
    id: 'calendar',
    name: 'Google Calendar',
    description: 'Read-only access to your primary calendar. Indexes events 14 days back and 14 days forward.',
    icon: <CalendarIcon />,
    dataNote: '28-day rolling window',
  },
  {
    id: 'drive',
    name: 'Google Drive',
    description: 'Read-only access to your Drive. Indexes your 30 most recent files.',
    icon: <DriveIcon />,
    dataNote: '30 most recent files',
  },
]

const COMING_SOON = [
  { name: 'Notion', emoji: '📝', desc: 'Index your notes, docs, and databases.' },
  { name: 'Slack', emoji: '💬', desc: 'Search across your DMs and channels.' },
  { name: 'LinkedIn', emoji: '🔗', desc: 'Track connections and job history.' },
  { name: 'GitHub', emoji: '🐙', desc: 'Surface your commits and pull requests.' },
]

export default function Integrations({ lastSyncedAt, onSync, syncStats }) {
  return (
    <div className="max-w-2xl px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage the data sources connected to Echo.
        </p>
      </div>

      {/* Connected */}
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Connected
      </div>
      <div className="mb-8 space-y-3">
        {CONNECTED.map((item) => (
          <div
            key={item.id}
            className="flex items-start gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-gray-100 bg-gray-50">
              {item.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-semibold text-gray-900">{item.name}</p>
                <span className="flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  Active
                </span>
              </div>
              <p className="mt-0.5 text-sm text-gray-500">{item.description}</p>
              <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                <span>Last synced: <span className="text-gray-600">{formatSyncedAt(lastSyncedAt)}</span></span>
                <span>Scope: {item.dataNote}</span>
              </div>
              {syncStats && (
                <div className="mt-1 text-xs text-gray-400">
                  {item.id === 'gmail' && `${syncStats.index_email_documents ?? '—'} email chunks in index`}
                  {item.id === 'calendar' && `${syncStats.index_calendar_documents ?? '—'} event chunks in index`}
                  {item.id === 'drive' && `${syncStats.index_drive_documents ?? '—'} file chunks in index`}
                </div>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button
                onClick={onSync}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100"
              >
                Sync now
              </button>
              <button
                disabled
                className="rounded-lg border border-red-100 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-400 cursor-not-allowed"
                title="Disconnect not available in MVP"
              >
                Disconnect
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Coming soon */}
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Coming soon
      </div>
      <div className="grid grid-cols-2 gap-3">
        {COMING_SOON.map((item) => (
          <div
            key={item.name}
            className="flex items-center gap-3 rounded-2xl border border-dashed border-gray-200 bg-gray-50/50 p-4 opacity-60"
          >
            <span className="text-xl">{item.emoji}</span>
            <div>
              <p className="text-sm font-semibold text-gray-500">{item.name}</p>
              <p className="text-xs text-gray-400">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

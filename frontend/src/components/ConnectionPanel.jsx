import { useState } from 'react'

function formatSyncedAt(iso) {
  if (!iso) return 'Not synced yet'
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

export default function ConnectionPanel({
  lastSyncedAt,
  syncError,
  onSync,
}) {
  const [busy, setBusy] = useState(false)
  const [localMsg, setLocalMsg] = useState('')

  const handleSync = async () => {
    setBusy(true)
    setLocalMsg('')
    const result = await onSync()
    if (result?.ok && result.data) {
      const d = result.data
      const fe = d.synced_emails
      const fcal = d.synced_events
      const ie = d.index_email_documents
      const ic = d.index_calendar_documents
      if (ie != null && ic != null) {
        setLocalMsg(
          `Pulled ${fe} inbox messages and ${fcal} calendar items from Google (this run). Search index now holds ${ie} email chunks and ${ic} calendar chunks.`
        )
      } else {
        setLocalMsg(`Synced ${fe} emails and ${fcal} events.`)
      }
    }
    setBusy(false)
  }

  return (
    <div className="mx-auto mb-6 max-w-3xl rounded-xl border border-green-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2">
          <span
            className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-green-500"
            title="Google connected"
          />
          <div>
            <p className="font-medium text-gray-800">Google connected</p>
            <p className="text-sm text-gray-600">
              Last index refresh:{' '}
              <span className="font-medium text-gray-800">
                {formatSyncedAt(lastSyncedAt)}
              </span>
            </p>
            <p className="mt-1 text-xs text-gray-500">
              “Last email” answers use live Gmail when needed; sync updates the
              search index for broader questions.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleSync}
          disabled={busy}
          className="shrink-0 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:bg-gray-400"
        >
          {busy ? 'Syncing…' : 'Sync again'}
        </button>
      </div>
      {localMsg && (
        <p className="mt-2 text-sm text-green-700">{localMsg}</p>
      )}
      {syncError && (
        <p className="mt-2 text-sm text-red-600">{syncError}</p>
      )}
    </div>
  )
}

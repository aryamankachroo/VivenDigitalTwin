import { useState } from 'react'

function Section({ title, children }) {
  return (
    <div className="border-b border-gray-100 pb-8 last:border-0">
      <h2 className="mb-5 text-sm font-semibold text-gray-900">{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <div className="mb-4">
      <label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>
      {children}
      {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  )
}

export default function Settings({ userEmail }) {
  const name = userEmail ? userEmail.split('@')[0] : ''
  const [saved, setSaved] = useState(false)

  const handleSave = (e) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="max-w-xl px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Manage your profile and preferences.</p>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        <Section title="Profile">
          <div className="mb-5 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-xl font-bold text-indigo-700">
              {userEmail ? userEmail.charAt(0).toUpperCase() : '?'}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{userEmail || 'Not signed in'}</p>
              <p className="text-xs text-gray-400">Google Account</p>
            </div>
          </div>

          <Field label="Display name" hint="Used in greetings on your dashboard.">
            <input
              type="text"
              defaultValue={name}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </Field>
          <Field label="Email">
            <input
              type="email"
              defaultValue={userEmail}
              disabled
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3.5 py-2.5 text-sm text-gray-400"
            />
          </Field>
        </Section>

        <Section title="Preferences">
          <Field label="Timezone" hint="Used to interpret calendar events correctly.">
            <select className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100">
              <option>America/New_York (UTC−5)</option>
              <option>America/Chicago (UTC−6)</option>
              <option>America/Denver (UTC−7)</option>
              <option>America/Los_Angeles (UTC−8)</option>
              <option>Europe/London (UTC±0)</option>
              <option>Asia/Kolkata (UTC+5:30)</option>
            </select>
          </Field>
          <Field label="Language">
            <select className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100">
              <option>English (US)</option>
              <option>English (UK)</option>
              <option>Spanish</option>
              <option>French</option>
              <option>German</option>
            </select>
          </Field>
        </Section>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            Save changes
          </button>
          {saved && (
            <span className="flex items-center gap-1.5 text-sm text-green-600">
              <svg width="14" height="14" viewBox="0 0 12 12" fill="none">
                <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Saved
            </span>
          )}
        </div>
      </form>

      {/* Danger zone */}
      <div className="mt-10 rounded-2xl border border-red-200 bg-red-50/40 p-5">
        <h2 className="mb-1 text-sm font-semibold text-red-700">Danger zone</h2>
        <p className="mb-4 text-xs text-red-500">
          These actions are irreversible. Please be certain.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            disabled
            className="rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            title="Not available in MVP"
          >
            Delete all my data
          </button>
          <button
            disabled
            className="rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            title="Not available in MVP"
          >
            Disconnect all integrations
          </button>
        </div>
        <p className="mt-3 text-xs text-red-400">
          These features are disabled in the current MVP build.
        </p>
      </div>
    </div>
  )
}

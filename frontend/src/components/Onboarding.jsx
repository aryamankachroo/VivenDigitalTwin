import { useEffect, useState } from 'react'

function StepIndicator({ current }) {
  return (
    <div className="flex items-center gap-3">
      {[1, 2].map((n) => (
        <div key={n} className="flex items-center gap-3">
          <div
            className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
              n < current
                ? 'bg-indigo-600 text-white'
                : n === current
                ? 'bg-indigo-600 text-white ring-4 ring-indigo-100'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            {n < current ? (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              n
            )}
          </div>
          {n < 2 && (
            <div className={`h-px w-16 ${n < current ? 'bg-indigo-600' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

function ServiceCard({ icon, name, description, connected }) {
  return (
    <div
      className={`flex flex-col gap-4 rounded-2xl border p-6 transition-all ${
        connected ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white shadow-sm border border-gray-100">
          {icon}
        </div>
        {connected ? (
          <div className="flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 6l3 3 5-5" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-xs font-semibold text-green-700">Connected</span>
          </div>
        ) : (
          <div className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-500">
            Pending
          </div>
        )}
      </div>
      <div>
        <div className="font-semibold text-gray-900">{name}</div>
        <div className="mt-1 text-sm text-gray-500">{description}</div>
      </div>
    </div>
  )
}

export default function Onboarding({ onBuildTwin }) {
  const [step, setStep] = useState(1)

  const handleContinue = () => {
    setStep(2)
    onBuildTwin()
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-6 py-16">
      <div className="w-full max-w-5xl">
        {/* Logo */}
        <div className="mb-10 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="white"/>
            </svg>
          </div>
          <span className="text-lg font-semibold text-gray-900">Echo</span>
        </div>

        <StepIndicator current={step} />

        {step === 1 && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-gray-900">Connect your data sources</h2>
            <p className="mt-2 text-gray-500">
              Your Google account has been authorized. All data sources below are ready.
            </p>

            <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
              <ServiceCard
                connected
                name="Gmail"
                description="Read-only access to your inbox — recent emails will be indexed."
                icon={
                  <svg width="24" height="24" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#EA4335" d="M6 40h6V23.8L4 18v18c0 2.2 1.8 4 4-2z" />
                    <path fill="#34A853" d="M36 40h6c2.2 0 4-1.8 4-4V18l-8 5.8" />
                    <path fill="#4285F4" d="M36 8H12L24 17.2 36 8z" />
                    <path fill="#FBBC05" d="M12 23.8V8L4 18l8 5.8z" />
                    <path fill="#EA4335" d="M36 8l8 10-8 5.8V8z" />
                    <path fill="#C5221F" d="M12 23.8l12 8.6 12-8.6V8L24 17.2 12 8v15.8z" />
                  </svg>
                }
              />
              <ServiceCard
                connected
                name="Google Calendar"
                description="Read-only access to your primary calendar — events will be indexed."
                icon={
                  <svg width="24" height="24" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#1976D2" d="M38 6H10C7.8 6 6 7.8 6 10v28c0 2.2 1.8 4 4 4h28c2.2 0 4-1.8 4-4V10c0-2.2-1.8-4-4-4z"/>
                    <path fill="#fff" d="M10 20h28v18H10z"/>
                    <path fill="#1976D2" d="M14 8c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2s2-.9 2-2v-4c0-1.1-.9-2-2-2zm20 0c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2s2-.9 2-2v-4c0-1.1-.9-2-2-2z"/>
                    <rect fill="#E53935" x="17" y="24" width="14" height="3" rx="1.5"/>
                    <rect fill="#1976D2" x="14" y="30" width="6" height="3" rx="1.5"/>
                    <rect fill="#1976D2" x="22" y="30" width="6" height="3" rx="1.5"/>
                  </svg>
                }
              />
              <ServiceCard
                connected
                name="Google Drive"
                description="Read-only access to your Drive — your 30 most recent files will be indexed."
                icon={
                  <svg width="24" height="24" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#0F9D58" d="M16 6h16l10 18H26z" />
                    <path fill="#F4B400" d="M6 30l10-18 10 18-10 18z" />
                    <path fill="#4285F4" d="M32 30H12l10-18h20z" />
                  </svg>
                }
              />
            </div>

            <button
              onClick={handleContinue}
              className="mt-8 w-full rounded-xl bg-indigo-600 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
            >
              Build Echo →
            </button>
            <p className="mt-3 text-center text-xs text-gray-400">
              This will index your last 100 emails, calendar events from the past 14 days and next 14 days, and your last 30 Drive files.
            </p>
          </div>
        )}

        {step === 2 && (
          <div className="mt-8 flex flex-col items-center text-center">
            <div className="relative mb-8 flex h-20 w-20 items-center justify-center">
              <div className="absolute inset-0 animate-ping rounded-full bg-indigo-100" />
              <div className="absolute inset-2 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
              <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="white"/>
                </svg>
              </div>
            </div>

            <h2 className="text-2xl font-bold text-gray-900">Echo is being built</h2>
            <p className="mt-2 text-gray-500">
              Indexing your emails, calendar events, and Drive files — this takes about 30–60 seconds.
            </p>

            <div className="mt-8 w-full space-y-3 text-left">
              {[
                'Fetching recent inbox messages…',
                'Fetching calendar events (past & upcoming)…',
                'Fetching your most recent Drive files…',
                'Building semantic search index…',
              ].map((step, i) => (
                <BuildingStep key={i} text={step} delay={i * 1.2} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function BuildingStep({ text, delay }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay * 1000)
    return () => clearTimeout(t)
  }, [delay])

  if (!visible) return null
  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 shadow-sm animate-[fadeIn_0.4s_ease]">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600 shrink-0" />
      {text}
    </div>
  )
}

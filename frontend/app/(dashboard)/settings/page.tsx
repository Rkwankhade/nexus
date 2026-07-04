'use client'

import { useState } from 'react'

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || '')

  return (
    <div className="max-w-xl space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary">Platform preferences</p>
      </div>

      <div className="card space-y-4 p-4">
        <div>
          <label className="mb-1 block text-xs text-text-secondary">API Base URL</label>
          <input
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
        </div>
        <p className="text-xs text-text-muted">
          Additional preferences (notification thresholds, theme, MFA) can be added here as
          the corresponding backend endpoints come online.
        </p>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { Search, Bell, User, Sun, Moon } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'

export default function TopBar() {
  const openAlerts = useAppStore((s) => s.openAlerts)
  const [dark, setDark] = useState(true)
  const [query, setQuery] = useState('')

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-bg-secondary/80 px-6 backdrop-blur">
      <div className="flex w-96 items-center gap-2 rounded-md border border-border bg-bg-card px-3 py-1.5">
        <Search size={14} className="text-text-muted" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search targets, findings, jobs..."
          className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />
      </div>

      <div className="flex items-center gap-4">
        <button
          className="relative rounded-md p-2 text-text-secondary hover:bg-bg-elevated hover:text-accent"
          aria-label="Notifications"
        >
          <Bell size={18} />
          {openAlerts.length > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent-red px-1 text-[10px] font-bold text-white">
              {openAlerts.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setDark((d) => !d)}
          className="rounded-md p-2 text-text-secondary hover:bg-bg-elevated hover:text-accent"
          aria-label="Toggle theme"
        >
          {dark ? <Moon size={18} /> : <Sun size={18} />}
        </button>

        <button className="flex items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-sm text-text-secondary hover:bg-bg-elevated">
          <User size={16} />
          <span>Account</span>
        </button>
      </div>
    </header>
  )
}

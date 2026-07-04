'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle } from 'lucide-react'
import { getJson } from '@/lib/api'
import type { LogEntry } from '@/types'

const SOURCES = ['all', 'edr', 'firewall', 'ids', 'application', 'auth', 'cloud'] as const

export default function SiemPage() {
  const [source, setSource] = useState<(typeof SOURCES)[number]>('all')

  const { data: logs, isLoading } = useQuery<LogEntry[]>({
    queryKey: ['siem-logs', source],
    queryFn: () =>
      getJson<LogEntry[]>('/blueteam/siem/logs', {
        source: source === 'all' ? undefined : source,
        limit: 150,
      }),
    refetchInterval: 8000,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary">
            <Activity size={18} className="text-accent" /> SIEM
          </h1>
          <p className="text-sm text-text-secondary">Aggregated log stream across sources</p>
        </div>
        <div className="flex gap-1">
          {SOURCES.map((s) => (
            <button
              key={s}
              onClick={() => setSource(s)}
              className={`rounded-md px-2.5 py-1.5 text-xs capitalize ${
                source === s
                  ? 'bg-bg-elevated text-accent'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[11px] uppercase text-text-muted">
              <th className="px-4 py-2 font-medium">Time</th>
              <th className="px-4 py-2 font-medium">Source</th>
              <th className="px-4 py-2 font-medium">Host</th>
              <th className="px-4 py-2 font-medium">Event</th>
              <th className="px-4 py-2 font-medium">Message</th>
              <th className="px-4 py-2 font-medium">Matched Rules</th>
            </tr>
          </thead>
          <tbody>
            {logs?.map((l) => (
              <tr key={l.id} className="border-t border-border hover:bg-bg-elevated/50">
                <td className="px-4 py-2 font-mono text-[11px] text-text-muted">
                  {new Date(l.ingested_at).toLocaleTimeString()}
                </td>
                <td className="px-4 py-2 font-mono text-xs text-text-secondary">{l.source}</td>
                <td className="px-4 py-2 font-mono text-xs text-text-secondary">
                  {l.host || '—'}
                </td>
                <td className="px-4 py-2 text-xs text-text-primary">{l.event_type || '—'}</td>
                <td className="max-w-sm truncate px-4 py-2 text-xs text-text-secondary">
                  {l.message}
                </td>
                <td className="px-4 py-2">
                  {l.matched_rules && l.matched_rules.length > 0 ? (
                    <span className="flex items-center gap-1 text-[11px] text-accent-red">
                      <AlertTriangle size={11} /> {l.matched_rules.join(', ')}
                    </span>
                  ) : (
                    <span className="text-[11px] text-text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
            {!isLoading && (!logs || logs.length === 0) && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-xs text-text-muted">
                  No log entries yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

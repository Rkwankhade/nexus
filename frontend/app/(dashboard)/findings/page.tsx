'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getJson } from '@/lib/api'
import RecentFindingsTable from '@/components/tools/RecentFindingsTable'
import type { Finding, Severity } from '@/types'

const SEVERITIES: (Severity | 'all')[] = ['all', 'critical', 'high', 'medium', 'low', 'info']

export default function FindingsPage() {
  const [severity, setSeverity] = useState<Severity | 'all'>('all')

  const { data: findings, isLoading } = useQuery<Finding[]>({
    queryKey: ['findings', severity],
    queryFn: () =>
      getJson<Finding[]>('/findings', severity === 'all' ? undefined : { severity }),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Findings</h1>
          <p className="text-sm text-text-secondary">All findings across every target</p>
        </div>
        <div className="flex gap-1">
          {SEVERITIES.map((s) => (
            <button
              key={s}
              onClick={() => setSeverity(s)}
              className={`rounded-md px-3 py-1.5 text-xs capitalize ${
                severity === s
                  ? 'bg-bg-elevated text-accent'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="card p-8 text-center text-sm text-text-muted">Loading findings…</div>
      ) : (
        <RecentFindingsTable findings={findings ?? []} />
      )}
    </div>
  )
}

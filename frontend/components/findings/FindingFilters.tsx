import { Search } from 'lucide-react'
import type { Severity, FindingStatus, Target } from '@/types'

const SEVERITIES: (Severity | 'all')[] = ['all', 'critical', 'high', 'medium', 'low', 'info']
const STATUSES: (FindingStatus | 'all')[] = [
  'all',
  'open',
  'confirmed',
  'false_positive',
  'remediated',
  'accepted_risk',
]

export interface FindingFilterState {
  severity: Severity | 'all'
  status: FindingStatus | 'all'
  targetId: string | 'all'
  search: string
}

export default function FindingFilters({
  filters,
  onChange,
  targets = [],
}: {
  filters: FindingFilterState
  onChange: (next: FindingFilterState) => void
  targets?: Target[]
}) {
  return (
    <div className="card flex flex-wrap items-center gap-3 p-3">
      <div className="flex min-w-[180px] flex-1 items-center gap-2 rounded-md border border-border bg-bg-elevated px-2.5 py-1.5">
        <Search size={14} className="text-text-muted" />
        <input
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          placeholder="Search findings…"
          className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />
      </div>

      <select
        value={filters.severity}
        onChange={(e) => onChange({ ...filters, severity: e.target.value as any })}
        className="rounded-md border border-border bg-bg-elevated px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
      >
        {SEVERITIES.map((s) => (
          <option key={s} value={s}>
            {s === 'all' ? 'All severities' : s}
          </option>
        ))}
      </select>

      <select
        value={filters.status}
        onChange={(e) => onChange({ ...filters, status: e.target.value as any })}
        className="rounded-md border border-border bg-bg-elevated px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
      >
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {s === 'all' ? 'All statuses' : s.replace('_', ' ')}
          </option>
        ))}
      </select>

      {targets.length > 0 && (
        <select
          value={filters.targetId}
          onChange={(e) => onChange({ ...filters, targetId: e.target.value })}
          className="rounded-md border border-border bg-bg-elevated px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
        >
          <option value="all">All targets</option>
          {targets.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}

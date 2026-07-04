import { ChevronRight, Wrench } from 'lucide-react'
import SeverityBadge from '@/components/ui/SeverityBadge'
import CVSSBadge from '@/components/ui/CVSSBadge'
import { formatRelativeTime } from '@/lib/utils'
import type { Finding } from '@/types'

const STATUS_LABEL: Record<string, string> = {
  open: 'Open',
  confirmed: 'Confirmed',
  false_positive: 'False Positive',
  remediated: 'Remediated',
  accepted_risk: 'Accepted Risk',
}

export default function FindingCard({
  finding,
  onSelect,
}: {
  finding: Finding
  onSelect?: (finding: Finding) => void
}) {
  return (
    <button
      onClick={() => onSelect?.(finding)}
      className="card flex w-full items-start justify-between gap-4 p-4 text-left transition-colors hover:border-accent/40"
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          {finding.cvss_score !== undefined && (
            <CVSSBadge score={finding.cvss_score} vector={finding.cvss_vector} />
          )}
          {finding.status && (
            <span className="text-[10px] uppercase tracking-wide text-text-muted">
              {STATUS_LABEL[finding.status] ?? finding.status}
            </span>
          )}
        </div>
        <h3 className="mt-1.5 truncate text-sm font-semibold text-text-primary">
          {finding.title}
        </h3>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-text-secondary">
          <span>{finding.target_name}</span>
          <span className="flex items-center gap-1 font-mono text-text-muted">
            <Wrench size={11} /> {finding.tool}
          </span>
          <span className="text-text-muted">{formatRelativeTime(finding.created_at)}</span>
        </div>
        {finding.mitre_techniques?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {finding.mitre_techniques.slice(0, 4).map((t) => (
              <span
                key={t}
                className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-text-secondary"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
      <ChevronRight size={16} className="mt-1 shrink-0 text-text-muted" />
    </button>
  )
}

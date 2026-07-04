import { Download, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { formatRelativeTime, cn } from '@/lib/utils'
import { API_URL } from '@/lib/constants'
import type { Report } from '@/types'

const STATUS_META: Record<
  Report['status'],
  { icon: typeof Clock; cls: string; label: string }
> = {
  pending: { icon: Clock, cls: 'text-text-muted', label: 'Pending' },
  generating: { icon: Loader2, cls: 'text-accent', label: 'Generating' },
  ready: { icon: CheckCircle2, cls: 'text-accent-green', label: 'Ready' },
  failed: { icon: XCircle, cls: 'text-accent-red', label: 'Failed' },
}

export default function ReportPreview({ report }: { report: Report }) {
  const meta = STATUS_META[report.status]
  const Icon = meta.icon
  const findingCount = (report.summary?.finding_count as number) ?? undefined
  const criticalCount = (report.summary?.critical_count as number) ?? undefined

  return (
    <div className="card flex items-center justify-between p-4">
      <div className="min-w-0">
        <h3 className="truncate text-sm font-semibold text-text-primary">{report.title}</h3>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-text-secondary">
          <span className={cn('flex items-center gap-1', meta.cls)}>
            <Icon size={12} className={report.status === 'generating' ? 'animate-spin' : ''} />
            {meta.label}
          </span>
          <span className="font-mono uppercase text-text-muted">{report.format}</span>
          {findingCount !== undefined && <span>{findingCount} findings</span>}
          {criticalCount !== undefined && criticalCount > 0 && (
            <span className="text-accent-red">{criticalCount} critical</span>
          )}
          <span className="text-text-muted">{formatRelativeTime(report.created_at)}</span>
        </div>
      </div>

      {report.status === 'ready' && report.file_path && (
        <a
          href={`${API_URL}/reports/${report.id}/download`}
          className="flex shrink-0 items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-accent hover:border-accent"
        >
          <Download size={13} /> Download
        </a>
      )}
    </div>
  )
}

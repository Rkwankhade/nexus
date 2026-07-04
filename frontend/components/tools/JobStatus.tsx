'use client'

import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'
import { getJson } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ToolJob } from '@/types'

const STATUS_META = {
  queued: { icon: Clock, cls: 'text-text-muted', label: 'Queued' },
  running: { icon: Loader2, cls: 'text-accent', label: 'Running' },
  completed: { icon: CheckCircle2, cls: 'text-accent-green', label: 'Completed' },
  failed: { icon: XCircle, cls: 'text-accent-red', label: 'Failed' },
} as const

export default function JobStatus({
  jobId,
  statusEndpoint,
}: {
  jobId: string
  statusEndpoint: string
}) {
  const { data: job } = useQuery<ToolJob>({
    queryKey: ['job', jobId],
    queryFn: () => getJson<ToolJob>(`${statusEndpoint}/${jobId}`),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 3000
    },
  })

  if (!job) {
    return <div className="card p-4 text-xs text-text-muted">Loading job…</div>
  }

  const meta = STATUS_META[job.status]
  const Icon = meta.icon

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm text-text-primary">
          {job.tool_name ?? job.tool}
        </span>
        <span className={cn('flex items-center gap-1.5 text-xs', meta.cls)}>
          <Icon size={13} className={job.status === 'running' ? 'animate-spin' : ''} />
          {meta.label}
        </span>
      </div>

      {job.status === 'running' && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-bg-elevated">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      {job.status === 'failed' && job.error_message && (
        <p className="mt-3 rounded-md bg-accent-red/10 p-2 text-xs text-accent-red">
          {job.error_message}
        </p>
      )}

      {job.status === 'completed' && job.result_summary && (
        <pre className="mt-3 max-h-64 overflow-auto rounded-md bg-bg-primary p-3 font-mono text-[11px] text-text-secondary">
          {JSON.stringify(job.result_summary, null, 2)}
        </pre>
      )}
    </div>
  )
}

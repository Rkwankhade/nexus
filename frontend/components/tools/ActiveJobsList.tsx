import { X } from 'lucide-react'
import type { ToolJob } from '@/types'

interface Props {
  jobs: ToolJob[]
  onCancel?: (jobId: string) => void
}

export default function ActiveJobsList({ jobs, onCancel }: Props) {
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-text-primary">Active Tool Jobs</h3>
      <div className="space-y-3">
        {jobs.map((job) => (
          <div key={job.id}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-mono text-text-secondary">{job.tool}</span>
              <div className="flex items-center gap-2">
                <span className="text-text-muted">{job.progress}%</span>
                <button
                  onClick={() => onCancel?.(job.id)}
                  className="text-text-muted hover:text-accent-red"
                  aria-label="Cancel job"
                >
                  <X size={12} />
                </button>
              </div>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-elevated">
              <div
                className="h-full rounded-full bg-accent transition-all"
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>
        ))}
        {jobs.length === 0 && (
          <p className="py-4 text-center text-xs text-text-muted">No active jobs.</p>
        )}
      </div>
    </div>
  )
}

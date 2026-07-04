import { formatRelativeTime, severityColor, cn } from '@/lib/utils'
import type { Alert } from '@/types'

export default function LiveAlertFeed({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="card flex h-full flex-col">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold text-text-primary">Live Alert Feed</h3>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {alerts.map((a) => (
          <div
            key={a.id}
            className={cn(
              'rounded-md border-l-2 bg-bg-elevated/40 px-3 py-2 text-xs',
              severityColor(a.severity)
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary">{a.title}</span>
              <span className="text-text-muted">{formatRelativeTime(a.created_at)}</span>
            </div>
            <p className="mt-0.5 text-text-secondary">{a.message}</p>
          </div>
        ))}
        {alerts.length === 0 && (
          <p className="py-6 text-center text-xs text-text-muted">No active alerts.</p>
        )}
      </div>
    </div>
  )
}

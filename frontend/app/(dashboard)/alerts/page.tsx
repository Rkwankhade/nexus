'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'
import { getJson, postJson } from '@/lib/api'
import { formatRelativeTime, severityColor, cn } from '@/lib/utils'
import type { Alert } from '@/types'

export default function AlertsPage() {
  const queryClient = useQueryClient()

  const { data: alerts, isLoading } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: () => getJson<Alert[]>('/alerts'),
    refetchInterval: 15_000,
  })

  const acknowledge = useMutation({
    mutationFn: (id: string) => postJson(`/alerts/${id}/acknowledge`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Alerts</h1>
        <p className="text-sm text-text-secondary">SIEM & platform alerts</p>
      </div>

      {isLoading ? (
        <div className="card p-8 text-center text-sm text-text-muted">Loading alerts…</div>
      ) : (
        <div className="space-y-2">
          {alerts?.map((a) => (
            <div
              key={a.id}
              className={cn(
                'card flex items-center justify-between border-l-2 p-3',
                severityColor(a.severity)
              )}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-text-primary">{a.title}</span>
                  <span className="text-[10px] text-text-muted">{a.source}</span>
                </div>
                <p className="mt-0.5 text-xs text-text-secondary">{a.message}</p>
                <p className="mt-1 text-[10px] text-text-muted">
                  {formatRelativeTime(a.created_at)}
                </p>
              </div>
              {!a.acknowledged && (
                <button
                  onClick={() => acknowledge.mutate(a.id)}
                  className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-xs text-text-secondary hover:border-accent-green hover:text-accent-green"
                >
                  <CheckCircle2 size={13} /> Acknowledge
                </button>
              )}
            </div>
          ))}
          {alerts?.length === 0 && (
            <div className="card p-8 text-center text-sm text-text-muted">
              No alerts. All clear.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

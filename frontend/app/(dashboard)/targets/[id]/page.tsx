'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ShieldCheck, ShieldAlert } from 'lucide-react'
import { getJson } from '@/lib/api'
import api from '@/lib/api'
import { cn, formatRelativeTime } from '@/lib/utils'
import FindingCard from '@/components/findings/FindingCard'
import FindingDetail from '@/components/findings/FindingDetail'
import type { Finding, Target, ToolJob } from '@/types'

export default function TargetDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [authRef, setAuthRef] = useState('')
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)

  const { data: target, isLoading } = useQuery<Target>({
    queryKey: ['target', params.id],
    queryFn: () => getJson<Target>(`/targets/${params.id}`),
  })

  const { data: scans } = useQuery<ToolJob[]>({
    queryKey: ['scans', params.id],
    queryFn: () => getJson<ToolJob[]>('/scans', { target_id: params.id }),
  })

  const { data: findings } = useQuery<Finding[]>({
    queryKey: ['findings', params.id],
    queryFn: () => getJson<Finding[]>('/findings', { target_id: params.id }),
  })

  const authorize = useMutation({
    mutationFn: () =>
      api.patch(`/targets/${params.id}`, {
        status: 'authorized',
        authorization_reference: authRef,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['target', params.id] }),
  })

  if (isLoading || !target) {
    return <div className="card p-8 text-center text-sm text-text-muted">Loading target…</div>
  }

  const isAuthorized = target.status === 'authorized' || target.status === 'active'

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.push('/targets')}
        className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft size={13} /> Back to Targets
      </button>

      <div className="card p-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-text-primary">{target.name}</h1>
            <p className="mt-0.5 font-mono text-sm text-text-secondary">{target.host}</p>
          </div>
          <span
            className={cn(
              'flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
              isAuthorized
                ? 'bg-accent-green/10 text-accent-green'
                : 'bg-accent-orange/10 text-accent-orange'
            )}
          >
            {isAuthorized ? <ShieldCheck size={13} /> : <ShieldAlert size={13} />}
            {target.status?.replace('_', ' ') ?? 'pending auth'}
          </span>
        </div>

        {target.scope_notes && (
          <p className="mt-3 text-sm text-text-secondary">{target.scope_notes}</p>
        )}

        {target.authorization_reference && (
          <p className="mt-2 font-mono text-xs text-text-muted">
            Authorization ref: {target.authorization_reference}
          </p>
        )}

        {!isAuthorized && (
          <div className="mt-4 flex items-center gap-2 rounded-md border border-accent-orange/30 bg-accent-orange/5 p-3">
            <input
              value={authRef}
              onChange={(e) => setAuthRef(e.target.value)}
              placeholder="Authorization reference (e.g. SOW-2026-014)"
              className="flex-1 rounded-md border border-border bg-bg-elevated px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
            <button
              onClick={() => authorize.mutate()}
              disabled={!authRef || authorize.isPending}
              className="rounded-md bg-accent-green/20 px-3 py-1.5 text-xs font-semibold text-accent-green hover:bg-accent-green/30 disabled:opacity-50"
            >
              Authorize
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Scan History</h3>
          <div className="space-y-1.5">
            {scans?.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-bg-elevated"
              >
                <span className="font-mono text-text-secondary">{s.tool}</span>
                <span className="text-text-muted">{s.status}</span>
                {s.started_at && (
                  <span className="text-text-muted">{formatRelativeTime(s.started_at)}</span>
                )}
              </div>
            ))}
            {(!scans || scans.length === 0) && (
              <p className="py-4 text-center text-xs text-text-muted">No scans run yet.</p>
            )}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">
            Findings ({findings?.length ?? 0})
          </h3>
          <div className="space-y-2">
            {findings?.map((f) => (
              <FindingCard key={f.id} finding={f} onSelect={setSelectedFinding} />
            ))}
            {(!findings || findings.length === 0) && (
              <p className="py-4 text-center text-xs text-text-muted">No findings yet.</p>
            )}
          </div>
        </div>
      </div>

      {selectedFinding && (
        <FindingDetail finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
      )}
    </div>
  )
}

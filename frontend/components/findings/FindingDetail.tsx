'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Sparkles } from 'lucide-react'
import { postJson } from '@/lib/api'
import api from '@/lib/api'
import SeverityBadge from '@/components/ui/SeverityBadge'
import CVSSBadge from '@/components/ui/CVSSBadge'
import { formatRelativeTime } from '@/lib/utils'
import type { Finding, FindingStatus } from '@/types'

const STATUS_OPTIONS: FindingStatus[] = [
  'open',
  'confirmed',
  'false_positive',
  'remediated',
  'accepted_risk',
]

export default function FindingDetail({
  finding,
  onClose,
}: {
  finding: Finding
  onClose: () => void
}) {
  const queryClient = useQueryClient()

  const updateStatus = useMutation({
    mutationFn: (status: FindingStatus) =>
      api.patch(`/findings/${finding.id}`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['findings'] }),
  })

  const requestAiAnalysis = useMutation({
    mutationFn: () => postJson(`/ai/analyze-finding`, { finding_id: finding.id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['findings'] }),
  })

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-lg overflow-y-auto border-l border-border bg-bg-secondary p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <SeverityBadge severity={finding.severity} />
              {finding.cvss_score !== undefined && (
                <CVSSBadge score={finding.cvss_score} vector={finding.cvss_vector} />
              )}
            </div>
            <h2 className="mt-2 text-lg font-bold text-text-primary">{finding.title}</h2>
            <p className="mt-0.5 text-xs text-text-muted">
              {finding.target_name} · {formatRelativeTime(finding.created_at)} · via{' '}
              <span className="font-mono">{finding.tool}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <span className="text-xs text-text-secondary">Status</span>
          <select
            value={finding.status ?? 'open'}
            onChange={(e) => updateStatus.mutate(e.target.value as FindingStatus)}
            className="rounded-md border border-border bg-bg-elevated px-2 py-1 text-xs text-text-primary focus:border-accent focus:outline-none"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        {finding.description && (
          <section className="mt-4">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">
              Description
            </h3>
            <p className="text-sm text-text-secondary">{finding.description}</p>
          </section>
        )}

        {finding.affected_host && (
          <section className="mt-4 grid grid-cols-3 gap-2 text-xs">
            <div>
              <p className="text-text-muted">Host</p>
              <p className="font-mono text-text-primary">{finding.affected_host}</p>
            </div>
            <div>
              <p className="text-text-muted">Port</p>
              <p className="font-mono text-text-primary">{finding.affected_port ?? '—'}</p>
            </div>
            <div>
              <p className="text-text-muted">Service</p>
              <p className="font-mono text-text-primary">{finding.affected_service || '—'}</p>
            </div>
          </section>
        )}

        {finding.cve_ids && finding.cve_ids.length > 0 && (
          <section className="mt-4">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">
              CVEs
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {finding.cve_ids.map((cve) => (
                <span
                  key={cve}
                  className="rounded border border-border px-2 py-0.5 font-mono text-[11px] text-accent"
                >
                  {cve}
                </span>
              ))}
            </div>
          </section>
        )}

        {finding.mitre_techniques?.length > 0 && (
          <section className="mt-4">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">
              MITRE ATT&CK
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {finding.mitre_techniques.map((t) => (
                <span
                  key={t}
                  className="rounded border border-border px-2 py-0.5 font-mono text-[11px] text-text-secondary"
                >
                  {t}
                </span>
              ))}
            </div>
          </section>
        )}

        {finding.remediation && (
          <section className="mt-4">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">
              Remediation
            </h3>
            <p className="text-sm text-text-secondary">{finding.remediation}</p>
          </section>
        )}

        <section className="mt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              AI Analysis
            </h3>
            <button
              onClick={() => requestAiAnalysis.mutate()}
              disabled={requestAiAnalysis.isPending}
              className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-[11px] text-accent hover:border-accent disabled:opacity-50"
            >
              <Sparkles size={11} />
              {requestAiAnalysis.isPending ? 'Analyzing…' : 'Re-analyze'}
            </button>
          </div>
          <p className="mt-1 text-sm text-text-secondary">
            {finding.ai_summary || 'No AI analysis yet — request one above.'}
          </p>
        </section>
      </div>
    </div>
  )
}

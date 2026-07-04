'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, Loader2 } from 'lucide-react'
import { getJson, postJson } from '@/lib/api'
import { REPORT_FORMATS } from '@/lib/constants'
import SeverityBadge from '@/components/ui/SeverityBadge'
import type { Finding, Report, ReportFormat, Target } from '@/types'

export default function ReportBuilder({ onCreated }: { onCreated?: (report: Report) => void }) {
  const queryClient = useQueryClient()
  const [targetId, setTargetId] = useState('')
  const [title, setTitle] = useState('')
  const [format, setFormat] = useState<ReportFormat>('pdf')
  const [selectedFindings, setSelectedFindings] = useState<Set<string>>(new Set())

  const { data: targets } = useQuery<Target[]>({
    queryKey: ['targets'],
    queryFn: () => getJson<Target[]>('/targets'),
  })

  const { data: findings } = useQuery<Finding[]>({
    queryKey: ['findings', 'by-target', targetId],
    queryFn: () => getJson<Finding[]>('/findings', { target_id: targetId }),
    enabled: !!targetId,
  })

  const createReport = useMutation({
    mutationFn: () =>
      postJson<Report>('/reports', {
        target_id: targetId,
        title: title || `Assessment Report — ${new Date().toLocaleDateString()}`,
        format,
        finding_ids: Array.from(selectedFindings),
      }),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      onCreated?.(report)
      setSelectedFindings(new Set())
      setTitle('')
    },
  })

  function toggleFinding(id: string) {
    setSelectedFindings((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="card space-y-4 p-4">
      <div className="flex items-center gap-2">
        <FileText size={16} className="text-accent" />
        <h3 className="text-sm font-semibold text-text-primary">Build a Report</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Target</label>
          <select
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-elevated px-2.5 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          >
            <option value="">Select a target…</option>
            {targets?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as ReportFormat)}
            className="w-full rounded-md border border-border bg-bg-elevated px-2.5 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          >
            {REPORT_FORMATS.map((f) => (
              <option key={f} value={f}>
                {f.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs text-text-secondary">Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Assessment Report — Q3 Pentest"
          className="w-full rounded-md border border-border bg-bg-elevated px-2.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
        />
      </div>

      {targetId && (
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Include findings ({selectedFindings.size} selected)
          </label>
          <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border border-border p-2">
            {findings?.map((f) => (
              <label
                key={f.id}
                className="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 hover:bg-bg-elevated"
              >
                <input
                  type="checkbox"
                  checked={selectedFindings.has(f.id)}
                  onChange={() => toggleFinding(f.id)}
                  className="accent-accent"
                />
                <SeverityBadge severity={f.severity} />
                <span className="truncate text-xs text-text-primary">{f.title}</span>
              </label>
            ))}
            {findings?.length === 0 && (
              <p className="px-1.5 py-2 text-xs text-text-muted">
                No findings for this target yet.
              </p>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => createReport.mutate()}
        disabled={!targetId || createReport.isPending}
        className="flex w-full items-center justify-center gap-2 rounded-md bg-accent py-2 text-sm font-semibold text-bg-primary hover:bg-accent/90 disabled:opacity-50"
      >
        {createReport.isPending ? (
          <>
            <Loader2 size={14} className="animate-spin" /> Generating…
          </>
        ) : (
          'Generate Report'
        )}
      </button>
    </div>
  )
}

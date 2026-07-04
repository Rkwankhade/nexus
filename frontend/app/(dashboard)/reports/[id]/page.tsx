'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { getJson } from '@/lib/api'
import ReportPreview from '@/components/reports/ReportPreview'
import type { Report } from '@/types'

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()

  const { data: report, isLoading } = useQuery<Report>({
    queryKey: ['report', params.id],
    queryFn: () => getJson<Report>(`/reports/${params.id}`),
    refetchInterval: (query) =>
      query.state.data?.status === 'generating' ? 4000 : false,
  })

  if (isLoading || !report) {
    return <div className="card p-8 text-center text-sm text-text-muted">Loading report…</div>
  }

  const summaryEntries = Object.entries(report.summary ?? {})

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.push('/reports')}
        className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft size={13} /> Back to Reports
      </button>

      <ReportPreview report={report} />

      {summaryEntries.length > 0 && (
        <div className="card p-4">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Summary</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {summaryEntries.map(([key, value]) => (
              <div key={key} className="rounded-md bg-bg-elevated p-3">
                <p className="text-[11px] uppercase tracking-wide text-text-muted">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="mt-1 font-mono text-lg text-text-primary">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {report.status === 'failed' && (
        <div className="card border-accent-red/30 bg-accent-red/5 p-4 text-sm text-accent-red">
          Report generation failed. Try regenerating it from the Reports page.
        </div>
      )}
    </div>
  )
}

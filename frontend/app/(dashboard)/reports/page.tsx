'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileDown, FilePlus } from 'lucide-react'
import { getJson, postJson } from '@/lib/api'

interface ReportSummary {
  id: string
  title: string
  target_name: string
  format: 'pdf' | 'html'
  created_at: string
  download_url: string
}

export default function ReportsPage() {
  const queryClient = useQueryClient()

  const { data: reports, isLoading } = useQuery<ReportSummary[]>({
    queryKey: ['reports'],
    queryFn: () => getJson<ReportSummary[]>('/reports'),
  })

  const generate = useMutation({
    mutationFn: () => postJson('/reports/generate', {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Reports</h1>
          <p className="text-sm text-text-secondary">Generated engagement reports</p>
        </div>
        <button
          onClick={() => generate.mutate()}
          disabled={generate.isPending}
          className="flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-bg-primary hover:bg-accent/90 disabled:opacity-50"
        >
          <FilePlus size={14} /> {generate.isPending ? 'Generating…' : 'Generate Report'}
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[11px] uppercase text-text-muted">
              <th className="px-4 py-2 font-medium">Title</th>
              <th className="px-4 py-2 font-medium">Target</th>
              <th className="px-4 py-2 font-medium">Format</th>
              <th className="px-4 py-2 font-medium">Created</th>
              <th className="px-4 py-2 font-medium" />
            </tr>
          </thead>
          <tbody>
            {reports?.map((r) => (
              <tr key={r.id} className="border-t border-border hover:bg-bg-elevated/50">
                <td className="px-4 py-2.5 text-text-primary">{r.title}</td>
                <td className="px-4 py-2.5 text-text-secondary">{r.target_name}</td>
                <td className="px-4 py-2.5 uppercase text-text-muted">{r.format}</td>
                <td className="px-4 py-2.5 text-xs text-text-muted">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <a
                    href={r.download_url}
                    className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
                  >
                    <FileDown size={13} /> Download
                  </a>
                </td>
              </tr>
            ))}
            {!isLoading && reports?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-xs text-text-muted">
                  No reports generated yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import SeverityBadge from '@/components/ui/SeverityBadge'
import { formatRelativeTime } from '@/lib/utils'
import type { Finding } from '@/types'

export default function RecentFindingsTable({ findings }: { findings: Finding[] }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold text-text-primary">Recent Findings</h3>
      </div>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-[11px] uppercase text-text-muted">
            <th className="px-4 py-2 font-medium">Severity</th>
            <th className="px-4 py-2 font-medium">Target</th>
            <th className="px-4 py-2 font-medium">Tool</th>
            <th className="px-4 py-2 font-medium">Time</th>
            <th className="px-4 py-2 font-medium">AI Analysis</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <tr key={f.id} className="border-t border-border hover:bg-bg-elevated/50">
              <td className="px-4 py-2.5">
                <SeverityBadge severity={f.severity} />
              </td>
              <td className="px-4 py-2.5 text-text-primary">{f.target_name}</td>
              <td className="px-4 py-2.5 font-mono text-xs text-text-secondary">{f.tool}</td>
              <td className="px-4 py-2.5 text-xs text-text-muted">
                {formatRelativeTime(f.created_at)}
              </td>
              <td className="max-w-xs truncate px-4 py-2.5 text-xs text-text-secondary">
                {f.ai_summary || '—'}
              </td>
            </tr>
          ))}
          {findings.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-6 text-center text-xs text-text-muted">
                No findings yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

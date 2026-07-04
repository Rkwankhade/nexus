import { cn } from '@/lib/utils'

function bandFor(score: number) {
  if (score >= 9.0) return { label: 'Critical', cls: 'badge-critical' }
  if (score >= 7.0) return { label: 'High', cls: 'badge-high' }
  if (score >= 4.0) return { label: 'Medium', cls: 'badge-medium' }
  if (score > 0) return { label: 'Low', cls: 'badge-low' }
  return { label: 'None', cls: 'badge-info' }
}

export default function CVSSBadge({ score, vector }: { score?: number; vector?: string }) {
  if (score === undefined || score === null) {
    return <span className="text-xs text-text-muted">—</span>
  }
  const band = bandFor(score)
  return (
    <span
      title={vector}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold',
        band.cls
      )}
    >
      {score.toFixed(1)} <span className="opacity-70">{band.label}</span>
    </span>
  )
}

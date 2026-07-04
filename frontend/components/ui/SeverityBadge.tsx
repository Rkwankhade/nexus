import { severityColor, cn } from '@/lib/utils'
import type { Severity } from '@/types'

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
        severityColor(severity)
      )}
    >
      {severity}
    </span>
  )
}

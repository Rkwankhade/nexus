import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  accent?: 'cyan' | 'red' | 'green' | 'orange'
  sub?: React.ReactNode
  loading?: boolean
}

const accentMap = {
  cyan: 'text-accent',
  red: 'text-accent-red',
  green: 'text-accent-green',
  orange: 'text-accent-orange',
}

export default function StatCard({
  label,
  value,
  icon: Icon,
  accent = 'cyan',
  sub,
  loading,
}: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium tracking-wide text-text-secondary">{label}</p>
        <Icon size={16} className={cn(accentMap[accent])} />
      </div>
      <p className="mt-2 font-mono text-2xl font-bold text-text-primary">
        {loading ? '—' : value}
      </p>
      {sub && <div className="mt-1">{sub}</div>}
    </div>
  )
}

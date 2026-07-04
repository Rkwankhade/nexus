'use client'

import { useQuery } from '@tanstack/react-query'
import { ListChecks, ShieldCheck } from 'lucide-react'
import { getJson } from '@/lib/api'
import { cn } from '@/lib/utils'
import SeverityBadge from '@/components/ui/SeverityBadge'
import type { DetectionRule } from '@/types'

const ENGINE_LABEL: Record<DetectionRule['engine'], string> = {
  sigma: 'Sigma',
  suricata: 'Suricata',
  yara: 'YARA',
  custom: 'Custom',
}

export default function DetectionRulesPage() {
  const { data: rules, isLoading } = useQuery<DetectionRule[]>({
    queryKey: ['detection-rules'],
    queryFn: () => getJson<DetectionRule[]>('/blueteam/rules'),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary">
          <ListChecks size={18} className="text-accent" /> Detection Rules
        </h1>
        <p className="text-sm text-text-secondary">
          Sigma, Suricata, and YARA rules active on this deployment
        </p>
      </div>

      {isLoading ? (
        <div className="card p-8 text-center text-sm text-text-muted">Loading rules…</div>
      ) : (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {rules?.map((r) => (
            <div key={r.id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-text-primary">{r.name}</p>
                  {r.description && (
                    <p className="mt-0.5 text-xs text-text-secondary">{r.description}</p>
                  )}
                </div>
                <span
                  className={cn(
                    'flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold',
                    r.enabled
                      ? 'bg-accent-green/10 text-accent-green'
                      : 'bg-text-muted/10 text-text-muted'
                  )}
                >
                  <ShieldCheck size={10} /> {r.enabled ? 'Active' : 'Disabled'}
                </span>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-text-secondary">
                    {ENGINE_LABEL[r.engine]}
                  </span>
                  <SeverityBadge severity={r.severity} />
                </div>
                {r.match_count !== undefined && (
                  <span className="font-mono text-xs text-text-muted">
                    {r.match_count} matches
                  </span>
                )}
              </div>
            </div>
          ))}
          {rules?.length === 0 && (
            <div className="card p-8 text-center text-sm text-text-muted sm:col-span-2">
              No detection rules configured yet.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

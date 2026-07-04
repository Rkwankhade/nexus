'use client'

import { useQuery } from '@tanstack/react-query'
import { Crosshair, ListChecks, Loader2, Bell } from 'lucide-react'
import StatCard from '@/components/ui/StatCard'
import RecentFindingsTable from '@/components/tools/RecentFindingsTable'
import LiveAlertFeed from '@/components/tools/LiveAlertFeed'
import ActiveJobsList from '@/components/tools/ActiveJobsList'
import RiskGauge from '@/components/charts/RiskGauge'
import SeverityPie from '@/components/charts/SeverityPie'
import ActivityTimeline from '@/components/charts/ActivityTimeline'
import MitreHeatmap from '@/components/charts/MitreHeatmap'
import { getJson } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'
import type { Finding, ToolJob } from '@/types'

interface DashboardSummary {
  total_targets: number
  open_findings: number
  active_jobs: number
  open_alerts: number
  critical_alerts: number
  risk_score: number
  severity_breakdown: { severity: string; count: number }[]
  activity_30d: { date: string; findings: number }[]
  mitre_coverage: { tactic: string; technique: string; coverage: number }[]
  recent_findings: Finding[]
}

export default function DashboardPage() {
  const activeJobs = useAppStore((s) => s.activeJobs)
  const openAlerts = useAppStore((s) => s.openAlerts)

  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: () => getJson<DashboardSummary>('/dashboard/summary'),
    refetchInterval: 20_000,
  })

  const jobs: ToolJob[] = activeJobs.length > 0 ? activeJobs : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Operations Overview</h1>
        <p className="text-sm text-text-secondary">Live status across all engagements</p>
      </div>

      {/* Row 1 — stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Targets"
          value={data?.total_targets ?? 0}
          icon={Crosshair}
          loading={isLoading}
        />
        <StatCard
          label="Open Findings"
          value={data?.open_findings ?? 0}
          icon={ListChecks}
          accent="orange"
          loading={isLoading}
        />
        <StatCard
          label="Active Jobs"
          value={jobs.length}
          icon={Loader2}
          accent="cyan"
        />
        <StatCard
          label="Open Alerts"
          value={openAlerts.length || data?.open_alerts || 0}
          icon={Bell}
          accent="red"
          sub={
            (data?.critical_alerts ?? 0) > 0 && (
              <span className="badge-critical rounded-full px-2 py-0.5 text-[10px] font-semibold">
                {data?.critical_alerts} critical
              </span>
            )
          }
          loading={isLoading}
        />
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <RecentFindingsTable findings={data?.recent_findings ?? []} />
        </div>
        <div className="card space-y-4 p-4 lg:col-span-2">
          <RiskGauge score={data?.risk_score ?? 0} />
          <SeverityPie data={data?.severity_breakdown ?? []} />
        </div>
      </div>

      {/* Row 3 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-2 text-sm font-semibold text-text-primary">
            Activity Timeline (30d)
          </h3>
          <ActivityTimeline data={data?.activity_30d ?? []} />
        </div>
        <LiveAlertFeed alerts={openAlerts} />
      </div>

      {/* Row 4 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <ActiveJobsList jobs={jobs} />
        </div>
        <div className="card p-4 lg:col-span-3">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">
            MITRE ATT&CK Coverage
          </h3>
          <MitreHeatmap cells={data?.mitre_coverage ?? []} />
        </div>
      </div>
    </div>
  )
}

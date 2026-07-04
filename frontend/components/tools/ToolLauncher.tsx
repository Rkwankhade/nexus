'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getJson, postJson } from '@/lib/api'
import ToolCard, { ToolMeta } from './ToolCard'
import ActiveJobsList from './ActiveJobsList'
import type { Target, ToolJob } from '@/types'

/**
 * Generic launcher for read-only / analytical tool categories
 * (recon, scanning, web, blueteam, forensics). Each page supplies
 * its own tool list and the API endpoint that dispatches jobs.
 */
export default function ToolLauncher({
  tools,
  dispatchEndpoint,
  category,
}: {
  tools: ToolMeta[]
  dispatchEndpoint: string
  category: string
}) {
  const queryClient = useQueryClient()
  const [targetId, setTargetId] = useState('')

  const { data: targets } = useQuery<Target[]>({
    queryKey: ['targets'],
    queryFn: () => getJson<Target[]>('/targets'),
  })

  const { data: jobs } = useQuery<ToolJob[]>({
    queryKey: ['jobs', category],
    queryFn: () => getJson<ToolJob[]>('/scans/jobs', { category }),
    refetchInterval: 5000,
  })

  const launch = useMutation({
    mutationFn: (toolId: string) =>
      postJson(dispatchEndpoint, { target_id: targetId, tool: toolId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs', category] }),
  })

  return (
    <div className="space-y-4">
      <div className="card p-3.5">
        <label className="mb-1 block text-xs text-text-secondary">Target</label>
        <select
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          className="w-full max-w-sm rounded-md border border-border bg-bg-elevated px-2.5 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
        >
          <option value="">Select a target…</option>
          {targets?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} — {t.host}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {tools.map((tool) => (
          <ToolCard
            key={tool.id}
            tool={tool}
            disabled={!targetId || launch.isPending}
            onLaunch={(toolId) => launch.mutate(toolId)}
          />
        ))}
      </div>

      <ActiveJobsList jobs={jobs ?? []} />
    </div>
  )
}

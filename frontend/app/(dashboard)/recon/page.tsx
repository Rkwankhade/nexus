'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import OutputTerminal from '@/components/tools/OutputTerminal'
import { getJson, postJson } from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'
import type { Target, ToolJob } from '@/types'

const TABS = ['Nmap', 'Amass', 'theHarvester', 'Shodan', 'WHOIS'] as const
type Tab = (typeof TABS)[number]

const TOOL_ENDPOINT: Record<Tab, string> = {
  Nmap: '/recon/nmap',
  Amass: '/recon/amass',
  theHarvester: '/recon/theharvester',
  Shodan: '/recon/shodan',
  WHOIS: '/recon/whois',
}

export default function ReconPage() {
  const [tab, setTab] = useState<Tab>('Nmap')
  const [targetId, setTargetId] = useState('')
  const [params, setParams] = useState('')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [resultTab, setResultTab] = useState<'terminal' | 'parsed' | 'ai'>('terminal')

  const { data: targets } = useQuery<Target[]>({
    queryKey: ['targets'],
    queryFn: () => getJson<Target[]>('/targets'),
  })

  const { data: jobHistory } = useQuery<ToolJob[]>({
    queryKey: ['jobs', tab],
    queryFn: () => getJson<ToolJob[]>('/scans', { tool: tab.toLowerCase() }),
  })

  const runTool = useMutation({
    mutationFn: () =>
      postJson<{ job_id: string }>(TOOL_ENDPOINT[tab], { target_id: targetId, params }),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Reconnaissance</h1>
        <p className="text-sm text-text-secondary">OSINT & discovery tooling</p>
      </div>

      <div className="flex gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`border-b-2 px-4 py-2 text-sm ${
              tab === t
                ? 'border-accent text-accent'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        {/* Left: form */}
        <div className="card space-y-3 p-4 lg:col-span-2">
          <div>
            <label className="mb-1 block text-xs text-text-secondary">Target</label>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
            >
              <option value="">Select a target…</option>
              {targets?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.host})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-secondary">
              {tab} parameters
            </label>
            <textarea
              value={params}
              onChange={(e) => setParams(e.target.value)}
              rows={4}
              placeholder={`Additional ${tab} flags / options…`}
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>
          <button
            onClick={() => runTool.mutate()}
            disabled={!targetId || runTool.isPending}
            className="w-full rounded-md bg-accent py-2 text-sm font-semibold text-bg-primary hover:bg-accent/90 disabled:opacity-50"
          >
            {runTool.isPending ? 'Launching…' : `Run ${tab}`}
          </button>

          <div className="pt-2">
            <h4 className="mb-2 text-xs font-semibold text-text-secondary">Job History</h4>
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {jobHistory?.map((j) => (
                <button
                  key={j.id}
                  onClick={() => setActiveJobId(j.id)}
                  className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs hover:bg-bg-elevated"
                >
                  <span className="font-mono text-text-secondary">{j.id.slice(0, 8)}</span>
                  <span className="text-text-muted">{j.status}</span>
                  {j.started_at && (
                    <span className="text-text-muted">{formatRelativeTime(j.started_at)}</span>
                  )}
                </button>
              ))}
              {(!jobHistory || jobHistory.length === 0) && (
                <p className="py-3 text-center text-xs text-text-muted">No jobs yet.</p>
              )}
            </div>
          </div>
        </div>

        {/* Right: output */}
        <div className="lg:col-span-3">
          <div className="mb-2 flex gap-1">
            {(['terminal', 'parsed', 'ai'] as const).map((rt) => (
              <button
                key={rt}
                onClick={() => setResultTab(rt)}
                className={`rounded-md px-3 py-1.5 text-xs ${
                  resultTab === rt
                    ? 'bg-bg-elevated text-accent'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {rt === 'terminal' ? 'Terminal' : rt === 'parsed' ? 'Parsed Results' : 'AI Analysis'}
              </button>
            ))}
          </div>

          {resultTab === 'terminal' && (
            <OutputTerminal jobId={activeJobId || 'idle'} />
          )}
          {resultTab === 'parsed' && (
            <div className="card p-4 text-sm text-text-secondary">
              {activeJobId
                ? 'Parsed results will appear here once the job completes.'
                : 'Run a job to see parsed results.'}
            </div>
          )}
          {resultTab === 'ai' && (
            <div className="card p-4 text-sm text-text-secondary">
              {activeJobId
                ? 'AI analysis with MITRE badges will appear here once the job completes.'
                : 'Run a job to get an AI analysis.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

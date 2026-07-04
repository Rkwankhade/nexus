'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FileSearch } from 'lucide-react'
import { postJson } from '@/lib/api'
import JobStatus from '@/components/tools/JobStatus'
import type { ToolJob } from '@/types'

const PLUGINS = ['pslist', 'netscan', 'malfind', 'cmdline', 'dlllist', 'filescan', 'hivelist']

export default function MemoryForensicsPage() {
  const [imagePath, setImagePath] = useState('')
  const [profile, setProfile] = useState('auto')
  const [plugins, setPlugins] = useState<string[]>(['pslist', 'netscan', 'malfind'])
  const [jobId, setJobId] = useState<string | null>(null)

  const analyze = useMutation({
    mutationFn: () =>
      postJson<ToolJob>('/forensics/memory/analyze', {
        image_path: imagePath,
        profile,
        plugins,
      }),
    onSuccess: (job) => setJobId(job.id),
  })

  function togglePlugin(p: string) {
    setPlugins((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]))
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary">
          <FileSearch size={18} className="text-accent" /> Memory Forensics
        </h1>
        <p className="text-sm text-text-secondary">
          Analyze a memory image with Volatility
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card space-y-3 p-4">
          <div>
            <label className="mb-1 block text-xs text-text-secondary">
              Memory image path
            </label>
            <input
              value={imagePath}
              onChange={(e) => setImagePath(e.target.value)}
              placeholder="/evidence/host01.mem"
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-secondary">Profile</label>
            <input
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              placeholder="auto"
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-secondary">Plugins</label>
            <div className="flex flex-wrap gap-1.5">
              {PLUGINS.map((p) => (
                <button
                  key={p}
                  onClick={() => togglePlugin(p)}
                  className={`rounded-full border px-2.5 py-1 font-mono text-[11px] ${
                    plugins.includes(p)
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-border text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
          <button
            onClick={() => analyze.mutate()}
            disabled={!imagePath || plugins.length === 0 || analyze.isPending}
            className="w-full rounded-md bg-accent py-2 text-sm font-semibold text-bg-primary hover:bg-accent/90 disabled:opacity-50"
          >
            {analyze.isPending ? 'Dispatching…' : 'Run Analysis'}
          </button>
        </div>

        <div>
          {jobId ? (
            <JobStatus jobId={jobId} statusEndpoint="/forensics/jobs" />
          ) : (
            <div className="card p-8 text-center text-sm text-text-muted">
              Run an analysis to see job status here.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

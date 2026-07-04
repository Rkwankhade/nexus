'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { HardDrive } from 'lucide-react'
import { postJson } from '@/lib/api'
import JobStatus from '@/components/tools/JobStatus'
import type { ToolJob } from '@/types'

const MODULES = ['timeline', 'deleted_files', 'registry', 'browser_artifacts', 'file_carving']

export default function DiskForensicsPage() {
  const [imagePath, setImagePath] = useState('')
  const [filesystem, setFilesystem] = useState('auto')
  const [modules, setModules] = useState<string[]>([
    'timeline',
    'deleted_files',
    'registry',
    'browser_artifacts',
  ])
  const [jobId, setJobId] = useState<string | null>(null)

  const analyze = useMutation({
    mutationFn: () =>
      postJson<ToolJob>('/forensics/disk/analyze', {
        image_path: imagePath,
        filesystem,
        modules,
      }),
    onSuccess: (job) => setJobId(job.id),
  })

  function toggleModule(m: string) {
    setModules((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]))
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary">
          <HardDrive size={18} className="text-accent" /> Disk Forensics
        </h1>
        <p className="text-sm text-text-secondary">
          Analyze a disk image with Autopsy-based modules
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card space-y-3 p-4">
          <div>
            <label className="mb-1 block text-xs text-text-secondary">Disk image path</label>
            <input
              value={imagePath}
              onChange={(e) => setImagePath(e.target.value)}
              placeholder="/evidence/host01.e01"
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-secondary">File system</label>
            <input
              value={filesystem}
              onChange={(e) => setFilesystem(e.target.value)}
              placeholder="auto"
              className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-secondary">Modules</label>
            <div className="flex flex-wrap gap-1.5">
              {MODULES.map((m) => (
                <button
                  key={m}
                  onClick={() => toggleModule(m)}
                  className={`rounded-full border px-2.5 py-1 font-mono text-[11px] ${
                    modules.includes(m)
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-border text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <button
            onClick={() => analyze.mutate()}
            disabled={!imagePath || modules.length === 0 || analyze.isPending}
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

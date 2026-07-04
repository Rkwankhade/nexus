'use client'

import Link from 'next/link'
import { FileSearch, HardDrive, Bug, ArrowRight } from 'lucide-react'

const SECTIONS = [
  {
    href: '/forensics/memory',
    icon: FileSearch,
    title: 'Memory Forensics',
    description: 'Volatility-based analysis of memory image captures',
  },
  {
    href: '/forensics/disk',
    icon: HardDrive,
    title: 'Disk Forensics',
    description: 'File-system timeline and artifact analysis via Autopsy',
  },
  {
    href: '/forensics/malware',
    icon: Bug,
    title: 'Malware Analysis',
    description: 'Static signature matching and file triage with YARA',
  },
]

export default function ForensicsOverviewPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Forensics</h1>
        <p className="text-sm text-text-secondary">Post-incident evidence analysis</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {SECTIONS.map((s) => (
          <Link key={s.href} href={s.href} className="card group p-4 hover:border-accent/40">
            <s.icon size={20} className="text-accent" />
            <h3 className="mt-3 text-sm font-semibold text-text-primary">{s.title}</h3>
            <p className="mt-1 text-xs text-text-secondary">{s.description}</p>
            <span className="mt-3 flex items-center gap-1 text-xs text-accent opacity-0 transition-opacity group-hover:opacity-100">
              Open <ArrowRight size={12} />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}

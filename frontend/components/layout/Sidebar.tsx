'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Crosshair,
  Radar,
  ShieldAlert,
  Globe,
  Swords,
  Footprints,
  KeyRound,
  Wifi,
  Bell,
  Activity,
  FileSearch,
  HardDrive,
  Bug,
  Bot,
  Share2,
  FileText,
  ListChecks,
  Settings,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/useAppStore'

const sections = [
  {
    label: 'OPERATIONS',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/targets', label: 'Targets', icon: Crosshair },
    ],
  },
  {
    label: 'RED TEAM',
    items: [
      { href: '/recon', label: 'Recon', icon: Radar },
      { href: '/scanner', label: 'Scanner', icon: ShieldAlert },
      { href: '/web-attacks', label: 'Web Attacks', icon: Globe },
      { href: '/exploitation', label: 'Exploitation', icon: Swords },
      { href: '/post-exploit', label: 'Post-Exploit', icon: Footprints },
      { href: '/passwords', label: 'Passwords', icon: KeyRound },
      { href: '/wireless', label: 'Wireless', icon: Wifi },
    ],
  },
  {
    label: 'BLUE TEAM',
    items: [
      { href: '/alerts', label: 'Alerts', icon: Bell },
      { href: '/siem', label: 'SIEM', icon: Activity },
      { href: '/detection-rules', label: 'Detection Rules', icon: ListChecks },
    ],
  },
  {
    label: 'FORENSICS',
    items: [
      { href: '/forensics/memory', label: 'Memory', icon: FileSearch },
      { href: '/forensics/disk', label: 'Disk', icon: HardDrive },
      { href: '/forensics/malware', label: 'Malware Analysis', icon: Bug },
    ],
  },
  {
    label: 'AI',
    items: [
      { href: '/ai-assistant', label: 'AI Assistant', icon: Bot },
      { href: '/attack-graph', label: 'Attack Graph', icon: Share2 },
    ],
  },
  {
    label: 'PLATFORM',
    items: [
      { href: '/reports', label: 'Reports', icon: FileText },
      { href: '/findings', label: 'Findings', icon: ListChecks },
      { href: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  const collapsed = useAppStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useAppStore((s) => s.toggleSidebar)
  const activeJobs = useAppStore((s) => s.activeJobs)
  const openAlerts = useAppStore((s) => s.openAlerts)

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r border-border bg-bg-secondary transition-all duration-200',
        collapsed ? 'w-16' : 'w-[280px]'
      )}
    >
      <div className="flex items-center justify-between px-4 py-4">
        {!collapsed && (
          <span className="font-mono text-lg font-bold tracking-widest text-accent">
            NEXUS
          </span>
        )}
        <button
          onClick={toggleSidebar}
          className="rounded-md p-1.5 text-text-secondary hover:bg-bg-elevated hover:text-accent"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
        </button>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-2 pb-4">
        {sections.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="mb-1 px-2 text-[10px] font-semibold tracking-widest text-text-muted">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon
                const active = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-md px-2.5 py-2 text-sm transition-colors',
                      active
                        ? 'bg-bg-elevated text-accent shadow-glow'
                        : 'text-text-secondary hover:bg-bg-elevated hover:text-text-primary'
                    )}
                  >
                    <Icon size={16} className="shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-border px-3 py-3 text-xs text-text-secondary">
        <div className="flex items-center justify-between">
          <span className={collapsed ? 'sr-only' : ''}>Active Jobs</span>
          <span className="font-mono text-accent">{activeJobs.length}</span>
        </div>
        <div className="mt-1 flex items-center justify-between">
          <span className={collapsed ? 'sr-only' : ''}>Open Alerts</span>
          <span className="font-mono text-accent-red">{openAlerts.length}</span>
        </div>
      </div>
    </aside>
  )
}

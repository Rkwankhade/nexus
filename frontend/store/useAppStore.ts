import { create } from 'zustand'
import type { Alert, ToolJob } from '@/types'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void

  activeJobs: ToolJob[]
  setActiveJobs: (jobs: ToolJob[]) => void
  upsertJob: (job: ToolJob) => void

  openAlerts: Alert[]
  setOpenAlerts: (alerts: Alert[]) => void
  pushAlert: (alert: Alert) => void

  selectedTargetId: string | null
  setSelectedTargetId: (id: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  activeJobs: [],
  setActiveJobs: (jobs) => set({ activeJobs: jobs }),
  upsertJob: (job) =>
    set((s) => {
      const idx = s.activeJobs.findIndex((j) => j.id === job.id)
      if (idx === -1) return { activeJobs: [...s.activeJobs, job] }
      const next = [...s.activeJobs]
      next[idx] = job
      return { activeJobs: next }
    }),

  openAlerts: [],
  setOpenAlerts: (alerts) => set({ openAlerts: alerts }),
  pushAlert: (alert) => set((s) => ({ openAlerts: [alert, ...s.openAlerts].slice(0, 50) })),

  selectedTargetId: null,
  setSelectedTargetId: (id) => set({ selectedTargetId: id }),
}))

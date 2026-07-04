'use client'

import { useEffect } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import TopBar from '@/components/layout/TopBar'
import { nexusSocket } from '@/lib/socket'
import { useAppStore } from '@/store/useAppStore'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const upsertJob = useAppStore((s) => s.upsertJob)
  const pushAlert = useAppStore((s) => s.pushAlert)

  useEffect(() => {
    const socket = nexusSocket.connect()
    nexusSocket.subscribeToAlerts()
    nexusSocket.setHandlers({
      onAlert: (alert) =>
        pushAlert({
          id: alert.id,
          severity: alert.severity,
          title: alert.title,
          message: alert.message,
          source: 'realtime',
          created_at: alert.created_at,
          acknowledged: false,
        }),
      onScanProgress: (p) =>
        upsertJob({
          id: p.job_id,
          tool: p.tool,
          target_id: '',
          status: p.status,
          progress: p.progress,
        }),
    })
    return () => {
      socket.disconnect()
    }
  }, [pushAlert, upsertJob])

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}

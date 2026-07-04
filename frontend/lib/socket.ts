import { io, Socket } from 'socket.io-client'

type AlertPayload = {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  title: string
  message: string
  created_at: string
}

type ScanProgressPayload = {
  job_id: string
  tool: string
  progress: number
  status: 'queued' | 'running' | 'completed' | 'failed'
}

type LogEntryPayload = {
  id: string
  source: string
  message: string
  timestamp: string
}

type JobCompletePayload = {
  job_id: string
  tool: string
  success: boolean
}

type Handlers = {
  onAlert?: (payload: AlertPayload) => void
  onScanProgress?: (payload: ScanProgressPayload) => void
  onLogEntry?: (payload: LogEntryPayload) => void
  onJobComplete?: (payload: JobCompletePayload) => void
}

class NexusSocket {
  private socket: Socket | null = null
  private handlers: Handlers = {}
  private reconnectAttempts = 0
  private readonly maxDelay = 30000

  connect() {
    if (this.socket?.connected) return this.socket

    const token =
      typeof window !== 'undefined'
        ? localStorage.getItem('nexus_access_token')
        : null

    this.socket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
      path: '/ws/socket.io',
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: this.maxDelay,
      randomizationFactor: 0.5,
    })

    this.socket.on('connect', () => {
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', () => {
      this.reconnectAttempts += 1
    })

    this.socket.on('alert', (payload: AlertPayload) => this.handlers.onAlert?.(payload))
    this.socket.on('scan_progress', (payload: ScanProgressPayload) =>
      this.handlers.onScanProgress?.(payload)
    )
    this.socket.on('log_entry', (payload: LogEntryPayload) =>
      this.handlers.onLogEntry?.(payload)
    )
    this.socket.on('job_complete', (payload: JobCompletePayload) =>
      this.handlers.onJobComplete?.(payload)
    )

    return this.socket
  }

  setHandlers(handlers: Handlers) {
    this.handlers = { ...this.handlers, ...handlers }
  }

  subscribeToJob(jobId: string) {
    this.socket?.emit('subscribe', { room: `job:${jobId}` })
  }

  unsubscribeFromJob(jobId: string) {
    this.socket?.emit('unsubscribe', { room: `job:${jobId}` })
  }

  subscribeToAlerts() {
    this.socket?.emit('subscribe', { room: 'alerts' })
  }

  disconnect() {
    this.socket?.disconnect()
    this.socket = null
  }
}

export const nexusSocket = new NexusSocket()

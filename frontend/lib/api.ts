import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
})

// Attach bearer token to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('nexus_access_token')
    if (token) {
      config.headers = config.headers ?? {}
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

let isRefreshing = false
let pendingQueue: Array<() => void> = []

function flushQueue() {
  pendingQueue.forEach((cb) => cb())
  pendingQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingQueue.push(() => resolve(api(originalRequest)))
        })
      }

      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem('nexus_refresh_token')
        const { data } = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/refresh`,
          { refresh_token: refreshToken }
        )
        localStorage.setItem('nexus_access_token', data.access_token)
        flushQueue()
        return api(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('nexus_access_token')
        localStorage.removeItem('nexus_refresh_token')
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response?.status === 403 && typeof window !== 'undefined') {
      window.location.href = '/dashboard?error=forbidden'
    }

    return Promise.reject(error)
  }
)

export default api

// ---- Typed convenience wrappers -------------------------------------------------

export const endpoints = {
  targets: '/targets',
  scans: '/scans',
  findings: '/findings',
  reports: '/reports',
  alerts: '/alerts',
  ai: '/ai',
  blueteam: '/blueteam',
  forensics: '/forensics',
}

export async function getJson<T>(url: string, params?: Record<string, unknown>) {
  const { data } = await api.get<T>(url, { params })
  return data
}

export async function postJson<T>(url: string, body?: unknown) {
  const { data } = await api.post<T>(url, body)
  return data
}

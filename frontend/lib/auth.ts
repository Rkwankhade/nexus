import api from './api'
import type { Severity } from '@/types'

export interface NexusUser {
  id: string
  email: string
  username: string
  full_name: string
  role: 'admin' | 'analyst' | 'operator' | 'viewer'
  is_active: boolean
  mfa_enabled: boolean
  last_login?: string
  created_at: string
}

const ACCESS_KEY = 'nexus_access_token'
const REFRESH_KEY = 'nexus_refresh_token'
const USER_KEY = 'nexus_user'

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(ACCESS_KEY)
}

export function isAuthenticated(): boolean {
  return !!getAccessToken()
}

export function getStoredUser(): NexusUser | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as NexusUser
  } catch {
    return null
  }
}

export function storeSession(tokens: {
  access_token: string
  refresh_token: string
  user: NexusUser
}) {
  localStorage.setItem(ACCESS_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  localStorage.setItem(USER_KEY, JSON.stringify(tokens.user))
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

export async function login(username: string, password: string) {
  const { data } = await api.post('/auth/login', { username, password })
  storeSession(data)
  return data.user as NexusUser
}

export async function register(payload: {
  email: string
  username: string
  full_name?: string
  password: string
}) {
  const { data } = await api.post('/auth/register', payload)
  return data as NexusUser
}

export async function fetchMe(): Promise<NexusUser> {
  const { data } = await api.get('/auth/me')
  storeSessionUser(data)
  return data
}

function storeSessionUser(user: NexusUser) {
  if (typeof window === 'undefined') return
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function logout() {
  clearSession()
  if (typeof window !== 'undefined') window.location.href = '/login'
}

/** Simple role hierarchy check — used to gate UI actions client-side. Server always re-checks. */
const ROLE_RANK: Record<NexusUser['role'], number> = {
  viewer: 0,
  operator: 1,
  analyst: 2,
  admin: 3,
}

export function hasRole(user: NexusUser | null, minRole: NexusUser['role']): boolean {
  if (!user) return false
  return ROLE_RANK[user.role] >= ROLE_RANK[minRole]
}

export const SEVERITY_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info']

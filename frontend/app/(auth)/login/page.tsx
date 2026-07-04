'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ShieldCheck } from 'lucide-react'
import api from '@/lib/api'
export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { username: email, password })
      localStorage.setItem('nexus_access_token', data.access_token)
      localStorage.setItem('nexus_refresh_token', data.refresh_token)
      router.push('/dashboard')
    } catch {
      setError('Invalid credentials.')
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-cyber-grid">
      <form onSubmit={handleSubmit} className="card w-full max-w-sm space-y-4 p-6">
        <div className="flex items-center justify-center gap-2 pb-2">
          <ShieldCheck className="text-accent" size={22} />
          <span className="font-mono text-lg font-bold tracking-widest text-accent">
            NEXUS
          </span>
        </div>
        {error && (
          <p className="rounded-md bg-accent-red/10 px-3 py-2 text-xs text-accent-red">
            {error}
          </p>
        )}
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-accent py-2 text-sm font-semibold text-bg-primary hover:bg-accent/90 disabled:opacity-50"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
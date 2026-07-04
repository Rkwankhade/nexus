'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { getJson, postJson } from '@/lib/api'
import type { Target } from '@/types'

export default function TargetsPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [host, setHost] = useState('')
  const [notes, setNotes] = useState('')
  const [showForm, setShowForm] = useState(false)

  const { data: targets, isLoading } = useQuery<Target[]>({
    queryKey: ['targets'],
    queryFn: () => getJson<Target[]>('/targets'),
  })

  const createTarget = useMutation({
    mutationFn: () => postJson('/targets', { name, host, scope_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      setName('')
      setHost('')
      setNotes('')
      setShowForm(false)
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Targets</h1>
          <p className="text-sm text-text-secondary">Authorized engagement scope</p>
        </div>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-bg-primary hover:bg-accent/90"
        >
          <Plus size={14} /> New Target
        </button>
      </div>

      {showForm && (
        <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
          <input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
          <input
            placeholder="Host / CIDR / domain"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            className="rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
          <input
            placeholder="Scope notes / authorization ref"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none"
          />
          <button
            onClick={() => createTarget.mutate()}
            disabled={!name || !host || createTarget.isPending}
            className="rounded-md bg-accent-green/20 px-3 py-2 text-sm font-semibold text-accent-green hover:bg-accent-green/30 disabled:opacity-50 sm:col-span-3"
          >
            {createTarget.isPending ? 'Adding…' : 'Add Target'}
          </button>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[11px] uppercase text-text-muted">
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Host</th>
              <th className="px-4 py-2 font-medium">Scope Notes</th>
              <th className="px-4 py-2 font-medium">Added</th>
            </tr>
          </thead>
          <tbody>
            {targets?.map((t) => (
              <tr key={t.id} className="border-t border-border hover:bg-bg-elevated/50">
                <td className="px-4 py-2.5 text-text-primary">{t.name}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-text-secondary">{t.host}</td>
                <td className="px-4 py-2.5 text-xs text-text-secondary">
                  {t.scope_notes || '—'}
                </td>
                <td className="px-4 py-2.5 text-xs text-text-muted">
                  {new Date(t.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
            {!isLoading && targets?.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-xs text-text-muted">
                  No targets yet. Add one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

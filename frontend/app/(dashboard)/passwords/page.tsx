import { ShieldOff } from 'lucide-react'

export default function PasswordsPage() {
  return (
    <div className="card mx-auto mt-12 max-w-lg p-6 text-center">
      <ShieldOff size={28} className="mx-auto text-text-muted" />
      <h1 className="mt-3 text-lg font-bold text-text-primary">Not included in this build</h1>
      <p className="mt-2 text-sm text-text-secondary">
        Automated credential-cracking (hashcat/hydra/john orchestration) isn&apos;t
        part of this deployment. Working automation here gives real capability
        to attack credentials wherever it&apos;s pointed, authorized or not.
      </p>
      <p className="mt-3 text-xs text-text-muted">
        See the write-up in <code>backend/tools/password/NOTE.md</code>.
      </p>
    </div>
  )
}

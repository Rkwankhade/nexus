import { ShieldOff } from 'lucide-react'

export default function WirelessPage() {
  return (
    <div className="card mx-auto mt-12 max-w-lg p-6 text-center">
      <ShieldOff size={28} className="mx-auto text-text-muted" />
      <h1 className="mt-3 text-lg font-bold text-text-primary">Not included in this build</h1>
      <p className="mt-2 text-sm text-text-secondary">
        Wi-Fi handshake capture and cracking (aircrack-ng-style tooling) isn&apos;t
        part of this deployment for the same reason as the other tabs in this
        section — it&apos;s attack capability the code itself can&apos;t gate on
        authorization.
      </p>
      <p className="mt-3 text-xs text-text-muted">
        See the write-up in <code>backend/tools/wireless/NOTE.md</code>.
      </p>
    </div>
  )
}

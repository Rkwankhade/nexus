'use client'

import ToolLauncher from '@/components/tools/ToolLauncher'
import { SCANNING_TOOLS } from '@/lib/constants'

export default function ScannerPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Vulnerability Scanner</h1>
        <p className="text-sm text-text-secondary">
          Template & signature-based scanning against authorized targets
        </p>
      </div>

      <ToolLauncher
        tools={[...SCANNING_TOOLS]}
        dispatchEndpoint="/scans"
        category="scanning"
      />
    </div>
  )
}

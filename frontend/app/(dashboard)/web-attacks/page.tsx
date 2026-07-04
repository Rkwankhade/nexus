'use client'

import ToolLauncher from '@/components/tools/ToolLauncher'
import { WEB_TOOLS } from '@/lib/constants'

export default function WebAttacksPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Web Application Testing</h1>
        <p className="text-sm text-text-secondary">
          Content discovery, fuzzing, and XSS surface analysis
        </p>
      </div>

      <ToolLauncher tools={[...WEB_TOOLS]} dispatchEndpoint="/scans" category="web" />
    </div>
  )
}

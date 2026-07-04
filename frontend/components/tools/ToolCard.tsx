import { Play } from 'lucide-react'

export interface ToolMeta {
  id: string
  label: string
  description: string
}

export default function ToolCard({
  tool,
  onLaunch,
  disabled,
}: {
  tool: ToolMeta
  onLaunch: (toolId: string) => void
  disabled?: boolean
}) {
  return (
    <div className="card flex items-center justify-between p-3.5">
      <div className="min-w-0">
        <p className="font-mono text-sm font-semibold text-text-primary">{tool.label}</p>
        <p className="mt-0.5 text-xs text-text-secondary">{tool.description}</p>
      </div>
      <button
        onClick={() => onLaunch(tool.id)}
        disabled={disabled}
        className="flex shrink-0 items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-accent hover:border-accent hover:bg-accent/5 disabled:opacity-40"
      >
        <Play size={12} /> Run
      </button>
    </div>
  )
}

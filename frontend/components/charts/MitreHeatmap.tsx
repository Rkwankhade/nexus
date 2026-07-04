'use client'

interface Cell {
  tactic: string
  technique: string
  coverage: number // 0-100
}

function heat(coverage: number) {
  if (coverage === 0) return 'bg-bg-elevated'
  if (coverage < 25) return 'bg-accent/10'
  if (coverage < 50) return 'bg-accent/30'
  if (coverage < 75) return 'bg-accent/55'
  return 'bg-accent/85'
}

export default function MitreHeatmap({ cells }: { cells: Cell[] }) {
  const tactics = Array.from(new Set(cells.map((c) => c.tactic)))

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[560px] grid-flow-col gap-1" style={{ gridTemplateRows: 'auto 1fr' }}>
        {tactics.map((tactic) => (
          <div key={tactic} className="flex flex-col items-center gap-1">
            <span className="w-20 truncate text-center text-[10px] text-text-secondary" title={tactic}>
              {tactic}
            </span>
            <div className="flex flex-col gap-1">
              {cells
                .filter((c) => c.tactic === tactic)
                .map((c) => (
                  <div
                    key={c.technique}
                    title={`${c.technique} — ${c.coverage}% coverage`}
                    className={`h-5 w-20 rounded-sm ${heat(c.coverage)} border border-border`}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

'use client'

import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'

function gaugeColor(score: number) {
  if (score >= 75) return '#ff3366'
  if (score >= 50) return '#ff8c42'
  if (score >= 25) return '#ffd700'
  return '#00ff88'
}

export default function RiskGauge({ score }: { score: number }) {
  const data = [{ name: 'risk', value: score, fill: gaugeColor(score) }]

  return (
    <div className="relative h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          innerRadius="70%"
          outerRadius="100%"
          data={data}
          startAngle={220}
          endAngle={-40}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: '#1a2540' }} dataKey="value" cornerRadius={8} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-3xl font-bold text-text-primary">{score}</span>
        <span className="text-xs text-text-secondary">Risk Score</span>
      </div>
    </div>
  )
}

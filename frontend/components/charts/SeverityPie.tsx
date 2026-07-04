'use client'

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS: Record<string, string> = {
  critical: '#ff3366',
  high: '#ff8c42',
  medium: '#ffd700',
  low: '#00d4ff',
  info: '#4a5568',
}

interface Props {
  data: { severity: string; count: number }[]
}

export default function SeverityPie({ data }: Props) {
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="severity"
            innerRadius={45}
            outerRadius={70}
            paddingAngle={2}
          >
            {data.map((entry) => (
              <Cell key={entry.severity} fill={COLORS[entry.severity] || '#4a5568'} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#141d35',
              border: '1px solid #1e3a5f',
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

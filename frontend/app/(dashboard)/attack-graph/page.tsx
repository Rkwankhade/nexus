'use client'

import { useCallback, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useEdgesState,
  useNodesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { getJson } from '@/lib/api'
import type { GraphEdge, GraphNode, Target } from '@/types'

const SEVERITY_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#ff8c42',
  medium: '#ffd700',
  low: '#00d4ff',
  info: '#4a5568',
}

const TYPE_ICON: Record<string, string> = {
  host: '🖥',
  vuln: '🐞',
  cred: '🔑',
  service: '🔌',
}

function toFlowNode(n: GraphNode, i: number): Node {
  const color = n.severity ? SEVERITY_COLOR[n.severity] : '#00d4ff'
  return {
    id: n.id,
    position: { x: (i % 6) * 180, y: Math.floor(i / 6) * 120 },
    data: { label: `${TYPE_ICON[n.type] || ''} ${n.label}` },
    style: {
      background: '#141d35',
      color: '#e2e8f0',
      border: `1px solid ${color}`,
      borderRadius: 8,
      fontSize: 12,
      padding: 8,
    },
  }
}

function toFlowEdge(e: GraphEdge): Edge {
  return {
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    labelStyle: { fill: '#94a3b8', fontSize: 10 },
    style: { stroke: '#1e3a5f' },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#1e3a5f' },
  }
}

export default function AttackGraphPage() {
  const [targetId, setTargetId] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')

  const { data: targets } = useQuery<Target[]>({
    queryKey: ['targets'],
    queryFn: () => getJson<Target[]>('/targets'),
  })

  const { data: graph } = useQuery<{ nodes: GraphNode[]; edges: GraphEdge[] }>({
    queryKey: ['attack-graph', targetId],
    queryFn: () => getJson('/ai/attack-graph', { target_id: targetId }),
    enabled: !!targetId,
  })

  const filteredNodes = useMemo(() => {
    if (!graph) return []
    if (severityFilter === 'all') return graph.nodes
    return graph.nodes.filter((n) => n.severity === severityFilter)
  }, [graph, severityFilter])

  const [nodes, setNodes, onNodesChange] = useNodesState(
    filteredNodes.map(toFlowNode)
  )
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    (graph?.edges || []).map(toFlowEdge)
  )
  const [selected, setSelected] = useState<GraphNode | null>(null)

  const onNodeClick = useCallback(
    (_: unknown, node: Node) => {
      const found = graph?.nodes.find((n) => n.id === node.id) || null
      setSelected(found)
    },
    [graph]
  )

  function exportPng() {
    // Rendering to PNG happens client-side against the flow canvas element.
    const el = document.querySelector('.react-flow') as HTMLElement | null
    if (!el) return
    // Placeholder hook point — wire up html-to-image or similar in the app shell.
    window.print()
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Attack Graph</h1>
          <p className="text-sm text-text-secondary">
            Host / vulnerability / credential relationships
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className="rounded-md border border-border bg-bg-elevated px-3 py-1.5 text-xs text-text-primary"
          >
            <option value="">Select target…</option>
            {targets?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-md border border-border bg-bg-elevated px-3 py-1.5 text-xs text-text-primary"
          >
            <option value="all">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button
            onClick={exportPng}
            className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-xs text-text-secondary hover:text-accent"
          >
            <Download size={13} /> Export PNG
          </button>
        </div>
      </div>

      <div className="flex flex-1 gap-3">
        <div className="card flex-1 overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="#1e3a5f" gap={24} />
            <Controls />
            <MiniMap
              nodeColor={(n) => (n.style?.border as string) || '#00d4ff'}
              maskColor="rgba(10,14,26,0.7)"
              style={{ background: '#0f1629' }}
            />
          </ReactFlow>
        </div>

        <div className="card w-72 shrink-0 p-4">
          <h3 className="mb-2 text-sm font-semibold text-text-primary">Node Detail</h3>
          {selected ? (
            <div className="space-y-2 text-xs text-text-secondary">
              <p>
                <span className="text-text-muted">Type:</span> {selected.type}
              </p>
              <p>
                <span className="text-text-muted">Label:</span> {selected.label}
              </p>
              {selected.severity && (
                <p>
                  <span className="text-text-muted">Severity:</span> {selected.severity}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-text-muted">Select a node to view details.</p>
          )}
        </div>
      </div>
    </div>
  )
}

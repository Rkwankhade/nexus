'use client'

import { useEffect, useRef, useState } from 'react'
import { Copy, Download, Search } from 'lucide-react'
import type { Terminal as XTerm } from '@xterm/xterm'

interface OutputTerminalProps {
  jobId: string
  onLine?: (line: string) => void
}

const ANSI_CYAN = '\x1b[36m'
const ANSI_RED = '\x1b[31m'
const ANSI_GREEN = '\x1b[32m'
const ANSI_RESET = '\x1b[0m'

function colorize(line: string) {
  const lower = line.toLowerCase()
  if (lower.includes('error') || lower.includes('fail')) return `${ANSI_RED}${line}${ANSI_RESET}`
  if (lower.includes('success') || lower.includes('complete'))
    return `${ANSI_GREEN}${line}${ANSI_RESET}`
  if (lower.startsWith('[info]') || lower.startsWith('info'))
    return `${ANSI_CYAN}${line}${ANSI_RESET}`
  return line
}

export default function OutputTerminal({ jobId, onLine }: OutputTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const termRef = useRef<XTerm | null>(null)
  const bufferRef = useRef<string[]>([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    let disposed = false

    async function init() {
      const { Terminal } = await import('@xterm/xterm')
      const { FitAddon } = await import('@xterm/addon-fit')
      if (disposed || !containerRef.current) return

      const term = new Terminal({
        convertEol: true,
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 12,
        theme: {
          background: '#0a0e1a',
          foreground: '#e2e8f0',
          cursor: '#00d4ff',
        },
      })
      const fitAddon = new FitAddon()
      term.loadAddon(fitAddon)
      term.open(containerRef.current)
      fitAddon.fit()
      termRef.current = term

      const resizeObserver = new ResizeObserver(() => fitAddon.fit())
      resizeObserver.observe(containerRef.current)

      return () => resizeObserver.disconnect()
    }

    const cleanupPromise = init()
    return () => {
      disposed = true
      cleanupPromise.then((cleanup) => cleanup?.())
      termRef.current?.dispose()
    }
  }, [])

  function writeLine(line: string) {
    bufferRef.current.push(line)
    termRef.current?.writeln(colorize(line))
    termRef.current?.scrollToBottom()
    onLine?.(line)
  }

  // Exposed for parent components / websocket wiring
  useEffect(() => {
    ;(window as unknown as Record<string, unknown>)[`__nexusTermWrite_${jobId}`] = writeLine
    return () => {
      delete (window as unknown as Record<string, unknown>)[`__nexusTermWrite_${jobId}`]
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  function copyOutput() {
    navigator.clipboard.writeText(bufferRef.current.join('\n'))
  }

  function downloadOutput() {
    const blob = new Blob([bufferRef.current.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${jobId}-output.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  function runSearch() {
    if (!search || !termRef.current) return
    const idx = bufferRef.current.findIndex((l) => l.includes(search))
    if (idx >= 0) {
      termRef.current.scrollToLine(idx)
    }
  }

  return (
    <div className="card flex h-80 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <Search size={13} className="text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runSearch()}
            placeholder="filter output..."
            className="w-40 bg-transparent text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={copyOutput}
            className="rounded p-1 text-text-secondary hover:bg-bg-elevated hover:text-accent"
            aria-label="Copy output"
          >
            <Copy size={13} />
          </button>
          <button
            onClick={downloadOutput}
            className="rounded p-1 text-text-secondary hover:bg-bg-elevated hover:text-accent"
            aria-label="Download output"
          >
            <Download size={13} />
          </button>
        </div>
      </div>
      <div ref={containerRef} className="flex-1 px-2 py-1" />
    </div>
  )
}

'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Send, Paperclip, Trash2, Download, ChevronDown, ChevronUp, Copy } from 'lucide-react'
import api from '@/lib/api'
import type { ChatMessage } from '@/types'

type ContextMode = 'none' | 'target' | 'findings' | 'job'

const PRESETS = [
  'Summarize open findings for this target',
  'Suggest MITRE ATT&CK techniques relevant to these findings',
  'Explain this vulnerability in plain language',
  'Draft an executive summary for the current report',
  'What defensive controls would mitigate this finding?',
]

export default function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [context, setContext] = useState<ContextMode>('none')
  const [streaming, setStreaming] = useState(false)
  const [presetsOpen, setPresetsOpen] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text: string) {
    if (!text.trim() || streaming) return
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setStreaming(true)

    const assistantId = crypto.randomUUID()
    setMessages((m) => [
      ...m,
      { id: assistantId, role: 'assistant', content: '', created_at: new Date().toISOString() },
    ])

    try {
      const { data } = await api.post('/ai/chat', {
        message: text,
        context_mode: context,
      })
      setMessages((m) =>
        m.map((msg) => (msg.id === assistantId ? { ...msg, content: data.reply } : msg))
      )
    } catch {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId
            ? { ...msg, content: '_Error reaching AI service. Please try again._' }
            : msg
        )
      )
    } finally {
      setStreaming(false)
    }
  }

  function clearContext() {
    setMessages([])
  }

  function exportChat() {
    const text = messages.map((m) => `### ${m.role}\n${m.content}`).join('\n\n')
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'nexus-ai-chat.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card flex h-[600px] flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <h3 className="text-sm font-semibold text-text-primary">AI Assistant</h3>
        <div className="flex items-center gap-2">
          <select
            value={context}
            onChange={(e) => setContext(e.target.value as ContextMode)}
            className="rounded-md border border-border bg-bg-elevated px-2 py-1 text-xs text-text-secondary focus:outline-none"
          >
            <option value="none">No context</option>
            <option value="target">Current Target</option>
            <option value="findings">Current Findings</option>
            <option value="job">Current Job</option>
          </select>
          <button
            onClick={exportChat}
            className="rounded p-1.5 text-text-secondary hover:bg-bg-elevated hover:text-accent"
            aria-label="Export chat"
          >
            <Download size={14} />
          </button>
          <button
            onClick={clearContext}
            className="rounded p-1.5 text-text-secondary hover:bg-bg-elevated hover:text-accent-red"
            aria-label="Clear context"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="border-b border-border">
        <button
          onClick={() => setPresetsOpen((o) => !o)}
          className="flex w-full items-center justify-between px-4 py-2 text-xs text-text-secondary hover:text-accent"
        >
          <span>Preset prompts</span>
          {presetsOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
        {presetsOpen && (
          <div className="flex flex-wrap gap-2 px-4 pb-3">
            {PRESETS.map((p) => (
              <button
                key={p}
                onClick={() => sendMessage(p)}
                className="rounded-full border border-border bg-bg-elevated px-3 py-1 text-[11px] text-text-secondary hover:border-accent hover:text-accent"
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div
              className={
                m.role === 'user'
                  ? 'max-w-[80%] rounded-lg bg-accent/15 px-3 py-2 text-sm text-text-primary'
                  : 'max-w-[80%] rounded-lg bg-bg-elevated px-3 py-2 text-sm text-text-primary'
              }
            >
              <MarkdownMessage content={m.content || (streaming ? '▍' : '')} />
            </div>
          </div>
        ))}
        {messages.length === 0 && (
          <p className="py-10 text-center text-xs text-text-muted">
            Ask about findings, request remediation guidance, or use a preset prompt above.
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 border-t border-border p-3">
        <button
          className="rounded p-2 text-text-secondary hover:bg-bg-elevated hover:text-accent"
          aria-label="Attach file"
        >
          <Paperclip size={16} />
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
          placeholder="Ask the AI assistant..."
          className="flex-1 rounded-md border border-border bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={streaming}
          className="rounded-md bg-accent px-3 py-2 text-bg-primary hover:bg-accent/90 disabled:opacity-50"
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}

function MarkdownMessage({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '')
          const codeText = String(children).replace(/\n$/, '')
          if (match) {
            return (
              <div className="relative my-2">
                <button
                  onClick={() => navigator.clipboard.writeText(codeText)}
                  className="absolute right-2 top-2 rounded bg-bg-primary/70 p-1 text-text-secondary hover:text-accent"
                  aria-label="Copy code"
                >
                  <Copy size={12} />
                </button>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{ borderRadius: 8, fontSize: 12 }}
                >
                  {codeText}
                </SyntaxHighlighter>
              </div>
            )
          }
          return (
            <code className="rounded bg-bg-primary/60 px-1 py-0.5 text-xs" {...props}>
              {children}
            </code>
          )
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

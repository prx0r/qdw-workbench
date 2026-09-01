import { useState, useEffect, useRef, useCallback } from 'react'
import { invoke } from '@tauri-apps/api/core'

interface ChatMessage {
  role: 'user' | 'agent' | 'system'
  content: string
  timestamp: number
}

export function TerminalPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'Private Lab Terminal — talk to your agents, query HydraDB, run commands.', timestamp: Date.now() },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const outputRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [messages])

  const addMessage = (role: ChatMessage['role'], content: string) => {
    setMessages(m => [...m, { role, content, timestamp: Date.now() }])
  }

  const handleCommand = async (cmd: string) => {
    const trimmed = cmd.trim()
    if (!trimmed) return

    addMessage('user', trimmed)
    setBusy(true)

    try {
      // HydraDB shortcuts
      if (trimmed === '/health' || trimmed === '/status') {
        const r = await invoke('hydra_health')
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/summary') {
        const r = await invoke('hydra_summary')
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed.startsWith('/query ')) {
        const query = trimmed.slice(7)
        const r = await invoke('hydra_query', { query })
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/workers') {
        const r = await invoke('hydra_query', { query: 'MATCH (w:Worker) RETURN w.name AS name' })
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/runs') {
        const r = await invoke('hydra_query', { query: 'MATCH (r:Run) RETURN r.outcome AS outcome, r.studio AS studio LIMIT 20' })
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/experiments') {
        const r = await invoke('hydra_query', { query: 'MATCH (e:Experiment) RETURN e.hypothesis AS hypothesis, e.status AS status' })
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/findings') {
        const r = await invoke('hydra_query', { query: 'MATCH (f:Finding) RETURN f.claim AS claim, f.tier AS tier' })
        addMessage('system', JSON.stringify(r, null, 2))
      } else if (trimmed === '/help') {
        addMessage('system', [
          'Commands:',
          '  /health     — HydraDB connection status',
          '  /summary    — Lab summary (worker/run/experiment counts)',
          '  /workers    — List all workers',
          '  /runs       — Recent runs',
          '  /experiments — All experiments',
          '  /findings   — All findings',
          '  /query <cypher> — Run raw Cypher query',
          '  /clear      — Clear terminal',
          '',
          'Or just type naturally to talk to your agent.',
        ].join('\n'))
      } else if (trimmed === '/clear') {
        setMessages([])
      } else {
        // Default: treat as a Cypher query if it starts with MATCH/CREATE/MERGE
        if (/^(MATCH|CREATE|MERGE|RETURN)/i.test(trimmed)) {
          const r = await invoke('hydra_query', { query: trimmed })
          addMessage('system', JSON.stringify(r, null, 2))
        } else {
          addMessage('system', `Unknown command: ${trimmed}\nType /help for available commands.`)
        }
      }
    } catch (e: any) {
      addMessage('system', `Error: ${String(e)}`)
    }

    setBusy(false)
  }

  return (
    <div className="terminal-panel">
      <div className="terminal-output" ref={outputRef}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            {m.role === 'user' && <span style={{ color: '#4ade80' }}>$ </span>}
            {m.role === 'system' && <span style={{ color: '#747f8e' }}>· </span>}
            <pre style={{
              display: 'inline',
              margin: 0,
              color: m.role === 'user' ? '#e7eaf0' : m.role === 'system' ? '#bfc8d4' : '#fbbf24',
            }}>{m.content}</pre>
          </div>
        ))}
        {busy && <div style={{ color: '#747f8e' }}>· Processing...</div>}
      </div>
      <div className="terminal-input">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !busy) { handleCommand(input); setInput('') } }}
          placeholder="Type /help for commands, or a Cypher query..."
          disabled={busy}
        />
        <button onClick={() => { handleCommand(input); setInput('') }} disabled={busy || !input.trim()}>
          Run
        </button>
      </div>
    </div>
  )
}

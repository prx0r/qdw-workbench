import { useState, useEffect, useCallback } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { LabDashboard } from './components/LabDashboard'
import { TerminalPanel } from './components/TerminalPanel'
import { GraphPanel } from './components/GraphPanel'
import { AgentPanel } from './components/AgentPanel'
import './styles.css'

type Tab = 'dashboard' | 'terminal' | 'graph' | 'agents'

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard')
  const [hydraReady, setHydraReady] = useState(false)

  useEffect(() => {
    invoke('hydra_health').then((h: any) => {
      setHydraReady(h?.status === 'ready')
    }).catch(() => setHydraReady(false))
  }, [])

  return (
    <main>
      <header>
        <strong>PRIVATE LAB</strong>
        <span className={`status-dot ${hydraReady ? 'live' : 'dead'}`}>
          {hydraReady ? '● HYDRA LIVE' : '○ HYDRA OFFLINE'}
        </span>
        <nav>
          {(['dashboard', 'terminal', 'graph', 'agents'] as Tab[]).map(t => (
            <button key={t} className={tab === t ? 'on' : ''} onClick={() => setTab(t)}>
              {t === 'dashboard' ? '📊 Dashboard' :
               t === 'terminal' ? '⌨ Terminal' :
               t === 'graph' ? '🔗 Graph' : '🤖 Agents'}
            </button>
          ))}
        </nav>
      </header>
      <div className="layout">
        <section className="center">
          {tab === 'dashboard' && <LabDashboard />}
          {tab === 'terminal' && <TerminalPanel />}
          {tab === 'graph' && <GraphPanel />}
          {tab === 'agents' && <AgentPanel />}
        </section>
      </div>
      <footer>
        <span>Private Lab · HydraDB Native</span>
        <span>{hydraReady ? 'Graph connected' : 'Graph offline'}</span>
      </footer>
    </main>
  )
}

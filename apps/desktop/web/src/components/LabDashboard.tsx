import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'

interface LabSummary {
  workers: number
  versions: number
  runs: number
  studios: number
  experiments: number
  findings: number
  proposals: number
}

interface HydraHealth {
  status: string
  bolt: string
  workers: number
}

export function LabDashboard() {
  const [summary, setSummary] = useState<LabSummary | null>(null)
  const [health, setHealth] = useState<HydraHealth | null>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [findings, setFindings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    setLoading(true)
    try {
      const [s, h, r, f] = await Promise.all([
        invoke('hydra_summary'),
        invoke('hydra_health'),
        invoke('hydra_query', { query: 'MATCH (r:Run) RETURN r.outcome AS outcome, r.studio AS studio, r.task_family AS family LIMIT 20' }),
        invoke('hydra_query', { query: 'MATCH (f:Finding) RETURN f.claim AS claim, f.tier AS tier LIMIT 10' }),
      ])
      setSummary(s as LabSummary)
      setHealth(h as HydraHealth)
      setRuns(r as any[])
      setFindings(f as any[])
    } catch (e) {
      console.error('Dashboard load failed:', e)
    }
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  if (loading && !summary) return <div className="loading">Loading lab state...</div>

  return (
    <div className="lab-dashboard">
      <div className="dash-header">
        <h1>Lab Dashboard</h1>
        <button onClick={refresh} className="ghost">↻ Refresh</button>
      </div>

      {/* Summary cards */}
      <div className="metric-grid">
        <div className="card">
          <small>Workers</small>
          <b>{summary?.workers ?? 0}</b>
        </div>
        <div className="card">
          <small>Versions</small>
          <b>{summary?.versions ?? 0}</b>
        </div>
        <div className="card">
          <small>Runs</small>
          <b>{summary?.runs ?? 0}</b>
        </div>
        <div className="card">
          <small>Studios</small>
          <b>{summary?.studios ?? 0}</b>
        </div>
        <div className="card">
          <small>Experiments</small>
          <b>{summary?.experiments ?? 0}</b>
        </div>
        <div className="card">
          <small>Findings</small>
          <b>{summary?.findings ?? 0}</b>
        </div>
      </div>

      {/* HydraDB status */}
      <div className="card status-card">
        <div className="status-row">
          <span className={`status-dot ${health?.status === 'ready' ? 'live' : 'dead'}`}>
            {health?.status === 'ready' ? '● Connected' : '○ Offline'}
          </span>
          <small>{health?.bolt ?? 'unknown'}</small>
        </div>
      </div>

      {/* Recent runs */}
      <h3>Recent Runs</h3>
      {runs.length === 0 ? (
        <div className="empty">No runs recorded yet. Start a worker to see data here.</div>
      ) : (
        <div className="run-list">
          {runs.map((r, i) => (
            <div key={i} className="card">
              <div className="row">
                <span>{r.family || r.studio || 'unknown'}</span>
                <span className={`status ${r.outcome === 'won' ? 'won' : r.outcome === 'lost' ? 'lost' : ''}`}>
                  {r.outcome}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Findings */}
      <h3>Findings</h3>
      {findings.length === 0 ? (
        <div className="empty">No findings yet.</div>
      ) : (
        <div className="finding-list">
          {findings.map((f, i) => (
            <div key={i} className="card">
              <small>{f.tier}</small>
              <span>{f.claim}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

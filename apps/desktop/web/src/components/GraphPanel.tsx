import { useState } from 'react'
import { invoke } from '@tauri-apps/api/core'

export function GraphPanel() {
  const [query, setQuery] = useState('MATCH (n:Worker) RETURN n.name AS name LIMIT 10')
  const [results, setResults] = useState<any[] | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<string[]>([])

  const runQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      const r = await invoke('hydra_query', { query: query.trim() })
      setResults(r as any[])
      setHistory(h => [query.trim(), ...h].slice(0, 20))
    } catch (e: any) {
      setError(String(e))
      setResults(null)
    }
    setLoading(false)
  }

  const shortcuts = [
    { label: 'All Workers', q: 'MATCH (w:Worker) RETURN w.name AS name' },
    { label: 'All Runs', q: 'MATCH (r:Run) RETURN r.outcome AS outcome, r.studio AS studio LIMIT 20' },
    { label: 'All Experiments', q: 'MATCH (e:Experiment) RETURN e.hypothesis AS hypothesis, e.status AS status' },
    { label: 'All Findings', q: 'MATCH (f:Finding) RETURN f.claim AS claim, f.tier AS tier' },
    { label: 'Win Rate', q: 'MATCH (r:Run) RETURN r.studio AS studio, r.outcome AS outcome' },
    { label: 'Lab Summary', q: 'MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count' },
  ]

  return (
    <div className="graph-panel">
      <h1>Graph Query</h1>

      <div className="query-input">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runQuery() }}
          placeholder="MATCH (n:Worker) RETURN n.name AS name"
          rows={3}
        />
        <button onClick={runQuery} disabled={loading}>
          {loading ? 'Running...' : 'Run Query ⏎'}
        </button>
      </div>

      <div className="shortcuts">
        {shortcuts.map(s => (
          <button key={s.label} className="ghost" onClick={() => { setQuery(s.q); }}>
            {s.label}
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}

      {results && (
        <div className="results">
          <div className="results-header">
            <small>{results.length} rows returned</small>
          </div>
          {results.length === 0 ? (
            <div className="empty">No results.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  {Object.keys(results[0]).map(k => <th key={k}>{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {results.map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((v, j) => (
                      <td key={j}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {history.length > 0 && (
        <>
          <h3>Recent Queries</h3>
          <div className="history">
            {history.map((h, i) => (
              <button key={i} className="ghost" onClick={() => setQuery(h)}>
                {h.length > 60 ? h.slice(0, 60) + '...' : h}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

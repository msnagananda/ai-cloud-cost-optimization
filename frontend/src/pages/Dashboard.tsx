import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ProgressTracker from '../components/ProgressTracker'

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('token')}` }
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [regions, setRegions] = useState<string[]>([])
  const [region, setRegion] = useState('')
  const [running, setRunning] = useState(false)
  const [progressMessages, setProgressMessages] = useState<string[]>([])
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/regions', { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        setRegions(d.regions ?? [])
        if (d.regions?.length) setRegion(d.regions[0])
      })
      .catch(() => setError('Could not load AWS regions.'))
  }, [])

  async function runAnalysis() {
    setError('')
    setProgressMessages([])
    setDone(false)
    setRunning(true)

    // Reserve an analysis_id client-side for the WS connection.
    // The server will send the real DB id back in the response.
    const tempId = crypto.randomUUID()
    const ws = new WebSocket(`ws://localhost:9000/ws/progress/${tempId}`)
    ws.onmessage = e => {
      const msg = JSON.parse(e.data)
      setProgressMessages(prev => [...prev, msg.message])
      if (msg.message === 'Analysis complete') setDone(true)
    }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ region }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Analysis failed')
      ws.close()
      navigate(`/report/${data.analysis_id}`, { state: { report: data } })
    } catch (err: unknown) {
      ws.close()
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setRunning(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold mb-1">Run Analysis</h1>
        <p className="text-gray-500 text-sm mb-8">
          Select an AWS region and scan your active resources for cost issues.
        </p>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-5">
          {error && (
            <div className="bg-red-950 border border-red-800 text-red-400 text-sm rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">AWS Region</label>
            <select
              value={region}
              onChange={e => setRegion(e.target.value)}
              disabled={running}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:opacity-50"
            >
              {regions.map(r => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <button
            onClick={runAnalysis}
            disabled={running || !region}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition-colors flex items-center justify-center gap-2"
          >
            {running ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Running...
              </>
            ) : (
              '▶ Run Analysis'
            )}
          </button>
        </div>

        {(running || done) && (
          <div className="mt-6">
            <ProgressTracker messages={progressMessages} done={done} />
          </div>
        )}
      </main>
    </div>
  )
}

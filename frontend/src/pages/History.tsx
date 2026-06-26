import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

interface AnalysisRecord {
  id: string
  region: string
  resources_scanned: number
  issues_found: number
  estimated_savings: string
  status: string
  created_at: string
  analysis_result: Record<string, unknown> | null
}

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('token')}` }
}

export default function History() {
  const navigate = useNavigate()
  const [records, setRecords] = useState<AnalysisRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/history', { headers: authHeaders() })
      .then(async r => {
        if (r.status === 401) {
          localStorage.removeItem('token')
          localStorage.removeItem('email')
          navigate('/login')
          return
        }
        const d = await r.json()
        setRecords(d.analyses ?? [])
      })
      .catch(() => setError('Could not load history.'))
      .finally(() => setLoading(false))
  }, [navigate])

  function openReport(record: AnalysisRecord) {
    if (!record.analysis_result) return
    navigate(`/report/${record.id}`, {
      state: { report: { analysis_id: record.id, region: record.region, ...record.analysis_result } },
    })
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold mb-1">Analysis History</h1>
        <p className="text-gray-500 text-sm mb-8">Past scans for your account.</p>

        {loading && (
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <span className="w-4 h-4 border-2 border-gray-600 border-t-gray-300 rounded-full animate-spin" />
            Loading...
          </div>
        )}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && !error && records.length === 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center">
            <p className="text-gray-500 text-sm mb-3">No analyses yet.</p>
            <button
              onClick={() => navigate('/')}
              className="text-blue-500 hover:text-blue-400 text-sm"
            >
              Run your first analysis →
            </button>
          </div>
        )}

        <div className="space-y-3">
          {records.map(r => {
            const monthly = parseFloat(r.estimated_savings) || 0
            const yearly = monthly * 12
            return (
              <button
                key={r.id}
                onClick={() => openReport(r)}
                disabled={!r.analysis_result}
                className="w-full text-left bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-sm font-medium text-white">{r.region}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        r.status === 'completed'
                          ? 'bg-green-950 text-green-400'
                          : 'bg-yellow-950 text-yellow-400'
                      }`}>
                        {r.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(r.created_at).toLocaleString()} · {r.resources_scanned} resources · {r.issues_found} issues
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-green-400 font-medium text-sm">${monthly.toFixed(0)}/mo</p>
                    <p className="text-green-600 text-xs">${yearly.toFixed(0)}/yr</p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </main>
    </div>
  )
}

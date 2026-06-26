import { useState } from 'react'
import { useLocation, useParams, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'

interface Issue {
  severity: 'high' | 'medium' | 'low'
  resource_type: string
  resource_id: string
  issue: string
  estimated_monthly_savings_usd: number | null
  remediation: string
  cli_commands: string[]
}

interface ReportData {
  analysis_id: string
  region: string
  summary: string
  total_estimated_monthly_savings_usd: number
  total_resources_scanned: number
  active_services: string[]
  issues: Issue[]
}

const SEVERITY_STYLES: Record<string, string> = {
  high: 'bg-red-950 text-red-400 border-red-800',
  medium: 'bg-yellow-950 text-yellow-400 border-yellow-800',
  low: 'bg-blue-950 text-blue-400 border-blue-800',
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
    >
      {copied ? '✓ copied' : 'copy'}
    </button>
  )
}

export default function Report() {
  const { analysisId } = useParams()
  const location = useLocation()
  const report = location.state?.report as ReportData | undefined

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        <main className="max-w-3xl mx-auto px-6 py-10 text-center">
          <p className="text-gray-500 mb-4">Report data not found.</p>
          <Link to="/history" className="text-blue-500 hover:text-blue-400 text-sm">View history</Link>
        </main>
      </div>
    )
  }

  const high = report.issues.filter(i => i.severity === 'high')
  const medium = report.issues.filter(i => i.severity === 'medium')
  const low = report.issues.filter(i => i.severity === 'low')

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link to="/" className="hover:text-gray-300">Dashboard</Link>
            <span>/</span>
            <span>Report</span>
          </div>
          <h1 className="text-2xl font-bold">Analysis Report</h1>
          <p className="text-gray-500 text-sm mt-1">{report.region} · {report.total_resources_scanned} resources scanned</p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Est. Monthly Savings</p>
            <p className="text-2xl font-bold text-green-400">${report.total_estimated_monthly_savings_usd.toFixed(0)}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Issues Found</p>
            <p className="text-2xl font-bold">{report.issues.length}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">By Severity</p>
            <p className="text-sm">
              <span className="text-red-400 font-medium">{high.length}H</span>
              {' · '}
              <span className="text-yellow-400 font-medium">{medium.length}M</span>
              {' · '}
              <span className="text-blue-400 font-medium">{low.length}L</span>
            </p>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Summary</h2>
          <p className="text-gray-300 text-sm leading-relaxed">{report.summary}</p>
        </div>

        {/* Issues */}
        <div>
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Issues</h2>
          {report.issues.length === 0 ? (
            <p className="text-gray-600 text-sm">No issues found.</p>
          ) : (
            <div className="space-y-4">
              {report.issues.map((issue, i) => (
                <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded border uppercase ${SEVERITY_STYLES[issue.severity]}`}>
                        {issue.severity}
                      </span>
                      <span className="text-xs text-gray-500">{issue.resource_type}</span>
                      <code className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded">{issue.resource_id}</code>
                    </div>
                    {issue.estimated_monthly_savings_usd != null && (
                      <span className="text-green-400 text-sm font-medium whitespace-nowrap">
                        ~${issue.estimated_monthly_savings_usd}/mo
                      </span>
                    )}
                  </div>

                  <p className="text-white text-sm font-medium mb-2">{issue.issue}</p>
                  <p className="text-gray-400 text-sm mb-3">{issue.remediation}</p>

                  {issue.cli_commands.length > 0 && (
                    <div className="space-y-2">
                      {issue.cli_commands.map((cmd, j) => (
                        <div key={j} className="bg-gray-950 rounded-lg px-4 py-3 flex items-start justify-between gap-3">
                          <code className="text-xs text-green-400 font-mono break-all">{cmd}</code>
                          <CopyButton text={cmd} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

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
  low: 'bg-green-950 text-green-400 border-green-800',
}

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 }

function classifyIssueType(issue: string): string {
  const l = issue.toLowerCase()
  if (l.includes('idle') || l.includes('unused') || l.includes('unattached') || l.includes('orphan')) return 'unused'
  if (l.includes('over-provision') || l.includes('overprovis') || l.includes('oversized') || l.includes('t2') || l.includes('gp2')) return 'over-provisioned'
  return 'misconfigured'
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      className="text-xs text-gray-500 hover:text-gray-300 transition-colors whitespace-nowrap"
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
          <Link to="/history" className="text-blue-500 hover:text-blue-400 text-sm">View history →</Link>
        </main>
      </div>
    )
  }

  const monthlySavings = report.total_estimated_monthly_savings_usd ?? 0
  const yearlySavings = monthlySavings * 12

  const sortedIssues = [...(report.issues ?? [])].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
  )
  const high = sortedIssues.filter(i => i.severity === 'high')
  const medium = sortedIssues.filter(i => i.severity === 'medium')
  const low = sortedIssues.filter(i => i.severity === 'low')

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* Breadcrumb + header */}
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link to="/" className="hover:text-gray-300">Dashboard</Link>
            <span>/</span>
            <Link to="/history" className="hover:text-gray-300">History</Link>
            <span>/</span>
            <span>Report</span>
          </div>
          <h1 className="text-2xl font-bold">Analysis Report</h1>
          <p className="text-gray-500 text-sm mt-1">{report.region}</p>
        </div>

        {/* Summary cards — 4 columns */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Resources Scanned</p>
            <p className="text-2xl font-bold">{report.total_resources_scanned}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Issues Found</p>
            <p className="text-2xl font-bold">
              {sortedIssues.length}
              <span className="text-sm font-normal text-gray-500 ml-1">
                (<span className="text-red-400">{high.length}</span>
                ·<span className="text-yellow-400">{medium.length}</span>
                ·<span className="text-green-400">{low.length}</span>)
              </span>
            </p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Monthly Savings</p>
            <p className="text-2xl font-bold text-green-400">${monthlySavings.toFixed(0)}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Yearly Savings</p>
            <p className="text-2xl font-bold text-green-300">${yearlySavings.toFixed(0)}</p>
          </div>
        </div>

        {/* Active services */}
        {report.active_services?.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Active Billing Services</h2>
            <div className="flex flex-wrap gap-2">
              {report.active_services.map(s => (
                <span key={s} className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* AI Summary */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Summary</h2>
          <p className="text-gray-300 text-sm leading-relaxed">{report.summary}</p>
        </div>

        {/* Issues */}
        <div>
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-4">Issues</h2>
          {sortedIssues.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
              <p className="text-green-400 font-medium mb-1">No issues found</p>
              <p className="text-gray-600 text-sm">Your infrastructure looks optimised.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sortedIssues.map((issue, i) => {
                const issueType = classifyIssueType(issue.issue)
                return (
                  <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded border uppercase ${SEVERITY_STYLES[issue.severity] ?? SEVERITY_STYLES.low}`}>
                          {issue.severity}
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded capitalize">
                          {issueType}
                        </span>
                        <span className="text-xs text-gray-500">{issue.resource_type}</span>
                      </div>
                      {issue.estimated_monthly_savings_usd != null && (
                        <span className="text-green-400 text-sm font-medium whitespace-nowrap flex-shrink-0">
                          ~${issue.estimated_monthly_savings_usd}/mo
                        </span>
                      )}
                    </div>

                    <code className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded block mb-2 break-all">
                      {issue.resource_id}
                    </code>

                    <p className="text-white text-sm font-medium mb-1">{issue.issue}</p>
                    <p className="text-gray-400 text-sm mb-3">{issue.remediation}</p>

                    {issue.cli_commands.length > 0 && (
                      <div className="space-y-2">
                        {issue.cli_commands.map((cmd, j) => (
                          <div key={j} className="bg-gray-950 rounded-lg px-4 py-3 flex items-start justify-between gap-3">
                            <code className="text-xs text-green-400 font-mono break-all leading-relaxed">{cmd}</code>
                            <CopyButton text={cmd} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-gray-800 flex gap-4">
          <Link to="/" className="text-sm text-blue-500 hover:text-blue-400">← New Analysis</Link>
          <Link to="/history" className="text-sm text-gray-500 hover:text-gray-300">View History</Link>
        </div>
      </main>
    </div>
  )
}

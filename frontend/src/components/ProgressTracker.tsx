interface Props {
  messages: string[]
  done: boolean
}

const STEPS = [
  'Querying AWS Cost Explorer for active services...',
  'Scanning active services',
  'Analyzing costs with AI...',
  'Storing results...',
  'Analysis complete',
]

export default function ProgressTracker({ messages, done }: Props) {
  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Progress</h3>
      <ol className="space-y-3">
        {STEPS.map((step, i) => {
          const matched = messages.find(m => m.startsWith(step.slice(0, 20)))
          const isActive = !matched && messages.length === i
          const isDone = !!matched || (done && i < STEPS.length - 1)

          return (
            <li key={step} className="flex items-start gap-3">
              <span className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                isDone || (done && step === 'Analysis complete')
                  ? 'bg-green-600 text-white'
                  : isActive
                  ? 'bg-blue-600 text-white animate-pulse'
                  : 'bg-gray-700 text-gray-500'
              }`}>
                {isDone || (done && step === 'Analysis complete') ? '✓' : i + 1}
              </span>
              <span className={`text-sm ${
                isDone || (done && step === 'Analysis complete')
                  ? 'text-gray-300'
                  : isActive
                  ? 'text-blue-400'
                  : 'text-gray-600'
              }`}>
                {step}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

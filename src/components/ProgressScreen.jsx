import { Check, Loader2 } from 'lucide-react'
import { Skeleton } from './ui'

const STEPS = [
  ['metadata', 'Reel metadata'], ['comments', 'Comments'], ['clean', 'Spam & duplicates'],
  ['sentiment', 'Sentiment'], ['emotion', 'Emotion'], ['aspects', 'Aspects'], ['nlp', 'NLP analytics'], ['engagement', 'Engagement'], ['finalize', 'Report'],
]

export default function ProgressScreen({ progress, isDemo }) {
  const cur = progress?.stage
  const idx = Math.max(0, STEPS.findIndex(([k]) => k === cur))
  const pct = progress?.percent ?? 2
  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
      <div className="card rise mx-auto max-w-xl p-6" aria-live="polite">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2 font-medium"><Loader2 size={16} className="animate-spin text-accent" />{'Analyzing Reel'}</span>
          <span className="tabular-nums text-muted">{pct}%</span>
        </div>
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-card2" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 transition-all duration-500" style={{ width: `${pct}%` }} />
        </div>
        <p className="mt-3 min-h-5 text-sm text-muted">{progress?.message || 'Starting…'}</p>
        <ol className="mt-5 grid grid-cols-3 gap-x-3 gap-y-2 text-xs">
          {STEPS.map(([k, label], i) => (
            <li key={k} className={`flex items-center gap-1.5 ${i < idx ? 'text-fg' : i === idx ? 'text-accent' : 'text-muted/60'}`}>
              {i < idx ? <Check size={12} className="text-pos" /> : <span className={`size-1.5 rounded-full ${i === idx ? 'animate-pulse bg-accent' : 'bg-border'}`} />}
              {label}
            </li>
          ))}
        </ol>
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-hidden>
        {[0, 1, 2, 3].map((i) => <div key={i} className="card p-5"><Skeleton className="h-3 w-16" /><Skeleton className="mt-4 h-8 w-24" /><Skeleton className="mt-3 h-3 w-20" /></div>)}
        <div className="card p-5 sm:col-span-2"><Skeleton className="h-3 w-28" /><Skeleton className="mt-4 h-40 w-full" /></div>
        <div className="card p-5 sm:col-span-2"><Skeleton className="h-3 w-28" /><Skeleton className="mt-4 h-40 w-full" /></div>
      </div>
    </div>
  )
}

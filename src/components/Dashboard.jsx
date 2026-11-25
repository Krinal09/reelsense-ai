import { useState } from 'react'
import { AlertTriangle, BarChart3, Download, FlaskConical, Info, MessageSquareText, Sparkles } from 'lucide-react'
import Overview from './Overview'
import CommentsExplorer from './CommentsExplorer'
import InsightsPanel from './InsightsPanel'
import ExportPanel from './ExportPanel'
import { Badge, Banner } from './ui'
import { dateFmt } from '../lib/format'

const TABS = [
  ['overview', 'Overview', BarChart3], ['comments', 'Comments', MessageSquareText], ['insights', 'AI Insights', Sparkles], ['export', 'Export', Download],
]

export default function Dashboard({ analysis: a }) {
  const [tab, setTab] = useState('overview')
  const r = a.reel
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="card rise flex flex-col gap-5 p-5 sm:flex-row sm:items-center">
        <div className="h-28 w-16 shrink-0 overflow-hidden rounded-xl border border-border bg-card2">
          {r.thumbnail ? <img src={r.thumbnail} alt="Reel thumbnail" className="size-full object-cover" referrerPolicy="no-referrer" /> : null}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight">@{r.username || 'unknown'}</h1>
            {a.is_demo ? <Badge tone="warn"><FlaskConical size={11} />Demo · sample data</Badge> : <Badge tone="pos">Live data</Badge>}
            {r.duration_seconds != null && <Badge>{r.duration_seconds}s</Badge>}
          </div>
          <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted">{r.caption || 'No caption available.'}</p>
          <p className="mt-2 flex flex-wrap items-center gap-x-3 text-xs text-muted">
            <span>Published {dateFmt(r.published_at)}</span>
            <a href={r.url} target={a.is_demo ? undefined : '_blank'} rel="noreferrer" onClick={(e) => a.is_demo && e.preventDefault()} className="truncate text-accent hover:underline">{r.url}</a>
            <span>Analysis took {a.processing_seconds}s</span>
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {a.is_demo && <Banner tone="warn" icon={FlaskConical}><b>Sample data.</b> The Reel, metrics and comments are generated for demonstration. The sentiment/NLP pipeline running on them is real.</Banner>}
        {a.warnings.filter((w) => !w.startsWith('Demo mode')).map((w, i) => <Banner key={i} tone="warn" icon={AlertTriangle}>{w}</Banner>)}
        {a.summary.reel_total_comments != null && a.summary.fetched < a.summary.reel_total_comments && (
          <Banner icon={Info}>Analysis covers {a.summary.fetched} of {a.summary.reel_total_comments.toLocaleString()} total comments – only the comments the data source exposes were collected.</Banner>)}
      </div>

      <nav className="mt-6 flex gap-1 overflow-x-auto border-b border-border" role="tablist">
        {TABS.map(([k, label, Icon]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
            className={`-mb-px flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition ${tab === k ? 'border-accent text-fg' : 'border-transparent text-muted hover:text-fg'}`}>
            <Icon size={15} />{label}
          </button>))}
      </nav>

      <div className="mt-6" role="tabpanel" key={tab}>
        <div className="rise">
          {tab === 'overview' && <Overview a={a} />}
          {tab === 'comments' && <CommentsExplorer comments={a.comments} />}
          {tab === 'insights' && <InsightsPanel a={a} />}
          {tab === 'export' && <ExportPanel analysis={a} />}
        </div>
      </div>

      <footer className="mt-12 border-t border-border pt-5 text-xs leading-relaxed text-muted">
        Models — sentiment: {a.engines.sentiment}; emotion: {a.engines.emotion}. Provider: {a.provider}.
      </footer>
    </div>
  )
}

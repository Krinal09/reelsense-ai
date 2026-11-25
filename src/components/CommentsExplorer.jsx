import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Heart, MessageSquare, Search, SearchX } from 'lucide-react'
import { Badge, Card, EmptyState, SentimentBadge } from './ui'
import { EMO_COLOR, EMO_EMOJI, dateTimeFmt } from '../lib/format'

const PAGE = 15
const COLS = [
  ['username', 'Username'], ['text', 'Comment'], ['sentiment', 'Sentiment'], ['emotion', 'Emotion'],
  ['confidence', 'Confidence'], ['likes', 'Likes'], ['timestamp', 'Date'],
]

export default function CommentsExplorer({ comments }) {
  const [q, setQ] = useState('')
  const [sent, setSent] = useState('all')
  const [emo, setEmo] = useState('all')
  const [lang, setLang] = useState('all')
  const [spam, setSpam] = useState(false)
  const [sort, setSort] = useState({ key: 'likes', dir: 'desc' })
  const [page, setPage] = useState(1)

  const langs = useMemo(() => [...new Set(comments.map((c) => c.language))].sort(), [comments])
  const emos = useMemo(() => [...new Set(comments.map((c) => c.emotion))].sort(), [comments])

  const rows = useMemo(() => {
    const ql = q.trim().toLowerCase()
    let r = comments.filter((c) =>
      (spam || !c.is_spam) && (sent === 'all' || c.sentiment === sent) && (emo === 'all' || c.emotion === emo) && (lang === 'all' || c.language === lang) &&
      (!ql || c.text.toLowerCase().includes(ql) || (c.username || '').toLowerCase().includes(ql)))
    const dir = sort.dir === 'asc' ? 1 : -1
    return r.sort((a, b) => {
      const x = a[sort.key] ?? (sort.key === 'text' || sort.key === 'username' ? '' : -1), y = b[sort.key] ?? (typeof x === 'string' ? '' : -1)
      return (x > y ? 1 : x < y ? -1 : 0) * dir
    })
  }, [comments, q, sent, emo, lang, spam, sort])

  const pages = Math.max(1, Math.ceil(rows.length / PAGE))
  const cur = Math.min(page, pages)
  const view = rows.slice((cur - 1) * PAGE, cur * PAGE)
  const reset = (fn) => (v) => { fn(v); setPage(1) }
  const toggle = (key) => setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: key === 'username' || key === 'text' ? 'asc' : 'desc' }))
  const counts = useMemo(() => ({ all: comments.filter((c) => spam || !c.is_spam).length, positive: 0, negative: 0, neutral: 0, ...Object.fromEntries(['positive', 'negative', 'neutral'].map((s) => [s, comments.filter((c) => (spam || !c.is_spam) && c.sentiment === s).length])) }), [comments, spam])

  return (
    <Card className="!p-0 overflow-hidden">
      <div className="space-y-3 border-b border-border p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <label className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input value={q} onChange={(e) => reset(setQ)(e.target.value)} placeholder="Search comments or usernames…" aria-label="Search comments"
              className="h-10 w-full rounded-lg border border-border bg-bg pl-9 pr-3 text-sm outline-none placeholder:text-muted/70 focus:border-accent" />
          </label>
          <div className="flex flex-wrap gap-2">
            <Select label="Emotion" value={emo} onChange={reset(setEmo)} options={emos} />
            <Select label="Language" value={lang} onChange={reset(setLang)} options={langs} />
            <label className="flex h-10 items-center gap-2 rounded-lg border border-border bg-bg px-3 text-xs text-muted">
              <input type="checkbox" checked={spam} onChange={(e) => reset(setSpam)(e.target.checked)} className="accent-[var(--accent)]" /> Show spam
            </label>
          </div>
        </div>
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Sentiment filter">
          {['all', 'positive', 'negative', 'neutral'].map((s) => (
            <button key={s} role="tab" aria-selected={sent === s} onClick={() => reset(setSent)(s)}
              className={`rounded-full border px-3 py-1 text-xs font-medium capitalize transition ${sent === s ? 'border-accent bg-accent/10 text-accent' : 'border-border text-muted hover:text-fg'}`}>
              {s} <span className="ml-1 tabular-nums opacity-70">{counts[s]}</span>
            </button>
          ))}
        </div>
      </div>

      {view.length === 0 ? <EmptyState icon={SearchX} title="No comments match these filters">Try clearing the search or choosing a different sentiment, emotion or language.</EmptyState> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="bg-card2/60 text-xs text-muted">
              <tr>{COLS.map(([k, label]) => (
                <th key={k} className="whitespace-nowrap px-4 py-2.5 font-medium" aria-sort={sort.key === k ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                  <button onClick={() => toggle(k)} className="inline-flex items-center gap-1 hover:text-fg">{label}
                    {sort.key === k && (sort.dir === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}</button>
                </th>))}</tr>
            </thead>
            <tbody>
              {view.map((c) => (
                <tr key={c.id} className="border-t border-border align-top hover:bg-card2/40">
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted">@{c.username || 'unknown'}</td>
                  <td className="max-w-md px-4 py-3">
                    <p className="whitespace-pre-wrap break-words leading-snug">{c.text}</p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <Badge>{c.language}</Badge>
                      {c.is_question && <Badge tone="accent">Question</Badge>}
                      {c.is_spam && <Badge tone="neg">Spam</Badge>}
                      {c.is_duplicate && <Badge tone="warn">Duplicate</Badge>}
                      {c.reply_count > 0 && <Badge><MessageSquare size={10} />{c.reply_count}</Badge>}
                      {(c.aspects || []).slice(0, 3).map((x) => <Badge key={x.aspect} tone={{ positive: 'pos', negative: 'neg', neutral: 'neutral' }[x.sentiment]}>{x.aspect}</Badge>)}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3"><SentimentBadge value={c.sentiment} /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs"><span className="inline-flex items-center gap-1.5"><span className="size-2 rounded-full" style={{ background: EMO_COLOR[c.emotion] }} />{EMO_EMOJI[c.emotion]} {c.emotion}</span></td>
                  <td className="whitespace-nowrap px-4 py-3 tabular-nums text-xs text-muted">{Math.round(c.confidence * 100)}%</td>
                  <td className="whitespace-nowrap px-4 py-3 tabular-nums text-xs"><span className="inline-flex items-center gap-1 text-muted"><Heart size={11} />{c.likes ?? '—'}</span></td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted">{dateTimeFmt(c.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted">
        <span>{rows.length ? `${(cur - 1) * PAGE + 1}–${Math.min(cur * PAGE, rows.length)} of ${rows.length}` : '0 results'}</span>
        <div className="flex items-center gap-1">
          <button disabled={cur <= 1} onClick={() => setPage(cur - 1)} className="grid size-8 place-items-center rounded-lg border border-border hover:bg-card2 disabled:opacity-40" aria-label="Previous page"><ChevronLeft size={14} /></button>
          <span className="px-2 tabular-nums">Page {cur} / {pages}</span>
          <button disabled={cur >= pages} onClick={() => setPage(cur + 1)} className="grid size-8 place-items-center rounded-lg border border-border hover:bg-card2 disabled:opacity-40" aria-label="Next page"><ChevronRight size={14} /></button>
        </div>
      </div>
    </Card>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="flex h-10 items-center gap-2 rounded-lg border border-border bg-bg pl-3 pr-1 text-xs text-muted">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)} className="h-8 rounded-md bg-transparent pr-1 text-xs text-fg outline-none">
        <option value="all">All</option>{options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  )
}

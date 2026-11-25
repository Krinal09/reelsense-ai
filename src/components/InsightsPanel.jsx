import { Compass, HelpCircle, Lightbulb, Megaphone, MessageSquareWarning, Sparkles, ThumbsDown, ThumbsUp, Wrench } from 'lucide-react'
import { Badge, Card, EmptyState } from './ui'

const toneFor = (label = '') => (/positive/i.test(label) ? 'pos' : /negative/i.test(label) ? 'neg' : 'neutral')

export default function InsightsPanel({ a }) {
  const ins = a.insights
  const r = ins.audience_reaction
  return (
    <div className="space-y-4">
      <div className="card rise relative overflow-hidden p-6">
        <div className="hero-glow pointer-events-none absolute inset-0 opacity-60" />
        <div className="relative">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-medium text-accent"><Sparkles size={14} />Executive summary</span>
            {a.is_demo && <Badge tone="warn">Sample data</Badge>}
          </div>
          <p className="max-w-4xl text-[15px] leading-relaxed">{ins.executive_summary}</p>
          <p className="mt-3 text-xs text-muted">{ins.method}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Audience reaction" action={<Compass size={15} className="text-muted" />}>
          <Badge tone={toneFor(r.label)} className="!text-xs">{r.label}</Badge>
          <p className="mt-3 text-sm leading-relaxed text-muted">{r.text}</p>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
            <Mini label="Positive" v={r.positive_pct} c="var(--pos)" /><Mini label="Negative" v={r.negative_pct} c="var(--neg)" /><Mini label="Neutral" v={r.neutral_pct} c="var(--neu)" />
          </div>
          {r.dominant_emotion && <p className="mt-4 text-xs text-muted">Dominant emotion: <b className="text-fg">{r.dominant_emotion}</b></p>}
        </Card>
        <Feedback title="Top positive feedback" icon={ThumbsUp} items={ins.top_positive_feedback} tone="pos" fallback={ins.praised_comments} />
        <Feedback title="Top negative feedback" icon={ThumbsDown} items={ins.top_negative_feedback} tone="neg" fallback={ins.common_complaints} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Common complaints" subtitle="Most-liked negative comments" action={<MessageSquareWarning size={15} className="text-muted" />}>
          {ins.common_complaints.length ? <ul className="space-y-3">{ins.common_complaints.map((c, i) => (
            <li key={i} className="rounded-lg border border-border bg-card2/40 p-3 text-sm">
              <p className="leading-snug">“{c.text}”</p>
              <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">{c.likes} likes · {c.language}{c.aspects.map((x) => <Badge key={x} tone="neg">{x}</Badge>)}</p>
            </li>))}</ul> : <EmptyState icon={ThumbsUp} title="No negative comments">Nothing to complain about in this sample.</EmptyState>}
        </Card>
        <Card title="Frequently asked questions" action={<HelpCircle size={15} className="text-muted" />}>
          {ins.frequently_asked_questions.length ? <ul className="space-y-3">{ins.frequently_asked_questions.map((q, i) => (
            <li key={i} className="flex items-start justify-between gap-3 text-sm"><span className="leading-snug">{q.question}</span><Badge tone="accent">asked ×{q.count}</Badge></li>))}</ul>
            : <EmptyState icon={HelpCircle} title="No questions detected" />}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Most discussed" subtitle="Topics and aspects by comment volume" action={<Megaphone size={15} className="text-muted" />}>
          <ul className="space-y-2.5 text-sm">
            {ins.most_discussed_topics.map((t) => <li key={t.topic} className="flex justify-between gap-3"><span className="capitalize">{t.topic}</span><span className="text-muted tabular-nums">{t.comments} comments · {t.share}%</span></li>)}
            {ins.most_discussed_aspects.map((t) => <li key={t.aspect} className="flex justify-between gap-3"><span>{t.aspect} <Badge className="ml-1">aspect</Badge></span><span className="text-muted tabular-nums">{t.mentions} mentions</span></li>)}
            {!ins.most_discussed_topics.length && !ins.most_discussed_aspects.length && <EmptyState title="Not enough data" />}
          </ul>
        </Card>
        <Card title="Content improvement suggestions" subtitle="Each one is tied to evidence from the comments" action={<Wrench size={15} className="text-muted" />}>
          <ul className="space-y-3 text-sm">{ins.improvement_suggestions.map((s, i) => (
            <li key={i}><p className="leading-snug">{s.suggestion}</p><p className="mt-0.5 text-xs text-muted">Evidence: {s.evidence}</p></li>))}</ul>
        </Card>
      </div>

      <Card title="Recommended next content" subtitle="Derived from questions, topics and appreciated aspects" action={<Lightbulb size={15} className="text-muted" />}>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {ins.next_content_ideas.map((s, i) => (
            <div key={i} className="rounded-xl border border-border bg-card2/40 p-4"><p className="text-sm font-medium leading-snug">{s.idea}</p><p className="mt-2 text-xs text-muted">Why: {s.basis}</p></div>))}
        </div>
      </Card>
    </div>
  )
}

const Mini = ({ label, v, c }) => <div className="rounded-lg bg-card2 py-2"><p className="text-base font-semibold tabular-nums" style={{ color: c }}>{v ?? '—'}%</p><p className="text-[11px] text-muted">{label}</p></div>

function Feedback({ title, icon: Icon, items, tone, fallback }) {
  return (
    <Card title={title} action={<Icon size={15} className="text-muted" />}>
      {items.length ? <ul className="space-y-3">{items.map((x) => (
        <li key={x.theme} className="text-sm">
          <div className="flex items-center justify-between"><span className="font-medium">{x.theme}</span><Badge tone={tone}>{x.count} of {x.mentions}</Badge></div>
          {x.example && <p className="mt-1 text-xs italic leading-snug text-muted">“{x.example}”</p>}
        </li>))}</ul>
        : fallback?.length ? <ul className="space-y-2 text-sm">{fallback.slice(0, 3).map((c, i) => <li key={i} className="italic text-muted">“{c.text}”</li>)}</ul>
        : <EmptyState title="Nothing notable" />}
    </Card>
  )
}

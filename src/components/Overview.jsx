import { Eye, Heart, MessageCircle, Percent, Hash, HelpCircle, Layers3, ThumbsUp, ThumbsDown, Copy, ShieldAlert, Trophy } from 'lucide-react'
import { Badge, Card, EmptyState, SentimentBadge } from './ui'
import { AspectChart, EmotionChart, EngagementChart, LanguageBars, SentimentDonut, TimelineChart, WordBars } from './Charts'
import WordCloud from './WordCloud'
import { SENT_COLOR, compact, full, pct } from '../lib/format'

function Kpi({ icon: Icon, label, value, hint, delay = 0 }) {
  return (
    <div className="card rise p-5" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center justify-between text-muted"><span className="text-xs font-medium">{label}</span><Icon size={15} /></div>
      <p className="mt-3 text-3xl font-semibold tabular-nums tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </div>
  )
}

export default function Overview({ a }) {
  const { kpis, nlp, summary } = a
  const er = kpis.engagement_rate
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi icon={Eye} label="Views" value={compact(kpis.views)} hint={kpis.views != null ? `${full(kpis.views)} total` : 'Not available for this Reel'} />
        <Kpi icon={Heart} label="Likes" value={compact(kpis.likes)} hint={kpis.likes != null ? `${full(kpis.likes)} total` : 'Not available for this Reel'} delay={40} />
        <Kpi icon={MessageCircle} label="Comments" value={compact(kpis.comments)} hint={`${summary.fetched} fetched · ${summary.analyzed} analyzed`} delay={80} />
        <Kpi icon={Percent} label="Engagement rate" value={er != null ? `${er}%` : '—'} hint={er != null ? '(likes + comments) ÷ views' : kpis.engagement_rate_note} delay={120} />
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3" title="Sentiment distribution" subtitle="Spam and duplicate comments excluded"><SentimentDonut sentiment={a.sentiment} /></Card>
        <Card className="lg:col-span-2" title="Most liked comment" action={<Trophy size={15} className="text-muted" />}>
          {kpis.most_liked_comment ? (
            <div>
              <p className="text-[15px] leading-relaxed">“{kpis.most_liked_comment.text}”</p>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted">
                <span>@{kpis.most_liked_comment.username}</span><span>·</span>
                <span className="flex items-center gap-1"><Heart size={12} />{full(kpis.most_liked_comment.likes)}</span>
                <SentimentBadge value={kpis.most_liked_comment.sentiment} />
              </div>
            </div>
          ) : <EmptyState title="Comment likes unavailable" />}
          <div className="mt-5 grid grid-cols-3 gap-2 text-center text-xs">
            <Stat label="Questions" value={summary.questions} icon={HelpCircle} />
            <Stat label="Spam" value={summary.spam} icon={ShieldAlert} />
            <Stat label="Duplicates" value={summary.duplicates} icon={Copy} />
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Emotion distribution" subtitle="Per analyzed comment"><EmotionChart emotions={a.emotions} /></Card>
        <Card title="Engagement" subtitle="Reel-level ratios and comment likes"><EngagementChart engagement={a.engagement} kpis={kpis} /></Card>
      </div>

      <Card title="Comment timeline" subtitle={`Comments per ${a.timeline.granularity}, stacked by sentiment`}><TimelineChart timeline={a.timeline} /></Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3" title="Aspect-based sentiment" subtitle="What people feel about each part of the Reel"><AspectChart aspects={nlp.aspects} /></Card>
        <Card className="lg:col-span-2" title="Appreciated vs. criticized">
          <AspectList title="Most appreciated" icon={ThumbsUp} rows={nlp.appreciated_aspects} k="positive" tone="pos" />
          <div className="my-4 border-t border-border" />
          <AspectList title="Most criticized" icon={ThumbsDown} rows={nlp.criticized_aspects} k="negative" tone="neg" />
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Top keywords" subtitle="Colour = dominant sentiment of comments using the word">
          <WordBars rows={nlp.keywords} labelKey="word" valueKey="comments" colorFn={(d) => SENT_COLOR[d.sentiment]} />
        </Card>
        <Card title="Word cloud"><WordCloud words={nlp.word_cloud} /></Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Hashtags" subtitle={nlp.caption_hashtags.length ? `Caption: ${nlp.caption_hashtags.join(' ')}` : 'Hashtags used in comments'} action={<Hash size={15} className="text-muted" />}>
          {nlp.hashtags.length ? <WordBars rows={nlp.hashtags} labelKey="tag" /> : <EmptyState icon={Hash} title="No hashtags in comments" />}
        </Card>
        <Card title="Languages" subtitle="Detected per comment (script + Romanised-Hindi detection)"><LanguageBars languages={a.languages} /></Card>
      </div>

      <Card title="Topic analysis" subtitle="NMF topic model over comment text" action={<Layers3 size={15} className="text-muted" />}>
        {nlp.topics.available ? (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {nlp.topics.topics.map((t) => (
              <div key={t.id} className="rounded-xl border border-border bg-card2/50 p-4">
                <div className="flex items-center justify-between"><p className="text-sm font-semibold capitalize">{t.label}</p><Badge tone="accent">{t.share}%</Badge></div>
                <div className="mt-2 flex flex-wrap gap-1">{t.terms.map((x) => <span key={x} className="rounded-md bg-card px-1.5 py-0.5 text-[11px] text-muted">{x}</span>)}</div>
                <p className="mt-3 line-clamp-2 text-xs italic text-muted">“{t.example}”</p>
                <p className="mt-3 text-[11px] text-muted"><span style={{ color: SENT_COLOR.positive }}>+{t.positive}</span> · <span style={{ color: SENT_COLOR.negative }}>−{t.negative}</span> · {t.neutral} neutral · {t.comment_count} comments</p>
              </div>
            ))}
          </div>
        ) : <EmptyState icon={Layers3} title="Topics unavailable">{nlp.topics.reason}</EmptyState>}
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Frequently asked questions" action={<HelpCircle size={15} className="text-muted" />}>
          {nlp.faqs.length ? <ul className="space-y-3">{nlp.faqs.slice(0, 6).map((q) => (
            <li key={q.question} className="flex items-start justify-between gap-3 text-sm"><span className="leading-snug">{q.question}</span><Badge tone="accent">×{q.count}</Badge></li>))}</ul>
            : <EmptyState icon={HelpCircle} title="No questions found" />}
        </Card>
        <Card title="Similar comment groups" subtitle="Near-identical wording">
          {nlp.similar_groups.length ? <ul className="space-y-3">{nlp.similar_groups.slice(0, 5).map((g, i) => (
            <li key={i} className="text-sm"><p className="line-clamp-2 leading-snug">“{g.representative}”</p><p className="mt-1 text-xs text-muted">{g.size} similar comments · mostly {g.dominant_sentiment}</p></li>))}</ul>
            : <EmptyState icon={Copy} title="No similar groups" />}
        </Card>
        <Card title="Spam & duplicates" action={<ShieldAlert size={15} className="text-muted" />}>
          {nlp.spam.length || nlp.duplicates.length ? (
            <div className="space-y-3 text-sm">
              {nlp.spam.slice(0, 3).map((s) => <div key={s.id}><p className="line-clamp-1">“{s.text}”</p><p className="text-xs text-muted">Spam · {s.reasons.join(', ')}</p></div>)}
              {nlp.duplicates.slice(0, 3).map((d, i) => <div key={i}><p className="line-clamp-1">“{d.text}”</p><p className="text-xs text-muted">Posted {d.count}× (duplicate)</p></div>)}
            </div>
          ) : <EmptyState icon={ShieldAlert} title="Clean comment section" />}
        </Card>
      </div>
    </div>
  )
}

const Stat = ({ label, value, icon: Icon }) => (
  <div className="rounded-lg bg-card2 px-2 py-2.5"><p className="flex items-center justify-center gap-1 text-base font-semibold tabular-nums"><Icon size={13} className="text-muted" />{value}</p><p className="text-[11px] text-muted">{label}</p></div>
)

function AspectList({ title, icon: Icon, rows, k, tone }) {
  return (
    <div>
      <p className="mb-2 flex items-center gap-2 text-xs font-medium text-muted"><Icon size={13} />{title}</p>
      {rows.length ? <ul className="space-y-2">{rows.slice(0, 4).map((r) => (
        <li key={r.aspect} className="flex items-center justify-between text-sm"><span>{r.aspect}</span><Badge tone={tone}>{r[k]} of {r.mentions} mentions</Badge></li>))}</ul>
        : <p className="text-xs text-muted">None detected.</p>}
    </div>
  )
}

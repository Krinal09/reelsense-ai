import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartTip, EmptyState } from './ui'
import { EMO_COLOR, EMO_EMOJI, SENT_COLOR, cap, full, pct } from '../lib/format'
import { BarChart3 } from 'lucide-react'

const tick = { fill: 'var(--muted)', fontSize: 11 }
const axisLine = { stroke: 'var(--border)' }

export function SentimentDonut({ sentiment }) {
  const data = ['positive', 'negative', 'neutral'].map((k) => ({ name: cap(k), key: k, value: sentiment.counts[k] }))
  const total = data.reduce((a, b) => a + b.value, 0)
  if (!total) return <EmptyState icon={BarChart3} title="No analyzed comments" />
  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:gap-8">
      <div className="relative size-48 shrink-0" role="img" aria-label={`Sentiment: ${data.map((d) => `${d.name} ${sentiment.percentages[d.key]}%`).join(', ')}`}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius={62} outerRadius={86} paddingAngle={2} stroke="none" startAngle={90} endAngle={-270}>
              {data.map((d) => <Cell key={d.key} fill={SENT_COLOR[d.key]} />)}
            </Pie>
            <Tooltip content={<ChartTip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div><p className="text-2xl font-semibold tabular-nums">{total}</p><p className="text-[11px] text-muted">comments</p></div>
        </div>
      </div>
      <ul className="w-full space-y-3">
        {data.map((d) => (
          <li key={d.key}>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2"><span className="size-2.5 rounded-full" style={{ background: SENT_COLOR[d.key] }} />{d.name}</span>
              <span className="tabular-nums text-muted"><b className="text-fg">{pct(sentiment.percentages[d.key])}</b> · {d.value}</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-card2"><div className="h-full rounded-full" style={{ width: `${sentiment.percentages[d.key] || 0}%`, background: SENT_COLOR[d.key] }} /></div>
          </li>
        ))}
        {sentiment.average_confidence != null && <li className="pt-1 text-xs text-muted">Average model confidence: {pct(sentiment.average_confidence * 100, 0)}</li>}
      </ul>
    </div>
  )
}

export function EmotionChart({ emotions }) {
  const data = emotions.map((e) => ({ ...e, label: `${EMO_EMOJI[e.emotion]} ${e.emotion}` }))
  return (
    <div className="h-64" role="img" aria-label="Emotion distribution">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={tick} axisLine={axisLine} tickLine={false} allowDecimals={false} />
          <YAxis type="category" dataKey="label" tick={tick} axisLine={false} tickLine={false} width={100} />
          <Tooltip cursor={{ fill: 'var(--card-2)' }} content={<ChartTip fmt={(v) => v} />} />
          <Bar dataKey="count" name="Comments" radius={[0, 6, 6, 0]} barSize={18}>
            {data.map((d) => <Cell key={d.emotion} fill={EMO_COLOR[d.emotion]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function EngagementChart({ engagement, kpis }) {
  const bars = engagement.likes_by_sentiment.map((d) => ({ name: cap(d.sentiment), key: d.sentiment, likes: d.likes }))
  const r = engagement.ratios
  return (
    <div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <Mini label="Like rate" value={r.like_rate != null ? `${r.like_rate}%` : '—'} />
        <Mini label="Comment rate" value={r.comment_rate != null ? `${r.comment_rate}%` : '—'} />
        <Mini label="Avg comment likes" value={kpis.avg_comment_likes ?? '—'} />
      </div>
      <p className="mb-1 mt-5 text-xs text-muted">Likes received by comments, grouped by their sentiment</p>
      <div className="h-44" role="img" aria-label="Comment likes by sentiment">
        <ResponsiveContainer>
          <BarChart data={bars} margin={{ left: -10, right: 8, top: 8 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis dataKey="name" tick={tick} axisLine={axisLine} tickLine={false} />
            <YAxis tick={tick} axisLine={false} tickLine={false} />
            <Tooltip cursor={{ fill: 'var(--card-2)' }} content={<ChartTip />} />
            <Bar dataKey="likes" name="Comment likes" radius={[6, 6, 0, 0]} barSize={42}>
              {bars.map((d) => <Cell key={d.key} fill={SENT_COLOR[d.key]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
const Mini = ({ label, value }) => <div className="rounded-lg bg-card2 px-2 py-2.5"><p className="text-base font-semibold tabular-nums">{value}</p><p className="text-[11px] text-muted">{label}</p></div>

export function TimelineChart({ timeline }) {
  if (!timeline.points.length) return <EmptyState icon={BarChart3} title="No timestamps available" />
  return (
    <div className="h-64" role="img" aria-label={`Comments per ${timeline.granularity}`}>
      <ResponsiveContainer>
        <AreaChart data={timeline.points} margin={{ left: -14, right: 8, top: 8 }}>
          <defs>{['positive', 'negative', 'neutral'].map((k) => (
            <linearGradient key={k} id={`g-${k}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={SENT_COLOR[k]} stopOpacity={0.45} /><stop offset="100%" stopColor={SENT_COLOR[k]} stopOpacity={0.03} /></linearGradient>))}
          </defs>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="date" tick={tick} axisLine={axisLine} tickLine={false} tickFormatter={(d) => d.slice(5, timeline.granularity === 'hour' ? 13 : 10)} minTickGap={24} />
          <YAxis tick={tick} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip content={<ChartTip />} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, color: 'var(--muted)' }} />
          {['positive', 'neutral', 'negative'].map((k) => <Area key={k} type="monotone" dataKey={k} name={cap(k)} stackId="1" stroke={SENT_COLOR[k]} fill={`url(#g-${k})`} strokeWidth={1.8} />)}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function WordBars({ rows, labelKey, valueKey = 'count', colorFn, height }) {
  if (!rows.length) return <EmptyState icon={BarChart3} title="Nothing to show yet" />
  const data = rows.slice(0, 12)
  return (
    <div style={{ height: height || Math.max(180, data.length * 26 + 20) }} role="img" aria-label="Bar chart">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 4, right: 24 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={tick} axisLine={axisLine} tickLine={false} allowDecimals={false} />
          <YAxis type="category" dataKey={labelKey} tick={tick} axisLine={false} tickLine={false} width={92} interval={0} />
          <Tooltip cursor={{ fill: 'var(--card-2)' }} content={<ChartTip />} />
          <Bar dataKey={valueKey} name="Count" radius={[0, 6, 6, 0]} barSize={14}>
            {data.map((d, i) => <Cell key={i} fill={colorFn ? colorFn(d) : 'var(--accent)'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AspectChart({ aspects }) {
  if (!aspects.length) return <EmptyState icon={BarChart3} title="No aspects detected" />
  return (
    <div style={{ height: aspects.length * 40 + 50 }} role="img" aria-label="Aspect-based sentiment">
      <ResponsiveContainer>
        <BarChart data={aspects} layout="vertical" margin={{ left: 4, right: 20 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={tick} axisLine={axisLine} tickLine={false} allowDecimals={false} />
          <YAxis type="category" dataKey="aspect" tick={tick} axisLine={false} tickLine={false} width={96} />
          <Tooltip cursor={{ fill: 'var(--card-2)' }} content={<ChartTip />} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, color: 'var(--muted)' }} />
          <Bar dataKey="positive" name="Positive" stackId="a" fill={SENT_COLOR.positive} barSize={16} />
          <Bar dataKey="neutral" name="Neutral" stackId="a" fill={SENT_COLOR.neutral} />
          <Bar dataKey="negative" name="Negative" stackId="a" fill={SENT_COLOR.negative} radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function LanguageBars({ languages }) {
  return <WordBars rows={languages} labelKey="language" valueKey="count" height={Math.max(150, languages.length * 30 + 20)} />
}
export { full }

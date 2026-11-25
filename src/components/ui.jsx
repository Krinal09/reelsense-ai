import { SENT_COLOR, cap } from '../lib/format'

export const Card = ({ title, subtitle, action, children, className = '' }) => (
  <section className={`card p-5 ${className}`}>
    {(title || action) && (
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          {title && <h3 className="text-sm font-semibold tracking-tight">{title}</h3>}
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
        {action}
      </header>
    )}
    {children}
  </section>
)

export const Skeleton = ({ className = '' }) => <div className={`skeleton ${className}`} />

export const Button = ({ variant = 'primary', className = '', icon: Icon, children, ...p }) => {
  const base = 'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition active:scale-[.98] disabled:opacity-50 disabled:pointer-events-none'
  const v = {
    primary: 'bg-accent text-white shadow-sm hover:brightness-110',
    secondary: 'border border-border bg-card text-fg hover:bg-card2',
    ghost: 'text-muted hover:bg-card2 hover:text-fg',
  }[variant]
  return <button className={`${base} ${v} ${className}`} {...p}>{Icon && <Icon size={16} />}{children}</button>
}

export const Badge = ({ tone = 'neutral', children, className = '' }) => {
  const t = {
    neutral: 'bg-card2 text-muted border-border',
    pos: 'bg-pos/10 text-pos border-pos/25', neg: 'bg-neg/10 text-neg border-neg/25',
    accent: 'bg-accent/10 text-accent border-accent/25', warn: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25',
  }[tone]
  return <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${t} ${className}`}>{children}</span>
}

export const SentimentBadge = ({ value }) => (
  <Badge tone={{ positive: 'pos', negative: 'neg', neutral: 'neutral' }[value]}>
    <span className="size-1.5 rounded-full" style={{ background: SENT_COLOR[value] }} />{cap(value)}
  </Badge>
)

export const EmptyState = ({ icon: Icon, title, children }) => (
  <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
    {Icon && <div className="rounded-full bg-card2 p-3 text-muted"><Icon size={20} /></div>}
    <p className="text-sm font-medium">{title}</p>
    {children && <p className="max-w-sm text-xs text-muted">{children}</p>}
  </div>
)

export const Banner = ({ tone = 'info', icon: Icon, children, action }) => {
  const t = { info: 'border-accent/30 bg-accent/5', warn: 'border-amber-500/30 bg-amber-500/5', danger: 'border-neg/30 bg-neg/5' }[tone]
  return (
    <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${t}`}>
      {Icon && <Icon size={16} className="mt-0.5 shrink-0 text-muted" />}
      <div className="flex-1 leading-relaxed">{children}</div>
      {action}
    </div>
  )
}

export const ChartTip = ({ active, payload, label, fmt }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card px-3 py-2 text-xs shadow-lg">
      {label != null && <p className="mb-1 font-medium">{label}</p>}
      {payload.map((p) => (
        <p key={p.dataKey + p.name} className="flex items-center gap-2 text-muted">
          <span className="size-2 rounded-full" style={{ background: p.color || p.payload?.fill }} />
          {p.name}: <b className="text-fg">{fmt ? fmt(p.value) : p.value}</b>
        </p>
      ))}
    </div>
  )
}

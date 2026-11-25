export const nf = new Intl.NumberFormat('en-US')
export const compact = (n) => (n == null ? '—' : new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n))
export const full = (n) => (n == null ? '—' : nf.format(n))
export const pct = (n, d = 1) => (n == null ? '—' : `${Number(n).toFixed(d).replace(/\.0+$/, '')}%`)
export const dateFmt = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? '—' : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
export const dateTimeFmt = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? '—' : d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export const SENT_COLOR = { positive: 'var(--pos)', negative: 'var(--neg)', neutral: 'var(--neu)' }
export const EMO_COLOR = { Happy: '#f5b324', Excited: '#ec4899', Angry: '#ef4444', Sad: '#3b82f6', Frustrated: '#f97316', Neutral: '#94a3b8' }
export const EMO_EMOJI = { Happy: '😊', Excited: '🤩', Angry: '😠', Sad: '😢', Frustrated: '😤', Neutral: '😐' }
export const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s)

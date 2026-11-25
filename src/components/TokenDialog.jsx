import { useState } from 'react'
import { ExternalLink, KeyRound, Loader2, X, CheckCircle2 } from 'lucide-react'
import { Button } from './ui'
import { getToken, setToken, verifyToken } from '../lib/api'
import { useToast } from './Toast'

export default function TokenDialog({ open, onClose, onSaved }) {
  const toast = useToast()
  const [val, setVal] = useState(getToken())
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  if (!open) return null

  const save = async () => {
    const t = val.trim()
    setErr('')
    setBusy(true)
    try {
      if (!t) { setToken(''); onSaved?.(''); onClose(); return }
      const r = await verifyToken(t)
      setToken(t); toast(`Connected to Apify${r.username ? ` as ${r.username}` : ''}.`, 'success'); onSaved?.(t); onClose()
    } catch (e) { setErr(e.message + (e.details ? ` ${e.details}` : '')) }
    finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Connect data provider" onClick={onClose}>
      <div className="card rise w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div className="grid size-10 place-items-center rounded-xl bg-accentsoft text-accent"><KeyRound size={18} /></div>
          <button onClick={onClose} className="rounded p-1 text-muted hover:text-fg" aria-label="Close"><X size={16} /></button>
        </div>
        <h2 className="mt-4 text-lg font-semibold tracking-tight">One-time setup</h2>
        <p className="mt-1.5 text-sm leading-relaxed text-muted">Instagram only shares comments through a data provider. Paste your free Apify token once — it stays in this browser and is never stored on the server.</p>
        <ol className="mt-4 space-y-1.5 text-sm text-muted">
          <li>1. <a className="inline-flex items-center gap-1 text-accent hover:underline" href="https://console.apify.com/sign-up" target="_blank" rel="noreferrer">Create a free Apify account <ExternalLink size={11} /></a></li>
          <li>2. <a className="inline-flex items-center gap-1 text-accent hover:underline" href="https://console.apify.com/settings/integrations" target="_blank" rel="noreferrer">Open Settings → API & Integrations <ExternalLink size={11} /></a></li>
          <li>3. Copy the <b className="text-fg">Personal API token</b> and paste it below.</li>
        </ol>
        <input value={val} onChange={(e) => setVal(e.target.value)} type="password" autoComplete="off" spellCheck={false} placeholder="apify_api_…" aria-label="Apify token"
          onKeyDown={(e) => e.key === 'Enter' && save()}
          className="mt-4 h-11 w-full rounded-lg border border-border bg-bg px-3 text-sm outline-none focus:border-accent" />
        {err && <p className="mt-2 text-xs text-neg">{err}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={save} disabled={busy} icon={busy ? Loader2 : CheckCircle2}>{busy ? 'Checking…' : 'Save & connect'}</Button>
        </div>
      </div>
    </div>
  )
}

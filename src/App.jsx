import { useCallback, useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import Landing from './components/Landing'
import ProgressScreen from './components/ProgressScreen'
import ErrorPanel from './components/ErrorPanel'
import Dashboard from './components/Dashboard'
import { useToast } from './components/Toast'
import TokenDialog from './components/TokenDialog'
import { analyze, getToken, health } from './lib/api'

export default function App() {
  const toast = useToast()
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  const [view, setView] = useState('landing') // landing | loading | error | dashboard
  const [progress, setProgress] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)
  const [lastUrl, setLastUrl] = useState('')
  const [demoRun, setDemoRun] = useState(false)
  const ctl = useRef(null)
  const [dlg, setDlg] = useState(false)
  const [hasToken, setHasToken] = useState(!!getToken())
  const pendingUrl = useRef('')

  useEffect(() => { health().then(setStatus) }, [])
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('reelsense-theme', dark ? 'dark' : 'light') } catch { /* ignore */ }
  }, [dark])

  const run = useCallback(async (mode, url = '') => {
    ctl.current?.abort()
    ctl.current = new AbortController()
    setDemoRun(mode === 'demo'); setLastUrl(url); setProgress({ percent: 2, message: 'Starting…' }); setError(null); setView('loading')
    try {
      const res = await analyze({ mode, url }, setProgress, ctl.current.signal)
      setAnalysis(res); setView('dashboard')
      res.warnings.filter((w) => !w.startsWith('Demo mode')).slice(0, 1).forEach((w) => toast(w, 'info', 7000))
      toast('Analysis complete.', 'success')
      window.scrollTo({ top: 0 })
    } catch (e) {
      if (e.name === 'AbortError') return
      setError({ code: e.code || 'error', message: e.message || 'Something went wrong.', details: e.details, canUseDemo: !!e.canUseDemo })
      setView('error')
      toast(e.message || 'Analysis failed.', 'error')
    }
  }, [toast])

  const onAnalyze = (url) => {
    if (!url) return toast('Paste an Instagram Reel URL first.', 'info')
    if (!getToken() && !status?.instagram_configured) { pendingUrl.current = url; setDlg(true); return }
    run('live', url)
  }
  const reset = () => { ctl.current?.abort(); setView('landing'); setError(null) }

  return (
    <div className="min-h-dvh">
      <Header dark={dark} onToggle={() => setDark((d) => !d)} onReset={reset} showReset={view !== 'landing'} onKey={() => setDlg(true)} connected={hasToken || status?.instagram_configured} isDemo={view === 'dashboard' && analysis?.is_demo} />
      <main>
        {view === 'landing' && <Landing onAnalyze={onAnalyze} status={status} initialUrl={lastUrl} />}
        {view === 'loading' && <ProgressScreen progress={progress} isDemo={demoRun} />}
        {view === 'error' && error && <ErrorPanel error={error} onRetry={reset} onKey={() => setDlg(true)} />}
        {view === 'dashboard' && analysis && <Dashboard analysis={analysis} />}
      </main>
      <TokenDialog open={dlg} onClose={() => setDlg(false)} onSaved={(t) => { setHasToken(!!t); if (t && pendingUrl.current) { const u = pendingUrl.current; pendingUrl.current = ''; run('live', u) } }} />
    </div>
  )
}

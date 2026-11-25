import { Moon, Sun, Sparkles, RotateCcw, KeyRound } from 'lucide-react'
import { Button } from './ui'

export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-pink-500 text-white shadow-sm"><Sparkles size={16} /></div>
      <span className="text-[15px] font-semibold tracking-tight">ReelSense <span className="text-accent">AI</span></span>
    </div>
  )
}

export default function Header({ dark, onToggle, onReset, showReset, isDemo, onKey, connected }) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <button onClick={onReset} className="rounded-lg" aria-label="ReelSense AI home"><Logo /></button>
        <div className="flex items-center gap-2">
          {isDemo && <span className="hidden rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-600 sm:inline dark:text-amber-400">Demo · sample data</span>}
          {showReset && <Button variant="secondary" icon={RotateCcw} onClick={onReset} className="!py-1.5">New analysis</Button>}
          <button onClick={onKey} className="relative grid size-9 place-items-center rounded-lg border border-border bg-card text-muted hover:text-fg" aria-label="Data provider token" title="Data provider token">
            <KeyRound size={16} />{connected && <span className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-pos" />}
          </button>
          <button onClick={onToggle} className="grid size-9 place-items-center rounded-lg border border-border bg-card text-muted hover:text-fg" aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </header>
  )
}

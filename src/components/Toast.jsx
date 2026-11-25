import { createContext, useCallback, useContext, useState } from 'react'
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react'

const Ctx = createContext(() => {})
export const useToast = () => useContext(Ctx)

const ICON = { success: CheckCircle2, error: AlertTriangle, info: Info }
const TONE = { success: 'text-pos', error: 'text-neg', info: 'text-accent' }

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const dismiss = useCallback((id) => setItems((xs) => xs.filter((x) => x.id !== id)), [])
  const push = useCallback((message, type = 'info', ms = 4500) => {
    const id = Math.random().toString(36).slice(2)
    setItems((xs) => [...xs.slice(-3), { id, message, type }])
    setTimeout(() => dismiss(id), ms)
  }, [dismiss])
  return (
    <Ctx.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-[min(92vw,360px)] flex-col gap-2" role="status" aria-live="polite">
        {items.map((t) => {
          const Icon = ICON[t.type]
          return (
            <div key={t.id} className="card toast-in flex items-start gap-3 p-3 pr-2 text-sm shadow-lg">
              <Icon size={18} className={`mt-0.5 shrink-0 ${TONE[t.type]}`} />
              <p className="flex-1 leading-snug">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="rounded p-1 text-muted hover:text-fg" aria-label="Dismiss"><X size={14} /></button>
            </div>
          )
        })}
      </div>
    </Ctx.Provider>
  )
}

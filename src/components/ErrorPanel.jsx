import { AlertTriangle, RotateCcw, KeyRound, Clock, WifiOff, Link2Off } from 'lucide-react'
import { Button } from './ui'

const ICONS = { credentials_missing: KeyRound, rate_limited: Clock, processing_timeout: Clock, network: WifiOff, invalid_url: Link2Off, unsupported_reel: Link2Off }
const TITLES = {
  invalid_url: 'That link doesn’t look right', unsupported_reel: 'This Reel can’t be analyzed', credentials_missing: 'Data provider isn’t configured',
  provider_unavailable: 'Instagram data is unavailable', rate_limited: 'Rate limit reached', no_comments: 'No comments to analyze',
  processing_timeout: 'Processing took too long', network: 'Can’t reach the server',
}

export default function ErrorPanel({ error, onRetry, onKey }) {
  const Icon = ICONS[error.code] || AlertTriangle
  return (
    <div className="mx-auto max-w-xl px-4 py-16 sm:px-6">
      <div className="card rise p-7 text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-neg/10 text-neg"><Icon size={22} /></div>
        <h2 className="mt-4 text-lg font-semibold tracking-tight">{TITLES[error.code] || 'Something went wrong'}</h2>
        <p className="mt-2 text-sm text-muted">{error.message}</p>
        {error.details && <p className="mt-2 rounded-lg bg-card2 px-3 py-2 text-left text-xs leading-relaxed text-muted">{error.details}</p>}
        <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row">
          {(error.code === 'credentials_missing') && <Button icon={KeyRound} onClick={onKey}>Add Apify token</Button>}
          <Button variant={error.code === 'credentials_missing' ? 'secondary' : 'primary'} icon={RotateCcw} onClick={onRetry}>Try another Reel</Button>
        </div>
      </div>
    </div>
  )
}

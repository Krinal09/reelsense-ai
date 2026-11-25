import { EmptyState } from './ui'
import { Cloud } from 'lucide-react'
import { SENT_COLOR } from '../lib/format'

/** Lightweight word cloud: font size ∝ frequency, colour = dominant sentiment of the comments containing the word. */
export default function WordCloud({ words }) {
  if (!words?.length) return <EmptyState icon={Cloud} title="Not enough text for a word cloud" />
  const max = Math.max(...words.map((w) => w.count))
  const min = Math.min(...words.map((w) => w.count))
  const size = (c) => 13 + (max === min ? 0.5 : (c - min) / (max - min)) * 27
  const shuffled = [...words].sort((a, b) => (a.word.charCodeAt(0) * 7 + a.count) % 11 - (b.word.charCodeAt(0) * 7 + b.count) % 11)
  return (
    <div className="flex min-h-56 flex-wrap items-center justify-center gap-x-4 gap-y-1.5 px-2 py-3" role="img" aria-label={`Word cloud of ${words.length} words`}>
      {shuffled.map((w) => (
        <span key={w.word} title={`${w.word}: ${w.count} · +${w.positive} −${w.negative} ~${w.neutral}`}
          className="cursor-default leading-tight font-semibold transition-transform hover:scale-110"
          style={{ fontSize: size(w.count), color: SENT_COLOR[w.sentiment], opacity: 0.62 + 0.38 * ((w.count - min) / Math.max(1, max - min)) }}>
          {w.word}
        </span>
      ))}
    </div>
  )
}

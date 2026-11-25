import { useState } from 'react'
import { FileSpreadsheet, FileText, FileType2, Download, Loader2 } from 'lucide-react'
import { Card } from './ui'
import { downloadExport } from '../lib/api'
import { useToast } from './Toast'

const OPTS = [
  { fmt: 'csv', icon: FileText, title: 'CSV', text: 'All comments with sentiment, emotion, confidence, language, aspects and flags. Opens in Excel with Hindi/Gujarati intact.' },
  { fmt: 'excel', icon: FileSpreadsheet, title: 'Excel workbook', text: 'Summary, comments, aspects, keywords, hashtags, topics, FAQs and timeline on separate sheets.' },
  { fmt: 'pdf', icon: FileType2, title: 'PDF report', text: 'KPIs, executive summary, sentiment chart, aspects, feedback, FAQs and recommendations.' },
]

export default function ExportPanel({ analysis }) {
  const [busy, setBusy] = useState(null)
  const toast = useToast()
  const go = async (fmt) => {
    setBusy(fmt)
    try { await downloadExport(fmt, analysis); toast(`${fmt.toUpperCase()} report downloaded.`, 'success') }
    catch (e) { toast(e.message || 'Export failed.', 'error') }
    finally { setBusy(null) }
  }
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {OPTS.map((o) => (
          <Card key={o.fmt} className="flex flex-col">
            <div className="mb-3 grid size-10 place-items-center rounded-xl bg-accentsoft text-accent"><o.icon size={20} /></div>
            <h3 className="text-sm font-semibold">{o.title}</h3>
            <p className="mt-1.5 flex-1 text-sm leading-relaxed text-muted">{o.text}</p>
            <button onClick={() => go(o.fmt)} disabled={!!busy}
              className="mt-5 inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card2 px-4 py-2.5 text-sm font-medium transition hover:border-accent/50 hover:text-accent disabled:opacity-60">
              {busy === o.fmt ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}{busy === o.fmt ? 'Preparing…' : `Download ${o.title}`}
            </button>
          </Card>
        ))}
      </div>
      <p className="text-xs text-muted">{analysis.is_demo ? 'Demo exports are labelled as sample data. ' : ''}PDF reports use standard Latin fonts: comments in Hindi or Gujarati are marked as non-Latin there and appear in full in the CSV and Excel files.</p>
    </div>
  )
}

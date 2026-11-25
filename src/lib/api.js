import axios from 'axios'

const TOKEN_KEY = 'reelsense-apify-token'
export const getToken = () => { try { return localStorage.getItem(TOKEN_KEY) || '' } catch { return '' } }
export const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ } }
const authHeaders = () => (getToken() ? { 'X-Apify-Token': getToken() } : {})

export async function verifyToken(token) {
  try {
    return (await axios.post('/api/apify/verify', null, { headers: { 'X-Apify-Token': token }, timeout: 15000 })).data
  } catch (e) { throw toApiError(e) }
}

export class ApiError extends Error {
  constructor(error) {
    super(error?.message || 'Request failed')
    this.code = error?.code || 'error'
    this.details = error?.details || null
    this.canUseDemo = !!error?.can_use_demo
  }
}

const toApiError = (e) => {
  if (e instanceof ApiError) return e
  const body = e?.response?.data
  if (body?.error) return new ApiError(body.error)
  if (body?.detail) {
    const d = Array.isArray(body.detail) ? body.detail.map((x) => x.msg).join('; ') : String(body.detail)
    return new ApiError({ code: 'invalid_request', message: d })
  }
  if (e?.code === 'ERR_NETWORK' || !e?.response)
    return new ApiError({ code: 'network', message: 'Could not reach the ReelSense API.', details: 'Is the backend running? (npm run dev:api)', can_use_demo: false })
  return new ApiError({ code: 'error', message: e?.message || 'Request failed', can_use_demo: true })
}

export async function health() {
  try { return (await axios.get('/api/health', { timeout: 6000 })).data } catch { return null }
}

/** POST /api/analyze with NDJSON streaming so the UI can show real extraction progress. */
export async function analyze({ mode, url }, onProgress, signal) {
  let res
  try {
    res = await fetch('/api/analyze', {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ mode, url: url || null, stream: true }),
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw toApiError({ code: 'ERR_NETWORK' })
  }
  if (!res.ok || !res.body) {
    let body = null
    try { body = await res.json() } catch { /* ignore */ }
    if (body?.error) throw new ApiError(body.error)
    if (body?.detail) throw new ApiError({ code: 'invalid_request', message: Array.isArray(body.detail) ? body.detail.map((x) => x.msg).join('; ') : String(body.detail) })
    throw new ApiError({ code: 'error', message: `The server responded with ${res.status}.`, can_use_demo: true })
  }
  const reader = res.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  let result = null
  const handle = (line) => {
    if (!line.trim()) return
    const ev = JSON.parse(line)
    if (ev.type === 'progress') onProgress?.(ev)
    else if (ev.type === 'result') result = ev.analysis
    else if (ev.type === 'error') throw new ApiError(ev.error)
  }
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop()
    lines.forEach(handle)
  }
  handle(buf)
  if (!result) throw new ApiError({ code: 'processing_timeout', message: 'The analysis was interrupted before it finished.', details: 'The request may have exceeded the serverless time limit. Lower MAX_COMMENTS.', can_use_demo: true })
  return result
}

const EXT = { csv: 'csv', excel: 'xlsx', pdf: 'pdf' }

/** Stateless export: posts the analysis we already hold (works without a server-side store). */
export async function downloadExport(fmt, analysis) {
  try {
    const res = await axios.post(`/api/export/${fmt}`, analysis, { responseType: 'blob', timeout: 60000 })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `reelsense-${analysis.is_demo ? 'demo-' : ''}${analysis.id}.${EXT[fmt]}`
    document.body.appendChild(a); a.click(); a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 2000)
  } catch (e) {
    if (e?.response?.data instanceof Blob) {
      try { throw new ApiError(JSON.parse(await e.response.data.text()).error) } catch (inner) { if (inner instanceof ApiError) throw inner }
    }
    throw toApiError(e)
  }
}

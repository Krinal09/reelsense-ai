# ReelSense AI – Instagram Reel Analytics POC

Paste any public Instagram Reel URL → collect accessible metadata + comments → multilingual AI sentiment, emotion, aspect, topic and FAQ analysis → interactive dashboard → CSV / Excel / PDF export.

**Stack:** React + Vite + Tailwind v4 + Recharts + Lucide + Axios · FastAPI (Vercel Python function) · built-in NumPy-only sentiment model (no scikit-learn).

## Project structure
```
api/index.py                 FastAPI app = the single Vercel function (all /api/* routes)
backend/reelsense/
  providers/                 base.py (abstraction) · graph_api.py (official Instagram Graph API) · mock.py (test fixture only), apify.py (live, any public Reel)
  nlp/                       sentiment.py (built-in model) · aspects.py · analytics.py · text.py · seed_corpus.py
  pipeline.py                fetch → clean → classify → analyse → insights (streams progress)
  engagement.py insights.py exports.py store.py errors.py config.py utils.py
src/                         React app (components/, lib/api.js, App.jsx)
tests/test_backend.py        API/NLP tests
vercel.json requirements.txt package.json .env.example
```

## Quick start (easiest)
1. Install Python 3.10+ and Node.js 18+.
2. Double-click `start.bat` (Windows) or run `./start.sh` (Mac/Linux) — or `python run.py`. It installs everything, builds the UI and opens http://localhost:8000.
3. Paste a Reel link. The first time, a dialog asks for a free Apify token (steps shown in the dialog); it's saved in your browser. No environment variables needed.

## Local development
```bash
npm install
pip install -r requirements-local.txt
cp .env.example .env            # add APIFY_TOKEN=... (or paste it in the app)
npm run dev:api                 # FastAPI on :8000
npm run dev                     # Vite on :5173 (proxies /api → :8000)
npm run test:api                # backend tests
```
Open http://localhost:5173 and paste a Reel link.

## How live analysis works
Paste any **public** Reel URL → the server calls Apify's Instagram Reel + Comment actors in parallel (server-side `APIFY_TOKEN`; users log in to nothing) → AI pipeline → dashboard. Private/deleted Reels can't be read and are reported as such.

## Environment variables
| Key | Needed for | Notes |
|---|---|---|
| `APIFY_TOKEN` | **Live analysis (required)** | https://console.apify.com/settings/integrations. Apify bills per result (~$0.002–0.003/comment, ~$0.003/reel); the free plan returns only ~15 comments, so use a paid plan for full comment sets. Check Instagram/Apify terms for your use. |
| `KV_REST_API_URL`, `KV_REST_API_TOKEN` | Optional | Upstash/Vercel KV so `GET /api/analysis/{id}` persists. |
| `IG_ACCESS_TOKEN`, `IG_USER_ID`, `LIVE_PROVIDER=graph` | Optional alternative | Official Graph API, only your own account's Reels. |
| `MAX_COMMENTS` (300), `TIME_BUDGET_SECONDS` (150) | Limits | |

## Deploy to Vercel
1. Push to GitHub → Import in Vercel (Vite + Python function `api/index.py`).
2. Add `APIFY_TOKEN` under Environment Variables.
3. Deploy. `vercel.json` sets `maxDuration` 300s (needs Fluid compute, default on new projects; lower to 60 if your plan rejects it).
4. Check `/api/health` (`instagram_configured: true`), then paste a Reel link.

The Python function stays well under Vercel's 500 MB limit (no pandas/nltk; node_modules and sources are excluded).

## API
`POST /api/analyze` (`{mode:"live", url, stream}`; `stream:true` → NDJSON progress events) · `GET /api/analysis/{id}` · `/comments` (page, filters, sort) · `/insights` · `/export/{csv|excel|pdf}` · `POST /api/export/{fmt}` (stateless export from a posted analysis) · `GET /api/health`.

## Design notes & honest limits
- Language detection is script-based (Gujarati/Devanagari) plus a Romanised-Hindi lexicon for Hinglish.
- Emotion: English emotion model for English text; multilingual zero-shot NLI for others. Accuracy on Hinglish/Gujarati is lower than English.
- Sentiment stats exclude spam and exact duplicates; FAQs count repeats. Insights are rule-based over computed stats and verbatim comments (no generative model, nothing invented).
- Replies are collected and counted but not sentiment-scored.
- PDF uses core Latin fonts; Hindi/Gujarati comments appear in CSV/Excel.
- I could not reach Apify or Instagram from the build sandbox: those paths are covered by mocked tests, not live calls. Apify output field names are parsed defensively; verify with a real Reel and adjust `providers/apify.py` if needed.
- Add a provider: subclass `ReelProvider` and register it in `providers/__init__.py`.

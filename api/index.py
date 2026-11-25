"""Vercel entrypoint: a single FastAPI ASGI app serving every /api/* route."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from typing import Literal, Optional  # noqa: E402

from fastapi import FastAPI, Header, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, Response, StreamingResponse  # noqa: E402
from pydantic import BaseModel, Field, model_validator  # noqa: E402

from backend.reelsense import store  # noqa: E402
from backend.reelsense.config import settings  # noqa: E402
from backend.reelsense.errors import NotFound, ReelSenseError  # noqa: E402
from backend.reelsense.exports import EXPORTERS  # noqa: E402
from backend.reelsense.pipeline import DEMO_SEED, analysis_stream, run_analysis  # noqa: E402

app = FastAPI(title="ReelSense AI", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _default(o):
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=_default)


class AnalyzeRequest(BaseModel):
    url: Optional[str] = Field(None, max_length=500)
    mode: Literal["live", "demo"] = "live"  # "demo" is for tests/dev only
    max_comments: Optional[int] = Field(None, ge=10, le=1000)
    stream: bool = False

    @model_validator(mode="after")
    def _need_url(self):
        if self.mode == "live" and not (self.url or "").strip():
            raise ValueError("url is required in live mode")
        return self


@app.exception_handler(ReelSenseError)
async def _reelsense_error(_: Request, exc: ReelSenseError):
    return JSONResponse(status_code=exc.status, content={"error": exc.to_dict()})


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": {
        "code": "internal_error", "message": "Something went wrong while analyzing this Reel.",
        "details": f"{type(exc).__name__}: {exc}", "can_use_demo": True}})


def _json(obj, status: int = 200):
    return Response(dumps(obj), status_code=status, media_type="application/json")


def _get_analysis(analysis_id: str) -> dict:
    a = store.load(analysis_id)
    if a:
        return a
    if analysis_id.startswith("demo-"):  # demo analyses are deterministic -> recompute
        try:
            seed = int(analysis_id.split("-", 1)[1])
        except ValueError:
            seed = DEMO_SEED
        return run_analysis("demo", None, seed=seed)
    raise NotFound(
        "Analysis not found.",
        details="Results are only kept if an Upstash Redis / Vercel KV store is configured (and for 24h). "
        "The /analyze response always contains the full analysis.",
    )


# ------------------------------------------------------------------ routes
@app.get("/api/health")
def health():
    return {"status": "ok", "instagram_configured": bool(settings.apify_token or (settings.ig_access_token and settings.ig_user_id)),
            "live_provider": "apify" if settings.apify_token and settings.live_provider != "graph" else ("graph" if settings.ig_access_token else None),
            "store_enabled": store.enabled(), "max_comments": settings.max_comments}


@app.post("/api/apify/verify")
def verify_token(x_apify_token: Optional[str] = Header(None)):
    import httpx
    from backend.reelsense.errors import CredentialsMissing
    tok = (x_apify_token or "").strip()
    if not tok:
        raise CredentialsMissing("Paste your Apify token first.")
    try:
        r = httpx.get("https://api.apify.com/v2/users/me", params={"token": tok}, timeout=10)
    except httpx.HTTPError:
        raise ReelSenseError("Could not reach Apify to check the token. Check your internet connection.")
    if r.status_code != 200:
        raise CredentialsMissing("Apify rejected this token.", details="Copy the Personal API token from console.apify.com → Settings → API & Integrations.")
    d = r.json().get("data", {})
    return {"ok": True, "username": d.get("username"), "plan": (d.get("plan") or {}).get("id")}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, x_apify_token: Optional[str] = Header(None)):
    """The Apify token may come from the server env or (per request) from the browser via X-Apify-Token."""
    if not req.stream:
        return _json(run_analysis(req.mode, req.url, req.max_comments, apify_token=x_apify_token))

    def events():
        gen = analysis_stream(req.mode, req.url, req.max_comments, apify_token=x_apify_token)
        try:
            while True:
                yield dumps(next(gen)) + "\n"
        except StopIteration as stop:
            yield dumps({"type": "result", "analysis": stop.value}) + "\n"
        except ReelSenseError as e:
            yield dumps({"type": "error", "error": e.to_dict()}) + "\n"
        except Exception as e:  # noqa: BLE001
            yield dumps({"type": "error", "error": {"code": "internal_error", "message": "Something went wrong while analyzing this Reel.",
                                                   "details": f"{type(e).__name__}: {e}", "can_use_demo": True}}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    return _json(_get_analysis(analysis_id))


@app.get("/api/analysis/{analysis_id}/comments")
def get_comments(
    analysis_id: str,
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
    q: Optional[str] = None, sentiment: Optional[str] = None, emotion: Optional[str] = None,
    language: Optional[str] = None, include_spam: bool = False,
    sort: Literal["likes", "timestamp", "confidence", "username", "sentiment", "emotion"] = "likes",
    order: Literal["asc", "desc"] = "desc",
):
    items = _get_analysis(analysis_id)["comments"]
    if not include_spam:
        items = [c for c in items if not c["is_spam"]]
    if sentiment: items = [c for c in items if c["sentiment"] == sentiment.lower()]
    if emotion: items = [c for c in items if c["emotion"].lower() == emotion.lower()]
    if language: items = [c for c in items if c["language"].lower() == language.lower()]
    if q:
        ql = q.lower()
        items = [c for c in items if ql in c["text"].lower() or ql in (c.get("username") or "").lower()]
    key = {"likes": lambda c: c.get("likes") or 0, "timestamp": lambda c: c.get("timestamp") or "",
           "confidence": lambda c: c["confidence"], "username": lambda c: (c.get("username") or "").lower(),
           "sentiment": lambda c: c["sentiment"], "emotion": lambda c: c["emotion"]}[sort]
    items = sorted(items, key=key, reverse=(order == "desc"))
    total = len(items)
    start = (page - 1) * page_size
    return _json({"total": total, "page": page, "page_size": page_size, "items": items[start:start + page_size]})


@app.get("/api/analysis/{analysis_id}/insights")
def get_insights(analysis_id: str):
    a = _get_analysis(analysis_id)
    return _json({"id": a["id"], "is_demo": a["is_demo"], "insights": a["insights"], "warnings": a["warnings"]})


def _file(a: dict, fmt: str) -> Response:
    if fmt not in EXPORTERS:
        raise NotFound(f"Unknown export format '{fmt}'. Use csv, excel or pdf.")
    build, mime, ext = EXPORTERS[fmt]
    name = f"reelsense-{'demo-' if a['is_demo'] else ''}{a['id']}.{ext}"
    return Response(build(a), media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/analysis/{analysis_id}/export/{fmt}")
def export_get(analysis_id: str, fmt: str):
    return _file(_get_analysis(analysis_id), fmt)


@app.post("/api/export/{fmt}")
async def export_post(fmt: str, request: Request):
    """Stateless export: the client posts the analysis it already holds
    (works without a result store)."""
    a = await request.json()
    if not isinstance(a, dict) or "comments" not in a or "reel" not in a:
        raise NotFound("Body must be a full analysis object as returned by /api/analyze.")
    return _file(a, fmt)


# ---- single-process local mode: serve the built React app (not used on Vercel) ----
_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
if not os.environ.get("VERCEL") and os.path.isdir(_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_dist, html=True), name="web")

"""Optional result store.

The POC has no database. If Upstash Redis / Vercel KV REST credentials are
configured we keep finished analyses for a day so the GET endpoints work
across serverless invocations. Without them the API is still fully usable:
`POST /api/analyze` returns the complete analysis, demo analyses are
deterministic (re-computable from their id), and exports accept the analysis
in a POST body."""
from __future__ import annotations

import json

import httpx

from .config import settings


def enabled() -> bool:
    return bool(settings.kv_url and settings.kv_token)


def _cmd(*args):
    r = httpx.post(
        settings.kv_url,
        headers={"Authorization": f"Bearer {settings.kv_token}"},
        json=list(args),
        timeout=8,
    )
    r.raise_for_status()
    return r.json().get("result")


def save(analysis_id: str, analysis: dict) -> bool:
    if not enabled():
        return False
    try:
        _cmd("SET", f"reelsense:{analysis_id}", json.dumps(analysis, ensure_ascii=False), "EX", settings.result_ttl_s)
        return True
    except Exception:
        return False


def load(analysis_id: str) -> dict | None:
    if not enabled():
        return None
    try:
        raw = _cmd("GET", f"reelsense:{analysis_id}")
        return json.loads(raw) if raw else None
    except Exception:
        return None

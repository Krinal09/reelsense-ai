"""Provider abstraction.

A provider turns a Reel URL into `(reel, comments)`. It is a *generator*:
it yields progress events and returns the result, so the pipeline can stream
progress with `result = yield from provider.fetch(...)`.

To add a data source: subclass `ReelProvider`, implement `fetch`, and register
it in `providers/__init__.py`.

Normalised shapes
-----------------
reel = {url, id, shortcode, username, caption, thumbnail, published_at,
        views, likes, comments_count, duration_seconds}      # any may be None
comment = {id, username, text, timestamp, likes, reply_count, replies:[...]}
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator

from ..utils import normalize_text

Progress = dict
FetchResult = tuple[dict, list[dict], list[str]]  # reel, comments, warnings


def progress(stage: str, percent: int, message: str) -> Progress:
    return {"type": "progress", "stage": stage, "percent": percent, "message": message}


class ReelProvider(ABC):
    name = "base"
    is_demo = False

    @abstractmethod
    def fetch(self, url: str, max_comments: int) -> Generator[Progress, None, FetchResult]:
        ...


def dedupe_by_id(comments: list[dict]) -> tuple[list[dict], int]:
    """Drop comments that the API returned twice (pagination overlap)."""
    seen: set[str] = set()
    out: list[dict] = []
    dropped = 0
    for c in comments:
        cid = str(c.get("id") or "")
        key = cid or f'{c.get("username")}|{normalize_text(c.get("text", ""))}|{c.get("timestamp")}'
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        out.append(c)
    return out, dropped

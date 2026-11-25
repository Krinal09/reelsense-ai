"""Live provider: any PUBLIC Instagram Reel, no user login.

Uses Apify's maintained Instagram actors (an authorised third-party data
provider) through its REST API, authenticated with a server-side APIFY_TOKEN.
The reel metadata actor and the comment actor run in parallel. Private,
deleted or login-walled Reels return nothing and are reported as such; nothing
here bypasses Instagram access controls itself.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from ..config import settings
from ..errors import (CredentialsMissing, ProcessingTimeout, ProviderUnavailable,
                      RateLimited, UnsupportedReel)
from ..utils import parse_reel_url
from .base import dedupe_by_id, progress

API = "https://api.apify.com/v2/acts"


def _first(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return default


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        n = int(v)
        return None if n < 0 else n  # Instagram uses -1 for hidden counts
    except (TypeError, ValueError):
        return None


class ApifyProvider:
    name = "apify-instagram"
    is_demo = False

    def __init__(self, token: str | None = None):
        self.token = (token or settings.apify_token or "").strip() or None

    def _run(self, actor: str, body: dict, timeout_s: float) -> list[dict]:
        try:
            r = httpx.post(
                f"{API}/{actor}/run-sync-get-dataset-items",
                params={"token": self.token, "timeout": int(timeout_s), "format": "json", "clean": "true"},
                json=body, timeout=timeout_s + 10,
            )
        except httpx.TimeoutException:
            raise ProcessingTimeout("The data provider took too long to respond.", details="Try again, or lower MAX_COMMENTS.")
        except httpx.HTTPError as e:
            raise ProviderUnavailable("Could not reach the data provider.", details=str(e))
        if r.status_code in (200, 201):
            data = r.json()
            return data if isinstance(data, list) else []
        msg = ""
        try:
            msg = r.json().get("error", {}).get("message", "")
        except Exception:
            msg = r.text[:200]
        if r.status_code == 401:
            raise CredentialsMissing("The APIFY_TOKEN is invalid.", details=msg)
        if r.status_code == 402:
            raise ProviderUnavailable("The Apify account has no remaining credits or plan access.", details=msg)
        if r.status_code == 429:
            raise RateLimited("The data provider rate limit was reached. Try again shortly.", details=msg)
        if r.status_code in (408, 504):
            raise ProcessingTimeout("The data provider timed out.", details=msg or "Try again in a moment.")
        raise ProviderUnavailable("The data provider returned an error.", details=f"HTTP {r.status_code}: {msg}")

    def fetch(self, url: str, max_comments: int):
        if not self.token:
            raise CredentialsMissing(
                "An Apify token is needed to read Instagram comments.",
                details="Click the key icon (top right), paste your free Apify token once, and try again.",
            )
        shortcode, canonical = parse_reel_url(url)
        budget = max(30.0, settings.time_budget_s - 20)
        yield progress("metadata", 5, "Contacting the data provider…")
        warnings: list[str] = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_reel = pool.submit(self._run, settings.apify_reel_actor,
                                 {"username": [canonical], "resultsLimit": 1}, budget)
            f_com = pool.submit(self._run, settings.apify_comment_actor,
                                {"directUrls": [canonical], "resultsLimit": max_comments,
                                 "includeNestedComments": settings.apify_include_replies}, budget)
            t0, last = time.monotonic(), ""
            while not (f_reel.done() and f_com.done()):
                time.sleep(1.2)
                el = time.monotonic() - t0
                msg = ("Reading Reel metadata and collecting comments…" if not f_reel.done() or not f_com.done() else "")
                if f_reel.done() and not f_com.done():
                    msg = "Reel metadata received. Collecting comments (this can take up to a minute)…"
                yield progress("comments", min(44, 8 + int(el / budget * 36)), msg or last)
                last = msg
            reel_items = f_reel.result()  # raises mapped errors
            try:
                comment_items = f_com.result()
            except (RateLimited, ProcessingTimeout) as e:
                comment_items = []
                warnings.append(f"Comment collection was interrupted ({e.message}); no comments could be analyzed.")

        if not reel_items:
            raise UnsupportedReel(
                "This Reel couldn't be read.",
                details="It may be private, deleted, age/region restricted, or not a Reel. Only public Reels can be analyzed.",
            )
        r = reel_items[0]
        if r.get("error") or r.get("errorDescription"):
            raise UnsupportedReel("This Reel couldn't be read.", details=str(r.get("errorDescription") or r.get("error")))
        views = _num(_first(r, "videoPlayCount", "playsCount", "videoViewCount", "viewsCount", "playCount"))
        likes = _num(_first(r, "likesCount", "likeCount"))
        total_comments = _num(_first(r, "commentsCount", "commentCount"))
        reel = {
            "url": r.get("url") or canonical,
            "id": str(r.get("id") or shortcode),
            "shortcode": r.get("shortCode") or shortcode,
            "username": _first(r, "ownerUsername", "username"),
            "caption": r.get("caption"),
            "thumbnail": _first(r, "displayUrl", "thumbnailUrl", "imageUrl"),
            "published_at": r.get("timestamp"),
            "views": views, "likes": likes, "comments_count": total_comments,
            "duration_seconds": _first(r, "videoDuration", "duration"),
        }
        if views is None: warnings.append("View count isn't available for this Reel; engagement rate was skipped.")
        if likes is None: warnings.append("Like count is hidden for this Reel.")

        yield progress("comments", 45, f"Processing {len(comment_items)} comments…")
        comments, replies_by_parent = [], {}
        for c in comment_items:
            parent = c.get("repliedToCommentId") or c.get("parentId")
            item = {
                "id": str(c.get("id") or f'{c.get("ownerUsername")}-{c.get("timestamp")}'),
                "username": _first(c, "ownerUsername", "username"),
                "text": c.get("text") or "", "timestamp": c.get("timestamp"),
                "likes": _num(_first(c, "likesCount", "likeCount")),
            }
            if parent:
                replies_by_parent.setdefault(str(parent), []).append(item)
                continue
            raw_replies = c.get("replies") or []
            item["replies"] = [
                {"id": str(x.get("id")), "username": _first(x, "ownerUsername", "username"), "text": x.get("text") or "",
                 "timestamp": x.get("timestamp"), "likes": _num(_first(x, "likesCount", "likeCount"))}
                for x in raw_replies if isinstance(x, dict)]
            item["reply_count"] = _num(c.get("repliesCount")) or len(item["replies"])
            comments.append(item)
        for c in comments:
            extra = replies_by_parent.get(c["id"], [])
            if extra:
                c["replies"] += extra
                c["reply_count"] = max(c["reply_count"], len(c["replies"]))
        comments, dropped = dedupe_by_id(comments)
        if dropped:
            warnings.append(f"Removed {dropped} comments returned twice by the provider.")
        if total_comments and len(comments) < total_comments:
            warnings.append(f"Collected {len(comments)} of {total_comments} comments (provider limit / MAX_COMMENTS).")
        return reel, comments[:max_comments], warnings

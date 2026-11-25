"""Official Instagram Graph API provider.

Scope & limits (by design of the API, not bypassed here):
  * Works for media owned by the Instagram Business/Creator account that the
    access token belongs to (IG_USER_ID). Other accounts' Reels are not
    accessible and are reported as such.
  * Comment access requires the `instagram_manage_comments` permission.
  * Rate limits are respected: on a rate-limit response we stop and return what
    we already have (with a warning) instead of retrying aggressively.
"""
from __future__ import annotations

import httpx

from ..config import settings
from ..errors import (CredentialsMissing, ProviderUnavailable, RateLimited,
                      UnsupportedReel)
from ..utils import extract_shortcode
from .base import FetchResult, ReelProvider, dedupe_by_id, progress

_RATE_CODES = {4, 17, 32, 613, 80002}
_AUTH_CODES = {190, 102}
_PERM_CODES = {10, 200, 3}
MEDIA_FIELDS = (
    "id,permalink,shortcode,media_type,media_product_type,caption,thumbnail_url,"
    "media_url,timestamp,like_count,comments_count,username"
)
COMMENT_FIELDS = (
    "id,text,timestamp,username,like_count,"
    "replies.limit(25){id,text,timestamp,username,like_count}"
)


class GraphApiProvider(ReelProvider):
    name = "instagram-graph-api"

    def __init__(self):
        self.base = f"https://graph.facebook.com/{settings.graph_version}"
        self.client = httpx.Client(timeout=12)

    # ---- low level ----
    def _get(self, url: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        if "access_token" not in url:
            params["access_token"] = settings.ig_access_token
        try:
            r = self.client.get(url, params=params)
        except httpx.TimeoutException:
            raise ProviderUnavailable("Instagram Graph API timed out.", details="Try again in a moment.")
        except httpx.HTTPError as e:
            raise ProviderUnavailable("Could not reach the Instagram Graph API.", details=str(e))
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        if r.status_code >= 400 or "error" in data:
            err = data.get("error", {})
            code = err.get("code")
            msg = err.get("message") or f"HTTP {r.status_code}"
            if code in _RATE_CODES or r.status_code == 429:
                raise RateLimited("Instagram API rate limit reached.", details=msg)
            if code in _AUTH_CODES:
                raise CredentialsMissing("The Instagram access token is invalid or expired.", details=msg)
            if code in _PERM_CODES:
                raise ProviderUnavailable("The token lacks a required Instagram permission.", details=msg)
            raise ProviderUnavailable("Instagram Graph API returned an error.", details=msg)
        return data

    # ---- steps ----
    def _find_media(self, shortcode: str) -> dict:
        url = f"{self.base}/{settings.ig_user_id}/media"
        params = {"fields": MEDIA_FIELDS, "limit": 50}
        for _ in range(40):  # up to 2000 recent media items
            data = self._get(url, params)
            for m in data.get("data", []):
                if m.get("shortcode") == shortcode or f"/{shortcode}" in (m.get("permalink") or ""):
                    return m
            nxt = data.get("paging", {}).get("next")
            if not nxt:
                break
            url, params = nxt, None
        raise UnsupportedReel(
            "This Reel isn't accessible with the connected Instagram account.",
            details="The Graph API only exposes media owned by the account behind IG_USER_ID. "
            "Use one of your own Reels or switch to the Apify provider.",
        )

    def _views(self, media_id: str):
        for metric in ("views", "plays"):  # `plays` was replaced by `views`
            try:
                d = self._get(f"{self.base}/{media_id}/insights", {"metric": metric})
                vals = d.get("data", [])
                if vals:
                    return vals[0]["values"][0]["value"]
            except Exception:
                continue
        return None

    # ---- main ----
    def fetch(self, url: str, max_comments: int):
        shortcode = extract_shortcode(url)
        if not (settings.ig_access_token and settings.ig_user_id):
            raise CredentialsMissing(
                "Instagram API credentials are not configured.",
                details="Set IG_ACCESS_TOKEN and IG_USER_ID in your environment, or set APIFY_TOKEN.",
            )
        warnings: list[str] = []
        yield progress("metadata", 8, "Looking up the Reel in your Instagram account…")
        media = self._find_media(shortcode)
        if media.get("media_product_type") not in (None, "REELS") and media.get("media_type") != "VIDEO":
            raise UnsupportedReel("This post is not a Reel.")
        yield progress("metadata", 15, "Reading Reel metrics…")
        views = self._views(media["id"])
        if views is None:
            warnings.append("View count is not available for this Reel; engagement rate was skipped.")
        reel = {
            "url": media.get("permalink") or url,
            "id": media["id"],
            "shortcode": shortcode,
            "username": media.get("username"),
            "caption": media.get("caption"),
            "thumbnail": media.get("thumbnail_url") or media.get("media_url"),
            "published_at": media.get("timestamp"),
            "views": views,
            "likes": media.get("like_count"),
            "comments_count": media.get("comments_count"),
            "duration_seconds": None,
        }
        if reel["likes"] is None:
            warnings.append("Like count is hidden or unavailable for this Reel.")

        comments: list[dict] = []
        url_c = f"{self.base}/{media['id']}/comments"
        params = {"fields": COMMENT_FIELDS, "limit": 50}
        total = reel.get("comments_count") or max_comments
        page = 0
        while url_c and len(comments) < max_comments:
            page += 1
            try:
                data = self._get(url_c, params)
            except RateLimited as e:
                warnings.append("Instagram rate limit hit; analysis uses the comments collected so far.")
                break
            for c in data.get("data", []):
                reps = [
                    {"id": r.get("id"), "username": r.get("username"), "text": r.get("text", ""),
                     "timestamp": r.get("timestamp"), "likes": r.get("like_count")}
                    for r in (c.get("replies") or {}).get("data", [])
                ]
                comments.append({
                    "id": c.get("id"), "username": c.get("username"), "text": c.get("text", ""),
                    "timestamp": c.get("timestamp"), "likes": c.get("like_count"),
                    "reply_count": len(reps), "replies": reps,
                })
            pct = 15 + int(30 * min(1, len(comments) / max(1, min(total, max_comments))))
            yield progress("comments", pct, f"Collected {len(comments)} comments (page {page})…")
            url_c = data.get("paging", {}).get("next")
            params = None
        comments, dropped = dedupe_by_id(comments)
        if dropped:
            warnings.append(f"Removed {dropped} comments returned twice by the API.")
        comments = comments[:max_comments]
        return reel, comments, warnings

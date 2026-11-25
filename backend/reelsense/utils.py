from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from .errors import InvalidUrl, UnsupportedReel

_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com", "instagr.am"}
_URL_RE = re.compile(
    r"^(?:https?://)?(?P<host>[^/\s]+)/(?P<rest>[^?#\s]*)", re.IGNORECASE
)
_REEL_RE = re.compile(r"^(?:[\w.]+/)?(?P<kind>reels?|p|tv)/(?P<code>[A-Za-z0-9_-]{5,})/?$")


def extract_shortcode(url: str) -> str:
    return parse_reel_url(url)[0]


def parse_reel_url(url: str) -> tuple[str, str]:
    """Validate an Instagram Reel URL -> (shortcode, canonical_url)."""
    url = (url or "").strip()
    if not url:
        raise InvalidUrl("Paste an Instagram Reel URL to analyze.")
    m = _URL_RE.match(url)
    if not m or m.group("host").lower() not in _HOSTS:
        raise InvalidUrl(
            "That doesn't look like an Instagram URL.",
            details="Expected something like https://www.instagram.com/reel/ABC123xyz/",
        )
    rest = m.group("rest")
    r = _REEL_RE.match(rest)
    if not r:
        raise UnsupportedReel(
            "This link is not a Reel.",
            details="Only /reel/<code>/ links (or /p/<code>/ posts that are Reels) are supported. "
            "Stories, profiles and highlights are not supported.",
        )
    kind = "p" if r.group("kind") == "p" else "reel"
    return r.group("code"), f"https://www.instagram.com/{kind}/{r.group('code')}/"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    """Casefold, strip accents/punctuation noise and collapse whitespace
    (used for duplicate detection; the original text is never modified)."""
    t = unicodedata.normalize("NFKC", text or "").casefold()
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)          # soooo -> soo
    t = re.sub(r"[^\w\sऀ-ॿ઀-૿#@]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        # Instagram returns +0000 without colon
        s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

"""Engagement KPIs, distributions and the comment timeline ."""
from __future__ import annotations

from collections import Counter

from datetime import timedelta

from .utils import parse_ts
from .nlp.sentiment import EMOTIONS, SENTIMENTS


def _pct(n: int, d: int) -> float | None:
    return round(n / d * 100, 1) if d else None


def engagement_rate(reel: dict) -> tuple[float | None, str | None]:
    """((Likes + Comments) / Views) * 100 – only when all three values exist."""
    v, l, c = reel.get("views"), reel.get("likes"), reel.get("comments_count")
    missing = [n for n, x in (("views", v), ("likes", l), ("comments", c)) if x is None]
    if missing:
        return None, f"Not available: {', '.join(missing)} not provided for this Reel."
    if not v:
        return None, "Not available: views is zero."
    return round((l + c) / v * 100, 2), None


def compute(reel: dict, comments: list[dict]) -> dict:
    analyzed = [c for c in comments if c["analyzed"]]
    n = len(analyzed)
    sc = Counter(c["sentiment"] for c in analyzed)
    sentiment = {
        "counts": {s: sc.get(s, 0) for s in SENTIMENTS},
        "percentages": {s: _pct(sc.get(s, 0), n) for s in SENTIMENTS},
        "average_confidence": round(sum(c["confidence"] for c in analyzed) / n, 3) if n else None,
    }
    ec = Counter(c["emotion"] for c in analyzed)
    emotions = [{"emotion": e, "count": ec.get(e, 0), "percentage": _pct(ec.get(e, 0), n)} for e in EMOTIONS]
    lc = Counter((c["language"]) for c in comments)
    languages = [{"language": k, "count": v, "percentage": _pct(v, len(comments))} for k, v in lc.most_common()]

    likes = [c.get("likes") for c in comments if c.get("likes") is not None and not c["is_spam"]]
    pool = [c for c in comments if not c["is_spam"] and c.get("likes") is not None]
    top = max(pool, key=lambda c: c["likes"]) if pool else None
    er, er_note = engagement_rate(reel)

    liked_by_sent = {s: 0 for s in SENTIMENTS}
    for c in analyzed:
        liked_by_sent[c["sentiment"]] += c.get("likes") or 0

    kpis = {
        "views": reel.get("views"), "likes": reel.get("likes"), "comments": reel.get("comments_count"),
        "engagement_rate": er, "engagement_rate_note": er_note,
        "positive_pct": sentiment["percentages"]["positive"], "negative_pct": sentiment["percentages"]["negative"],
        "neutral_pct": sentiment["percentages"]["neutral"],
        "avg_comment_likes": round(sum(likes) / len(likes), 2) if likes else None,
        "most_liked_comment": {"id": top["id"], "username": top.get("username"), "text": top["text"], "likes": top["likes"],
                               "sentiment": top["sentiment"]} if top else None,
    }

    engagement = {
        "ratios": {
            "like_rate": round(reel["likes"] / reel["views"] * 100, 2) if reel.get("views") and reel.get("likes") is not None else None,
            "comment_rate": round(reel["comments_count"] / reel["views"] * 100, 3) if reel.get("views") and reel.get("comments_count") is not None else None,
        },
        "likes_by_sentiment": [{"sentiment": s, "likes": liked_by_sent[s]} for s in SENTIMENTS],
        "totals": [
            {"metric": m, "value": v} for m, v in (("Likes", reel.get("likes")), ("Comments", reel.get("comments_count")),
                                                   ("Fetched comments", len(comments)))
            if v is not None
        ],
    }

    # ---- timeline ----
    timeline, granularity = [], "day"
    stamped = [(parse_ts(c.get("timestamp")), c["sentiment"]) for c in analyzed if c.get("timestamp")]
    stamped = [(t, s) for t, s in stamped if t]
    if stamped:
        span_h = (max(t for t, _ in stamped) - min(t for t, _ in stamped)).total_seconds() / 3600
        granularity = "hour" if span_h <= 48 else "day"
        buckets: dict = {}
        for t, sent in stamped:
            b = t.replace(minute=0, second=0, microsecond=0) if granularity == "hour" else t.replace(hour=0, minute=0, second=0, microsecond=0)
            buckets.setdefault(b, Counter())[sent] += 1
        for b in sorted(buckets):
            r = buckets[b]
            timeline.append({
                "date": b.strftime("%Y-%m-%d %H:00" if granularity == "hour" else "%Y-%m-%d"),
                "positive": r["positive"], "negative": r["negative"], "neutral": r["neutral"],
                "total": r["positive"] + r["negative"] + r["neutral"],
            })
    return {"kpis": kpis, "sentiment": sentiment, "emotions": emotions, "languages": languages,
            "engagement": engagement, "timeline": {"granularity": granularity, "points": timeline}}

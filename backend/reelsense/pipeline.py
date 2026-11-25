"""Orchestrates: fetch -> clean -> classify -> analyse -> insights.

`analysis_stream()` is a generator yielding progress events and finally the
result, so the API can stream it; `run_analysis()` simply drains it."""
from __future__ import annotations

import time
import uuid
from typing import Generator

from . import engagement, store
from .config import settings
from .errors import NoComments, ProcessingTimeout
from .insights import build_insights
from .nlp import analytics as nlpa
from .nlp.aspects import detect_aspects, split_clauses
from .nlp.sentiment import SentimentEngine
from .providers import get_provider
from .providers.base import progress
from .utils import extract_shortcode, normalize_text, now_iso

DEMO_SEED = 7


def demo_id(seed: int = DEMO_SEED) -> str:
    return f"demo-{seed}"


def _clause_aspects(engine: SentimentEngine, comments: list[dict]) -> None:
    """Aspect sentiment. Single-aspect comments inherit the comment's prediction;
    multi-aspect comments with contrast are scored clause by clause."""
    todo: list[tuple[dict, str, list[str]]] = []
    for c in comments:
        asp = detect_aspects(c["text"])
        c["aspects"] = []
        if not asp:
            continue
        if len(asp) >= 2:
            for cl in split_clauses(c["text"]):
                ca = detect_aspects(cl)
                if ca and len(split_clauses(c["text"])) > 1:
                    todo.append((c, cl, ca))
        c["_asp"] = asp
    texts = [t for _, t, _ in todo]
    results = []
    for i in range(0, len(texts), engine.BATCH):
        results += engine._sentiment_batch(texts[i:i + engine.BATCH])
    seen: dict[str, set] = {}
    for (c, _, ca), (lab, conf, _, _) in zip(todo, results):
        for a in ca:
            if a not in seen.setdefault(c["id"], set()):
                seen[c["id"]].add(a)
                c["aspects"].append({"aspect": a, "sentiment": lab, "confidence": round(conf, 3)})
    for c in comments:
        for a in c.pop("_asp", []):
            if a not in seen.get(c["id"], set()):
                c["aspects"].append({"aspect": a, "sentiment": c["sentiment"], "confidence": c["confidence"]})


def analysis_stream(mode: str, url: str | None, max_comments: int | None = None, seed: int = DEMO_SEED, apify_token: str | None = None) -> Generator[dict, None, dict]:
    t0 = time.monotonic()
    deadline = t0 + settings.time_budget_s
    max_comments = min(max_comments or settings.max_comments, settings.max_comments)

    yield progress("validate", 2, "Validating request…")
    if mode == "live":
        extract_shortcode(url or "")  # raises InvalidUrl / UnsupportedReel early
    provider = get_provider(mode, apify_token)
    if mode == "demo":
        provider.seed = seed

    reel, raw, warnings = yield from provider.fetch(url or "", max_comments)
    if time.monotonic() > deadline - 5:
        raise ProcessingTimeout("Fetching comments used up the processing time budget.",
                                details="Lower MAX_COMMENTS or try again.")
    if not raw:
        raise NoComments(
            "No accessible comments were found for this Reel.",
            details="Comments may be disabled, restricted, or not exposed by the data provider.",
        )

    # ---- clean ----
    yield progress("clean", 46, "Detecting spam and duplicate comments…")
    comments = []
    for c in raw:
        c = dict(c)
        c["text"] = c.get("text") or ""
        c["likes"] = c.get("likes")
        c["replies"] = c.get("replies") or []
        c["reply_count"] = c.get("reply_count", len(c["replies"]))
        comments.append(c)
    nlpa.detect_spam(comments)
    dup_flagged = nlpa.detect_duplicates(comments)
    for c in comments:
        c["is_question"] = nlpa.is_question(c["text"])
        c["analyzed"] = (not c["is_spam"]) and (not c["is_duplicate"])

    # ---- classify unique texts only ----
    engine = SentimentEngine(deadline)
    reps: dict[str, dict] = {}
    for c in comments:
        reps.setdefault(normalize_text(c["text"]) or c["text"], c)
    results = yield from engine.run(list(reps.values()))
    for c in comments:
        r = results[reps[normalize_text(c["text"]) or c["text"]]["id"]]
        c.update(
            language=r["language"], language_code=r["language_code"], sentiment=r["sentiment"],
            confidence=r["confidence"], emotion=r["emotion"], emotion_confidence=r["emotion_confidence"],
            sentiment_engine=r["sentiment_engine"],
        )

    yield progress("aspects", 82, "Running aspect-based sentiment…")
    _clause_aspects(engine, comments)

    yield progress("nlp", 86, "Extracting keywords, topics and questions…")
    analyzed = [c for c in comments if c["analyzed"]]
    keywords, cloud = nlpa.keyword_stats(analyzed)
    hashtags, caption_tags = nlpa.hashtag_stats([c for c in comments if not c["is_spam"]], reel.get("caption"))
    topics = nlpa.topic_model(analyzed)
    similar = nlpa.similar_groups(analyzed)
    faqs = nlpa.faq_groups([c for c in comments if not c["is_spam"]])
    aspects, appreciated, criticized = nlpa.aspect_summary(analyzed)

    dup_groups: dict[int, list[dict]] = {}
    for c in comments:
        if c.get("duplicate_group"):
            dup_groups.setdefault(c["duplicate_group"], []).append(c)
    duplicates = sorted(
        [{"text": g[0]["text"], "count": len(g)} for g in dup_groups.values()], key=lambda d: -d["count"])[:10]
    spam = [{"id": c["id"], "username": c.get("username"), "text": c["text"], "reasons": c["spam_reasons"],
             "score": c["spam_score"]} for c in comments if c["is_spam"]]

    yield progress("engagement", 92, "Computing engagement analytics…")
    eng = engagement.compute(reel, comments)

    summary = {
        "fetched": len(comments), "analyzed": len(analyzed), "spam": len(spam), "duplicates": dup_flagged,
        "questions": sum(1 for c in comments if c["is_question"] and not c["is_spam"]),
        "replies_collected": sum(len(c["replies"]) for c in comments),
        "reel_total_comments": reel.get("comments_count"),
        "note": "Sentiment statistics use analyzed comments only (spam and exact duplicates removed).",
    }

    engines = engine.engine_summary()

    is_demo = provider.is_demo
    analysis = {
        "id": demo_id(seed) if is_demo else uuid.uuid4().hex[:16],
        "created_at": now_iso(), "mode": mode, "is_demo": is_demo, "provider": provider.name,
        "reel": reel, "summary": summary, "kpis": eng["kpis"], "sentiment": eng["sentiment"],
        "emotions": eng["emotions"], "languages": eng["languages"], "engagement": eng["engagement"],
        "timeline": eng["timeline"],
        "nlp": {
            "keywords": keywords, "word_cloud": cloud, "hashtags": hashtags, "caption_hashtags": caption_tags,
            "topics": topics, "similar_groups": similar, "duplicates": duplicates, "spam": spam, "faqs": faqs,
            "aspects": aspects, "appreciated_aspects": appreciated, "criticized_aspects": criticized,
        },
        "comments": comments, "engines": engines, "warnings": warnings,
        "processing_seconds": round(time.monotonic() - t0, 2),
    }
    analysis["insights"] = build_insights(analysis)

    yield progress("finalize", 98, "Finalizing report…")
    analysis["persisted"] = store.save(analysis["id"], analysis)
    return analysis


def run_analysis(mode: str, url: str | None, max_comments: int | None = None, seed: int = DEMO_SEED, apify_token: str | None = None) -> dict:
    gen = analysis_stream(mode, url, max_comments, seed, apify_token)
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value

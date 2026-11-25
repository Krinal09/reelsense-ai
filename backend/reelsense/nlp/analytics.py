"""NLP analytics over classified comments: spam, duplicates, similarity groups,
keywords, hashtags, word cloud, topics, FAQs and aspect aggregation."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import numpy as np

from ..utils import normalize_text
from .text import (EMOJI_RE, HASHTAG_RE, MENTION_RE, URL_RE, content_tokens,
                   detect_language, emoji_count, tokenize)

# ------------------------------------------------------------------ spam & duplicates
_SPAM_PHRASES = [
    "follow back", "follow me", "dm me", "dm for", "click link", "link in bio", "check my profile", "check out my page",
    "giveaway", "free iphone", "win iphone", "earn $", "earn money", "make money", "from home", "buy followers",
    "cheap followers", "promote your", "sponsorship", "crypto signal", "hot singles", "click here", "whatsapp me",
    "telegram", "forex", "investment plan", "visit www", "free prizes",
]
_MONEY = re.compile(r"[$₹€£]\s?\d{2,}|\b\d{2,}\s?(?:usd|inr|rs)\b", re.I)


def detect_spam(comments: list[dict]) -> None:
    """Adds `spam_score`, `is_spam`, `spam_reasons` to each comment (in place)."""
    by_text: dict[str, set[str]] = defaultdict(set)
    for c in comments:
        by_text[normalize_text(c["text"])].add(c.get("username") or c["id"])
    for c in comments:
        t = c["text"] or ""
        low = t.lower()
        score, why = 0.0, []
        if URL_RE.search(t):
            score += 0.5; why.append("contains a link")
        if any(p in low for p in _SPAM_PHRASES):
            score += 0.45; why.append("promotional phrase")
        if len(MENTION_RE.findall(t)) >= 1 and len(t) > 25 and (score > 0 or len(MENTION_RE.findall(t)) >= 2):
            score += 0.2; why.append("promotes another account")
        if len(HASHTAG_RE.findall(t)) > 3:
            score += 0.15; why.append("hashtag stuffing")
        if _MONEY.search(t):
            score += 0.25; why.append("money claim")
        norm = normalize_text(t)
        if len(norm) > 25 and len(by_text[norm]) >= 3:
            score += 0.4; why.append("same text posted by 3+ accounts")
        c["spam_score"] = round(min(1.0, score), 2)
        c["is_spam"] = score >= 0.5
        c["spam_reasons"] = why


def detect_duplicates(comments: list[dict]) -> int:
    """Marks exact (normalised) repeats. The earliest comment of each group is kept
    as the original; later ones get `is_duplicate=True`. Returns number flagged."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in comments:
        key = normalize_text(c["text"]) or (c["text"] or "").strip()
        groups[key].append(c)
    flagged, gid = 0, 0
    for key, items in groups.items():
        for c in items:
            c["is_duplicate"], c["duplicate_group"] = False, None
        if len(items) < 2 or not key:
            continue
        gid += 1
        items.sort(key=lambda c: c.get("timestamp") or "")
        for c in items:
            c["duplicate_group"] = gid
        for c in items[1:]:
            c["is_duplicate"] = True
            flagged += 1
    return flagged


# ------------------------------------------------------------------ similar comments
def similar_groups(comments: list[dict], threshold: float = 0.55, limit: int = 8) -> list[dict]:
    from .mini_ml import Tfidf, char_wb, cosine_matrix, nmf as run_nmf

    items = [c for c in comments if len(normalize_text(c["text"])) >= 10]
    if len(items) < 4:
        return []
    X = Tfidf(lambda t: char_wb(t, 3, 5)).fit_transform([normalize_text(c["text"]) for c in items])
    S = cosine_matrix(X)
    assigned, groups = set(), []
    for i in range(len(items)):
        if i in assigned:
            continue
        members = [j for j in np.where(S[i] >= threshold)[0] if j not in assigned]
        if len(members) >= 2:
            assigned.update(members)
            groups.append(members)
    out = []
    for g in groups:
        cs = [items[j] for j in g]
        rep = max(cs, key=lambda c: (c.get("likes") or 0))
        out.append({
            "size": len(cs), "representative": rep["text"],
            "comment_ids": [c["id"] for c in cs][:20],
            "dominant_sentiment": Counter(c["sentiment"] for c in cs).most_common(1)[0][0],
        })
    out.sort(key=lambda g: -g["size"])
    return out[:limit]


# ------------------------------------------------------------------ keywords / hashtags / cloud
def keyword_stats(comments: list[dict], top: int = 20):
    cnt, doc, sent = Counter(), Counter(), defaultdict(Counter)
    for c in comments:
        toks = [t for t in content_tokens(c["text"]) if not EMOJI_RE.fullmatch(t)]
        cnt.update(toks)
        for t in set(toks):
            doc[t] += 1
            sent[t][c["sentiment"]] += 1
    ranked = sorted(cnt, key=lambda t: (-doc[t], -cnt[t]))
    def row(t):
        dom = sent[t].most_common(1)[0][0] if sent[t] else "neutral"
        return {"word": t, "count": cnt[t], "comments": doc[t], "sentiment": dom,
                "positive": sent[t]["positive"], "negative": sent[t]["negative"], "neutral": sent[t]["neutral"]}
    keywords = [row(t) for t in ranked[:top]]
    cloud = [row(t) for t in ranked[:60]]
    return keywords, cloud


def hashtag_stats(comments: list[dict], caption: str | None, top: int = 15):
    cnt = Counter()
    for c in comments:
        cnt.update(h.lower() for h in HASHTAG_RE.findall(c["text"] or ""))
    cap = [h.lower() for h in HASHTAG_RE.findall(caption or "")]
    return [{"tag": t, "count": n} for t, n in cnt.most_common(top)], list(dict.fromkeys(cap))


# ------------------------------------------------------------------ topics (NMF)
def topic_model(comments: list[dict]):
    from .mini_ml import Tfidf, char_wb, cosine_matrix, nmf as run_nmf

    docs = [c for c in comments if len(content_tokens(c["text"])) >= 2]
    if len(docs) < 12:
        return {"available": False, "reason": "Not enough text-bearing comments for topic modeling (need ≥ 12).", "topics": []}
    vec = Tfidf(content_tokens, min_df=2, max_df=0.7)
    X = vec.fit_transform([c["text"] for c in docs])
    if X.shape[1] < 6:
        return {"available": False, "reason": "Vocabulary too small for topic modeling.", "topics": []}
    k = int(max(2, min(6, round(len(docs) / 25), X.shape[1] // 3)))
    W, H = run_nmf(X, k)
    terms = np.array(vec.vocab)
    assign = W.argmax(axis=1)
    topics = []
    for t in range(k):
        idx = np.where(assign == t)[0]
        if len(idx) == 0:
            continue
        top_terms = terms[H[t].argsort()[::-1][:6]].tolist()
        cs = [docs[i] for i in idx]
        sc = Counter(c["sentiment"] for c in cs)
        best = max(idx, key=lambda i: W[i, t])
        topics.append({
            "id": t + 1, "label": " · ".join(top_terms[:3]), "terms": top_terms, "comment_count": int(len(idx)),
            "share": round(len(idx) / len(docs) * 100, 1),
            "positive": sc["positive"], "negative": sc["negative"], "neutral": sc["neutral"],
            "example": docs[int(best)]["text"],
        })
    topics.sort(key=lambda t: -t["comment_count"])
    return {"available": True, "topics": topics}


# ------------------------------------------------------------------ FAQs
_Q_START = {
    "what", "how", "where", "when", "which", "who", "why", "can", "could", "does", "do", "is", "are", "will", "would", "should",
    "kya", "kaise", "kaha", "kahan", "kab", "kitna", "kitni", "kitne", "kaun", "kyu", "kyun", "kisme", "konsa", "kaunsa",
    "क्या", "कैसे", "कहाँ", "कहां", "कब", "कितना", "कितनी", "कितने", "कौन", "क्यों",
    "શું", "ક્યાં", "કેટલી", "કેટલું", "કેટલા", "કેવી", "કેવું", "કોણ", "ક્યારે", "કેમ",
}
_Q_ANY = {"kya", "kaise", "kaha", "kahan", "kab", "kitna", "kitni", "kitne", "kaun", "क्या", "कैसे", "कहाँ", "कब", "कितना",
          "कितनी", "कौन", "શું", "ક્યાં", "કેટલી", "કેટલું", "ક્યારે", "કેમ", "kab"}
_Q_ONLY_WORD = re.compile(r"^(price|link|link please|kitne ka|rate|cost)\??$", re.I)


def is_question(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if "?" in t or "？" in t or _Q_ONLY_WORD.match(t):
        return True
    toks = tokenize(t)
    if not toks:
        return False
    return toks[0] in _Q_START or any(w in _Q_ANY for w in toks)


def faq_groups(comments: list[dict], limit: int = 8) -> list[dict]:
    from .mini_ml import Tfidf, char_wb, cosine_matrix, nmf as run_nmf

    qs = [c for c in comments if is_question(c["text"])]
    if not qs:
        return []
    norm = [normalize_text(c["text"]) or c["text"] for c in qs]
    if len(qs) == 1:
        groups = [[0]]
    else:
        X = Tfidf(lambda t: char_wb(t, 2, 4)).fit_transform(norm)
        S = cosine_matrix(X)
        assigned, groups = set(), []
        for i in range(len(qs)):
            if i in assigned:
                continue
            g = [j for j in np.where(S[i] >= 0.5)[0] if j not in assigned]
            assigned.update(g)
            groups.append(g or [i])
    out = []
    for g in groups:
        cs = [qs[j] for j in g]
        rep = max(cs, key=lambda c: ((c.get("likes") or 0), len(c["text"])))
        out.append({
            "question": rep["text"], "count": len(cs),
            "total_likes": int(sum(c.get("likes") or 0 for c in cs)),
            "language": rep.get("language"), "comment_ids": [c["id"] for c in cs][:20],
        })
    out.sort(key=lambda q: (-q["count"], -q["total_likes"]))
    return out[:limit]


# ------------------------------------------------------------------ aspects aggregation
def aspect_summary(comments: list[dict]):
    agg = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "conf": 0.0, "pos_ex": None, "neg_ex": None})
    for c in comments:
        for a in c.get("aspects", []):
            r = agg[a["aspect"]]
            r[a["sentiment"]] += 1
            r["conf"] += a.get("confidence", 0)
            likes = c.get("likes") or 0
            if a["sentiment"] == "positive" and (r["pos_ex"] is None or likes > r["pos_ex"][0]):
                r["pos_ex"] = (likes, c["text"])
            if a["sentiment"] == "negative" and (r["neg_ex"] is None or likes > r["neg_ex"][0]):
                r["neg_ex"] = (likes, c["text"])
    rows = []
    for name, r in agg.items():
        m = r["positive"] + r["negative"] + r["neutral"]
        rows.append({
            "aspect": name, "mentions": m, "positive": r["positive"], "negative": r["negative"], "neutral": r["neutral"],
            "net_score": round((r["positive"] - r["negative"]) / m, 3), "avg_confidence": round(r["conf"] / m, 3),
            "positive_example": r["pos_ex"][1] if r["pos_ex"] else None,
            "negative_example": r["neg_ex"][1] if r["neg_ex"] else None,
        })
    rows.sort(key=lambda r: -r["mentions"])
    appreciated = sorted([r for r in rows if r["positive"] > 0], key=lambda r: (-r["positive"], -r["net_score"]))[:5]
    criticized = sorted([r for r in rows if r["negative"] > 0], key=lambda r: (-r["negative"], r["net_score"]))[:5]
    return rows, appreciated, criticized

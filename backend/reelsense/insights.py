"""Grounded AI insights.

Every sentence is assembled from numbers and comments that were actually
computed in the analysis – no generative model, no invented statistics.
Quotes are verbatim comments (original language preserved)."""
from __future__ import annotations


def _q(text: str, n: int = 170) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def _reaction(pos, neg):
    if pos is None or neg is None:
        return "Unknown"
    d = pos - neg
    if d >= 40: return "Overwhelmingly positive"
    if d >= 15: return "Mostly positive"
    if d > -15: return "Mixed"
    if d > -40: return "Mostly negative"
    return "Overwhelmingly negative"


_ADVICE = {
    "Pricing": "Address price head-on: show a cost-vs-value breakdown or compare alternatives so price objections are answered in the video.",
    "Video quality": "Check resolution, stabilisation and pacing – viewers flag the picture/editing quality as a weak point.",
    "Music": "Review the audio mix (music vs. voice level) and track choice – viewers react to the music.",
    "Service": "Pin a comment with support, delivery and warranty details so service concerns are answered in one place.",
    "Creator": "Be explicit about sponsorships and cover downsides as well as upsides to address authenticity concerns.",
    "Content": "Tighten structure or vary the format – viewers comment on the content itself being repetitive or unclear.",
    "Product": "Cover the product weaknesses viewers raise (see the complaints below) instead of leaving them to the comments.",
}


def build_insights(a: dict) -> dict:
    k, s, nlp = a["kpis"], a["sentiment"], a["nlp"]
    summ = a["summary"]
    n = summ["analyzed"]
    pos, neg, neu = k["positive_pct"], k["negative_pct"], k["neutral_pct"]
    comments = a["comments"]
    analyzed = [c for c in comments if c["analyzed"]]
    label = _reaction(pos, neg)
    dom_emotion = max(a["emotions"], key=lambda e: e["count"]) if a["emotions"] else None
    app, crit = nlp["appreciated_aspects"], nlp["criticized_aspects"]
    faqs = nlp["faqs"]

    # ---- executive summary ----
    parts = []
    if n:
        parts.append(f"Of {summ['fetched']} comments collected, {n} were analyzed after removing {summ['spam']} spam and "
                     f"{summ['duplicates']} duplicate comments. Sentiment is {pos}% positive, {neg}% negative and {neu}% neutral "
                     f"({label.lower()}).")
        if dom_emotion and dom_emotion["count"]:
            parts.append(f"The dominant emotion is {dom_emotion['emotion'].lower()} ({dom_emotion['percentage']}% of analyzed comments).")
        if app:
            parts.append(f"The most appreciated aspect is {app[0]['aspect'].lower()} ({app[0]['positive']} positive mentions).")
        if crit:
            parts.append(f"The most criticized aspect is {crit[0]['aspect'].lower()} ({crit[0]['negative']} negative mentions).")
        if faqs:
            parts.append(f"The most common question was asked {faqs[0]['count']} time(s): “{_q(faqs[0]['question'], 90)}”.")
    else:
        parts.append("No analyzable comments were found for this Reel.")
    if k["engagement_rate"] is not None:
        parts.append(f"Engagement rate is {k['engagement_rate']}% ((likes + comments) / views).")
    if a["is_demo"]:
        parts.append("This is SAMPLE data from Demo Mode.")

    # ---- positive / negative feedback ----
    def feedback(rows, kind):
        out = []
        for r in rows[:4]:
            ex = r["positive_example"] if kind == "positive" else r["negative_example"]
            out.append({"theme": r["aspect"], "mentions": r["mentions"], "count": r[kind], "example": _q(ex) if ex else None})
        return out

    top_pos = feedback(app, "positive")
    top_neg = feedback(crit, "negative")

    neg_comments = sorted([c for c in analyzed if c["sentiment"] == "negative"],
                          key=lambda c: (-(c.get("likes") or 0), -c["confidence"]))[:5]
    complaints = [{"text": _q(c["text"]), "likes": c.get("likes") or 0, "language": c["language"],
                   "aspects": [x["aspect"] for x in c.get("aspects", []) if x["sentiment"] == "negative"]} for c in neg_comments]
    pos_comments = sorted([c for c in analyzed if c["sentiment"] == "positive"],
                          key=lambda c: (-(c.get("likes") or 0), -c["confidence"]))[:5]
    praise = [{"text": _q(c["text"]), "likes": c.get("likes") or 0, "language": c["language"]} for c in pos_comments]

    # ---- suggestions (rule-based, each cites its evidence) ----
    suggestions = []
    for r in crit:
        if r["negative"] >= 2 and r["negative"] / r["mentions"] >= 0.3:
            suggestions.append({
                "suggestion": _ADVICE.get(r["aspect"], f"Look at how {r['aspect'].lower()} is handled."),
                "evidence": f"{r['negative']} of {r['mentions']} comments mentioning {r['aspect'].lower()} are negative.",
            })
    if faqs and faqs[0]["count"] >= 2:
        suggestions.append({
            "suggestion": "Pin an answer (or add the info to the caption) for the most-asked question.",
            "evidence": f"“{_q(faqs[0]['question'], 80)}” and similar wording appeared {faqs[0]['count']} times.",
        })
    if summ["fetched"] and summ["spam"] / summ["fetched"] >= 0.05:
        suggestions.append({
            "suggestion": "Turn on Instagram's hidden-words / spam filters for comments.",
            "evidence": f"{summ['spam']} of {summ['fetched']} comments ({round(summ['spam'] / summ['fetched'] * 100)}%) were flagged as spam.",
        })
    if not suggestions:
        suggestions.append({"suggestion": "No clear weak spot stands out; keep the current format.",
                            "evidence": "No aspect had a meaningful share of negative mentions."})

    # ---- next content ideas ----
    ideas = []
    for q in faqs[:3]:
        ideas.append({"idea": f"A follow-up that answers: “{_q(q['question'], 90)}”", "basis": f"asked {q['count']} time(s)"})
    for t in (nlp["topics"].get("topics") or [])[:2]:
        ideas.append({"idea": f"Go deeper on “{t['label']}”", "basis": f"topic in {t['comment_count']} comments ({t['share']}%)"})
    for r in app[:2]:
        ideas.append({"idea": f"Lean into {r['aspect'].lower()} – the audience responds to it", "basis": f"{r['positive']} positive mentions"})
    if nlp["hashtags"]:
        h = nlp["hashtags"][0]
        ideas.append({"idea": f"Audience-driven theme {h['tag']}", "basis": f"used {h['count']} time(s) in comments"})
    if not ideas:
        ideas.append({"idea": "Collect more comments to surface content ideas.", "basis": "too little signal in this sample"})

    discussed = [{"topic": t["label"], "comments": t["comment_count"], "share": t["share"]} for t in (nlp["topics"].get("topics") or [])[:5]]
    aspects_discussed = [{"aspect": r["aspect"], "mentions": r["mentions"]} for r in nlp["aspects"][:5]]

    return {
        "executive_summary": " ".join(parts),
        "audience_reaction": {
            "label": label, "positive_pct": pos, "negative_pct": neg, "neutral_pct": neu,
            "dominant_emotion": dom_emotion["emotion"] if dom_emotion and dom_emotion["count"] else None,
            "text": f"{label}: {pos}% positive vs {neg}% negative." if n else "No data.",
        },
        "top_positive_feedback": top_pos, "top_negative_feedback": top_neg,
        "praised_comments": praise, "common_complaints": complaints,
        "frequently_asked_questions": [{"question": _q(q["question"]), "count": q["count"], "likes": q["total_likes"]} for q in faqs[:6]],
        "most_discussed_topics": discussed, "most_discussed_aspects": aspects_discussed,
        "improvement_suggestions": suggestions, "next_content_ideas": ideas,
        "method": "Rule-based synthesis of the computed statistics and verbatim comments. No generative model was used and no figures are estimated.",
    }

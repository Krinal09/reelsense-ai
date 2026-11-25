"""CSV / Excel / PDF report builders (pure functions: analysis dict -> bytes)."""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone

import csv

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def comment_rows(a: dict) -> list[dict]:
    return [{
        "comment_id": c["id"], "username": c.get("username"), "comment": c["text"], "sentiment": c["sentiment"],
        "confidence": c["confidence"], "emotion": c["emotion"], "language": c["language"], "likes": c.get("likes"),
        "reply_count": c.get("reply_count"), "timestamp": c.get("timestamp"), "is_question": c.get("is_question"),
        "is_spam": c["is_spam"], "is_duplicate": c["is_duplicate"],
        "aspects": "; ".join(f"{x['aspect']}:{x['sentiment']}" for x in c.get("aspects", [])),
    } for c in a["comments"]]


def to_csv(a: dict) -> bytes:
    rows = comment_rows(a)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["comment_id"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM so Excel opens Hindi/Gujarati/emoji correctly


def _sheet(wb, title: str, rows: list[dict], header: list[str] | None = None):
    ws = wb.create_sheet(title)
    cols = header or (list(rows[0].keys()) if rows else ["note"])
    ws.append(cols)
    for r in rows:
        ws.append([("" if r.get(c) is None else (r[c] if isinstance(r[c], (int, float, str, bool)) else str(r[c]))) for c in cols])
    for i, col in enumerate(ws.columns, 1):
        width = max((len(str(c.value)) for c in list(col)[:60] if c.value is not None), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(60, max(10, width + 2))
    ws.freeze_panes = "A2"
    return ws


def to_excel(a: dict) -> bytes:
    from openpyxl import Workbook
    k, reel, ins, nlp = a["kpis"], a["reel"], a["insights"], a["nlp"]
    wb = Workbook()
    wb.remove(wb.active)
    summary = [
        ("Data source", "DEMO – sample data" if a["is_demo"] else a["provider"]),
        ("Reel URL", reel.get("url")), ("Creator", reel.get("username")), ("Published", reel.get("published_at")),
        ("Views", k["views"]), ("Likes", k["likes"]), ("Comments (total)", k["comments"]),
        ("Engagement rate %", k["engagement_rate"]), ("Comments analyzed", a["summary"]["analyzed"]),
        ("Spam removed", a["summary"]["spam"]), ("Duplicates removed", a["summary"]["duplicates"]),
        ("Positive %", k["positive_pct"]), ("Negative %", k["negative_pct"]), ("Neutral %", k["neutral_pct"]),
        ("Avg comment likes", k["avg_comment_likes"]),
        ("Sentiment model", a["engines"]["sentiment"]), ("Emotion model", a["engines"]["emotion"]),
        ("Executive summary", ins["executive_summary"]),
    ]
    _sheet(wb, "Summary", [{"Metric": m, "Value": v} for m, v in summary])
    _sheet(wb, "Comments", comment_rows(a), header=list(comment_rows(a)[0].keys()) if a["comments"] else None)
    _sheet(wb, "Aspects", nlp["aspects"], header=["aspect", "mentions", "positive", "negative", "neutral", "net_score", "avg_confidence"])
    _sheet(wb, "Keywords", nlp["keywords"], header=["word", "count", "comments", "sentiment", "positive", "negative", "neutral"])
    _sheet(wb, "Hashtags", nlp["hashtags"], header=["tag", "count"])
    _sheet(wb, "Topics", [{"label": t["label"], "terms": ", ".join(t["terms"]), "comments": t["comment_count"], "share_pct": t["share"],
                           "positive": t["positive"], "negative": t["negative"], "neutral": t["neutral"], "example": t["example"]}
                          for t in nlp["topics"].get("topics", [])],
           header=["label", "terms", "comments", "share_pct", "positive", "negative", "neutral", "example"])
    _sheet(wb, "FAQs", [{"question": q["question"], "count": q["count"], "likes": q["total_likes"]} for q in nlp["faqs"]],
           header=["question", "count", "likes"])
    _sheet(wb, "Timeline", a["timeline"]["points"], header=["date", "positive", "negative", "neutral", "total"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _safe(text: str, limit: int = 160) -> str:
    """Core PDF fonts are Latin-1 only: strip emoji, mark non-Latin scripts."""
    t = _EMOJI.sub("", text or "").strip()
    enc = t.encode("latin-1", "replace").decode("latin-1")
    if t and enc.count("?") > max(2, len(t) * 0.3):
        return "[text in non-Latin script – see CSV/Excel export]"
    t = enc if enc else "(emoji only)"
    t = " ".join(t.split())
    return t if len(t) <= limit else t[: limit - 1] + "..."


def to_pdf(a: dict) -> bytes:
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    k, reel, ins, nlp = a["kpis"], a["reel"], a["insights"], a["nlp"]
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=22, textColor=colors.HexColor("#4f46e5"), alignment=0, spaceAfter=4)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13, textColor=colors.HexColor("#111827"), spaceBefore=12, spaceAfter=4)
    P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.5, leading=13)
    SM = ParagraphStyle("SM", parent=P, fontSize=8.5, textColor=colors.HexColor("#4b5563"))
    p = lambda t, st=P: Paragraph(escape(_safe(t, 600)), st)
    fmt = lambda v: "n/a" if v is None else f"{v:,}" if isinstance(v, int) else str(v)

    story = [Paragraph("ReelSense AI – Reel Analysis Report", H1)]
    if a["is_demo"]:
        story.append(Paragraph("<font color='#b45309'><b>DEMO / SAMPLE DATA – not from Instagram</b></font>", P))
    story += [p(f"Reel: {reel.get('url')}", SM), p(f"Creator: @{reel.get('username')}  |  Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", SM)]
    story.append(Paragraph("Key metrics", H2))
    t = Table([["Views", "Likes", "Comments", "Engagement rate"],
               [fmt(k["views"]), fmt(k["likes"]), fmt(k["comments"]), "n/a" if k["engagement_rate"] is None else f"{k['engagement_rate']}%"],
               ["Positive", "Negative", "Neutral", "Avg comment likes"],
               [f"{k['positive_pct']}%", f"{k['negative_pct']}%", f"{k['neutral_pct']}%", fmt(k["avg_comment_likes"])]],
              colWidths=[42 * mm] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")), ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eef2ff")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"), ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(t)

    story.append(Paragraph("Executive summary", H2))
    story.append(p(ins["executive_summary"]))

    d = Drawing(170 * mm, 55 * mm)
    ch = VerticalBarChart()
    ch.x, ch.y, ch.width, ch.height = 25, 20, 300, 90
    ch.data = [[a["sentiment"]["counts"]["positive"], a["sentiment"]["counts"]["negative"], a["sentiment"]["counts"]["neutral"]]]
    ch.categoryAxis.categoryNames = ["Positive", "Negative", "Neutral"]
    ch.bars[0].fillColor = colors.HexColor("#6366f1")
    ch.valueAxis.valueMin = 0
    ch.categoryAxis.labels.fontSize = 8
    ch.valueAxis.labels.fontSize = 8
    d.add(ch)
    story.append(Paragraph("Sentiment (analyzed comments)", H2))
    story.append(d)

    story.append(Paragraph("Aspect sentiment", H2))
    rows = [["Aspect", "Mentions", "Positive", "Negative", "Neutral"]] + [
        [r["aspect"], r["mentions"], r["positive"], r["negative"], r["neutral"]] for r in nlp["aspects"]]
    at = Table(rows, colWidths=[50 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm])
    at.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db"))]))
    story.append(at)

    story.append(Paragraph("Top keywords", H2))
    story.append(p(", ".join(f"{x['word']} ({x['count']})" for x in nlp["keywords"][:15]) or "None"))
    if nlp["hashtags"]:
        story.append(p("Hashtags in comments: " + ", ".join(f"{h['tag']} ({h['count']})" for h in nlp["hashtags"][:10]), SM))

    for title, key in (("Top positive feedback", "top_positive_feedback"), ("Top negative feedback", "top_negative_feedback")):
        story.append(Paragraph(title, H2))
        for x in ins[key] or []:
            story.append(p(f"- {x['theme']} ({x['count']} mentions): \"{x['example'] or ''}\""))
    story.append(Paragraph("Frequently asked questions", H2))
    for q in ins["frequently_asked_questions"] or []:
        story.append(p(f"- {q['question']}  (asked {q['count']}x)"))
    story.append(Paragraph("Recommendations", H2))
    for s in ins["improvement_suggestions"]:
        story.append(p(f"- {s['suggestion']}  [{s['evidence']}]"))
    story.append(Paragraph("Next content ideas", H2))
    for s in ins["next_content_ideas"]:
        story.append(p(f"- {s['idea']}  [{s['basis']}]"))

    story.append(Paragraph("Most-liked comments", H2))
    top = sorted([c for c in a["comments"] if not c["is_spam"]], key=lambda c: -(c.get("likes") or 0))[:8]
    ct = Table([["User", "Comment", "Sentiment", "Likes"]] + [[_safe(c.get("username") or "", 18), Paragraph(escape(_safe(c["text"], 110)), SM), c["sentiment"], c.get("likes") or 0] for c in top],
               colWidths=[32 * mm, 85 * mm, 24 * mm, 16 * mm])
    ct.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")), ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db"))]))
    story.append(ct)
    story.append(Spacer(1, 8))
    story.append(p(f"Models: {a['engines']['sentiment']} (sentiment); {a['engines']['emotion']} (emotion). {ins['method']}", SM))
    for w in a["warnings"]:
        story.append(p("Note: " + w, SM))

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                      title="ReelSense AI Report").build(story)
    return buf.getvalue()


EXPORTERS = {
    "csv": (to_csv, "text/csv; charset=utf-8", "csv"),
    "excel": (to_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "pdf": (to_pdf, "application/pdf", "pdf"),
}

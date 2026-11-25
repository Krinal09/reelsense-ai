"""Aspect-based sentiment.

Aspect *detection* uses a multilingual lexicon (EN / Hinglish / Hindi / Gujarati);
aspect *sentiment* is taken from the transformer prediction for the comment.
When a comment mentions several aspects separated by contrast words
("great sound but terrible price") it is split into clauses and each clause
is scored on its own by the same sentiment engine."""
from __future__ import annotations

import re

ASPECTS = {
    "Product": ["product", "earbud", "buds", "battery", "build", "bass", "sound", "audio quality", "mic", "design", "case",
                "device", "gadget", "feature", "connect", "bluetooth", "durab",
                "प्रोडक्ट", "बैटरी", "आवाज़", "आवाज", "साउंड", "माइक", "प्रोडक्ट",
                "પ્રોડક્ટ", "બેટરી", "અવાજ", "સાઉન્ડ"],
    "Creator": ["creator", "channel", "subscribe", "follow you", "your work", "your content", "you are", "you're the best",
                "genuine", "honest", "paid promo", "promotion", "sponsor", "biased", "one-sided", "tumhara", "tera content",
                "aapka kaam", "tune", "tumne", "bhai tu",
                "आपका काम", "आपका कंटेंट", "आप", "તમારું કામ", "તમારું કન્ટેન્ટ", "તમે"],
    "Video quality": ["video quality", "editing", "edit", "transition", "camera", "visual", "cinematic", "lighting", "4k",
                      "blur", "crisp", "resolution", "shot", "footage", "clean video", "quality of the video",
                      "एडिटिंग", "वीडियो की क्वालिटी", "धुंधली", "ધુંધળ", "વીડિયો ક્વોલિટી", "એડિટિંગ"],
    "Content": ["content", "review", "explain", "informative", "detail", "comparison", "tutorial", "boring", "pros and cons",
                "series", "next part", "topic", "helpful", "breakdown",
                "रिव्यू", "कंटेंट", "समझ", "રિવ્યુ", "કન્ટેન્ટ"],
    "Pricing": ["price", "pricing", "cost", "expensive", "overpriced", "cheap", "worth", "value for money", "paisa", "paise",
                "discount", "offer", "mehnga", "mehenga", "sasta", "zyada", "rs.", "₹", "$",
                "दाम", "कीमत", "महंगा", "सस्ता", "पैसे", "किमत", "કિંમત", "ભાવ", "મોંઘું", "સસ્તું", "પૈસા"],
    "Music": ["music", "song", "track", "bgm", "background", "beat", "soundtrack", "gaana", "gana",
              "म्यूज़िक", "म्यूजिक", "संगीत", "गाना", "સંગીત", "ગીત", "મ્યુઝિક"],
    "Service": ["service", "support", "delivery", "deliver", "warranty", "refund", "reply", "replied", "response", "customer care",
                "courier", "shipping", "ship", "return", "replace",
                "सर्विस", "डिलीवरी", "वारंटी", "સર્વિસ", "ડિલિવરી", "વોરંટી"],
}

_SPLIT = re.compile(r"\b(?:but|however|although|though|while|lekin|magar|par|parantu)\b|[.;!]\s+|,\s+|\bलेकिन\b|\bपर\b|\bપણ\b|\bપરંતુ\b", re.I)


def _compile():
    out = {}
    for asp, terms in ASPECTS.items():
        has_letters = lambda t: bool(re.search(r"[A-Za-z]", t))
        latin = [re.escape(t) for t in terms if has_letters(t)]
        other = [re.escape(t) for t in terms if not has_letters(t)]
        parts = []
        if latin:
            parts.append(r"(?<![A-Za-z])(?:" + "|".join(latin) + r")")
        if other:
            parts.append("(?:" + "|".join(other) + ")")
        out[asp] = re.compile("|".join(parts), re.I)
    return out


_RX = _compile()


def detect_aspects(text: str) -> list[str]:
    t = (text or "").lower()
    return [a for a, rx in _RX.items() if rx.search(t)]


def split_clauses(text: str) -> list[str]:
    parts = [p.strip() for p in _SPLIT.split(text or "") if p and p.strip()]
    return [p for p in parts if len(p) >= 3]

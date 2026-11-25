"""Sentiment + emotion classification with a built-in model (no external API, no tokens).
Trained at startup on a small bundled multilingual corpus (EN / Hinglish / Hindi / Gujarati / emoji)."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from .seed_corpus import EMOTION as SEED_EMOTION
from .seed_corpus import SENTIMENT as SEED_SENTIMENT
from .text import detect_language

SENTIMENTS = ["positive", "negative", "neutral"]
EMOTIONS = ["Happy", "Excited", "Angry", "Sad", "Frustrated", "Neutral"]



# ---------------------------------------------------------------- local fallback
@lru_cache(maxsize=1)
def _local_models():
    from .mini_ml import NaiveBayes, char_wb, word_feats

    def analyzer(t: str):
        return char_wb(t, 2, 5) + word_feats(t)

    def train(corpus: dict):
        X, y = [], []
        for label, items in corpus.items():
            X += items
            y += [label] * len(items)
        return NaiveBayes(analyzer, alpha=0.5, sharpness=6.0).fit(X, y)

    return train(SEED_SENTIMENT), train(SEED_EMOTION)


def _local_predict(model, texts: list[str]):
    out = []
    for t in texts:
        p = model.predict_proba(t)
        best = max(p, key=p.get)
        out.append((best, float(p[best]), p))
    return out


def _clip(t: str) -> str:
    t = (t or "").strip()
    return t[:400] if t else "."


class SentimentEngine:
    """Runs sentiment + emotion over comments and yields progress."""

    BATCH = 32
    MODEL = "built-in model (char + word n-gram Naive Bayes, trained at startup)"

    def __init__(self, deadline: float | None = None):
        self.deadline = deadline

    def _sentiment_batch(self, texts: list[str]):
        sent_model, _ = _local_models()
        return [(l, c, p, "local") for l, c, p in _local_predict(sent_model, [_clip(t) for t in texts])]

    def _emotion_batch(self, texts: list[str]):
        _, emo_model = _local_models()
        return [(l, c, "local") for l, c, _ in _local_predict(emo_model, [_clip(t) for t in texts])]

    def run(self, comments: list[dict]):
        """Generator: yields progress dicts, returns {comment_id: result}."""
        n = len(comments)
        out: dict = {}
        for c in comments:
            code, name = detect_language(c["text"])
            out[c["id"]] = {"language_code": code, "language": name}
        ids = [c["id"] for c in comments]
        texts = {c["id"]: c["text"] for c in comments}
        yield {"type": "progress", "stage": "sentiment", "percent": 50, "message": f"Classifying sentiment for {n} comments…"}
        batches = [ids[i:i + self.BATCH] for i in range(0, n, self.BATCH)]
        for k, b in enumerate(batches, 1):
            for cid, (lab, conf, probs, eng) in zip(b, self._sentiment_batch([texts[i] for i in b])):
                out[cid].update(sentiment=lab, confidence=round(conf, 4), sentiment_engine=eng)
            for cid, (emo, conf, eng) in zip(b, self._emotion_batch([texts[i] for i in b])):
                out[cid].update(emotion=emo, emotion_confidence=round(conf, 4), emotion_engine=eng)
            yield {"type": "progress", "stage": "emotion", "percent": 50 + int(30 * k / len(batches)), "message": f"Sentiment & emotion: {min(n, k * self.BATCH)}/{n} comments"}

        for r in out.values():  # an emotion can't contradict a confident sentiment
            if r["sentiment"] == "positive" and r["emotion"] in ("Angry", "Sad", "Frustrated") and r["confidence"] > 0.6:
                r["emotion"], r["emotion_confidence"] = "Happy", round(r["confidence"] * 0.7, 4)
            if r["sentiment"] == "negative" and r["emotion"] in ("Happy", "Excited") and r["confidence"] > 0.6:
                r["emotion"], r["emotion_confidence"] = "Frustrated", round(r["confidence"] * 0.7, 4)
        return out

    def engine_summary(self) -> dict:
        return {"sentiment": self.MODEL, "emotion": self.MODEL, "fallback_used": False}

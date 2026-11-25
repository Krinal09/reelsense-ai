"""Tiny dependency-light ML toolkit (numpy only) – replaces scikit-learn so the Vercel
function stays small. Provides TF-IDF, cosine similarity, NMF topics and Naive Bayes."""
from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

_WORD = re.compile(r"[\wऀ-ॿ઀-૿]+", re.UNICODE)


def char_wb(text: str, lo: int, hi: int) -> list[str]:
    out: list[str] = []
    for w in (text or "").lower().split():
        w = f" {w} "
        for n in range(lo, hi + 1):
            if len(w) >= n:
                out.extend(w[i:i + n] for i in range(len(w) - n + 1))
    return out


def word_feats(text: str, lo: int = 1, hi: int = 2) -> list[str]:
    toks = _WORD.findall((text or "").lower())
    out = []
    for n in range(lo, hi + 1):
        out.extend("w:" + " ".join(toks[i:i + n]) for i in range(len(toks) - n + 1))
    return out


class Tfidf:
    """Dense TF-IDF (sublinear tf, smooth idf, L2 rows). Intended for ≤ ~1000 short docs."""

    def __init__(self, analyzer, min_df: int = 1, max_df: float = 1.0):
        self.analyzer, self.min_df, self.max_df = analyzer, min_df, max_df
        self.vocab: list[str] = []

    def fit_transform(self, docs: list[str]) -> np.ndarray:
        feats = [Counter(self.analyzer(d)) for d in docs]
        df: Counter = Counter()
        for f in feats:
            df.update(f.keys())
        n = len(docs)
        self.vocab = sorted(t for t, c in df.items() if c >= self.min_df and c <= self.max_df * n)
        idx = {t: i for i, t in enumerate(self.vocab)}
        idf = np.array([math.log((1 + n) / (1 + df[t])) + 1 for t in self.vocab], dtype=np.float32)
        X = np.zeros((n, len(self.vocab)), dtype=np.float32)
        for r, f in enumerate(feats):
            for t, c in f.items():
                j = idx.get(t)
                if j is not None:
                    X[r, j] = 1 + math.log(c)
        X *= idf
        norm = np.linalg.norm(X, axis=1, keepdims=True)
        norm[norm == 0] = 1
        return X / norm


def cosine_matrix(X: np.ndarray) -> np.ndarray:
    return X @ X.T  # rows are already L2-normalised


def nmf(X: np.ndarray, k: int, iters: int = 250, seed: int = 0):
    """Multiplicative-update NMF (Frobenius). Returns W (docs×k), H (k×terms)."""
    rng = np.random.default_rng(seed)
    n, m = X.shape
    W = rng.random((n, k), dtype=np.float32) + 0.1
    H = rng.random((k, m), dtype=np.float32) + 0.1
    eps = 1e-9
    for _ in range(iters):
        H *= (W.T @ X) / (W.T @ W @ H + eps)
        W *= (X @ H.T) / (W @ H @ H.T + eps)
    return W, H


class NaiveBayes:
    """Multinomial Naive Bayes over sub-linear feature counts with calibrated scores."""

    def __init__(self, analyzer, alpha: float = 0.5, sharpness: float = 5.0):
        self.analyzer, self.alpha, self.sharpness = analyzer, alpha, sharpness
        self.classes: list[str] = []

    def fit(self, docs: list[str], labels: list[str]):
        self.classes = sorted(set(labels))
        counts = {c: Counter() for c in self.classes}
        prior = Counter(labels)
        vocab: set[str] = set()
        for d, y in zip(docs, labels):
            for f, c in Counter(self.analyzer(d)).items():
                counts[y][f] += 1 + math.log(c)
                vocab.add(f)
        V = len(vocab)
        self.logp, self.default = {}, {}
        for c in self.classes:
            tot = sum(counts[c].values()) + self.alpha * V
            self.logp[c] = {f: math.log((counts[c][f] + self.alpha) / tot) for f in vocab}
            self.default[c] = math.log(self.alpha / tot)
        self.logprior = {c: math.log(prior[c] / len(labels)) for c in self.classes}
        self.vocab = vocab
        return self

    def predict_proba(self, text: str) -> dict[str, float]:
        feats = {f: 1 + math.log(c) for f, c in Counter(self.analyzer(text)).items() if f in self.vocab}
        W = sum(feats.values())
        if not W:
            z = {c: self.logprior[c] for c in self.classes}
        else:
            k = self.sharpness
            z = {c: self.logprior[c] + k * sum(w * self.logp[c][f] for f, w in feats.items()) / W for c in self.classes}
        m = max(z.values())
        e = {c: math.exp(v - m) for c, v in z.items()}
        s = sum(e.values())
        return {c: v / s for c, v in e.items()}

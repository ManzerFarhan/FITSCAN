"""Metric helpers: CER / WER (Levenshtein), retrieval metrics."""
from __future__ import annotations


def levenshtein(a: list | str, b: list | str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    ref, hyp = " ".join(ref.split()), " ".join(hyp.split())
    return levenshtein(ref, hyp) / max(len(ref), 1)


def wer(ref: str, hyp: str) -> float:
    r, h = ref.split(), hyp.split()
    return levenshtein(r, h) / max(len(r), 1)


def precision_recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> tuple[float, float]:
    top = retrieved[:k]
    hits = sum(1 for x in top if x in relevant)
    return hits / k, hits / max(len(relevant), 1)


def mrr(retrieved: list[str], relevant: set[str]) -> float:
    for i, x in enumerate(retrieved, 1):
        if x in relevant:
            return 1 / i
    return 0.0

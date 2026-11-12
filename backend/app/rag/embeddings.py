"""Text embeddings (FR-AI-7, P3-03).

Primary: sentence-transformers (all-MiniLM-L6-v2). Fallback when it is not installed: a small
TF-IDF embedder (pure numpy) fitted on the KB, so retrieval still works offline / on CPU-only installs.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Protocol

import numpy as np

ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> np.ndarray: ...


def _tokens(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]


class TfidfEmbedder:
    name = "tfidf"

    def __init__(self, vocab: dict[str, int] | None = None, idf: list[float] | None = None):
        self.vocab = vocab or {}
        self.idf = np.array(idf or [], dtype=np.float32)

    def fit(self, texts: list[str]) -> "TfidfEmbedder":
        df: Counter = Counter()
        for t in texts:
            df.update(set(_tokens(t)))
        self.vocab = {tok: i for i, tok in enumerate(sorted(df))}
        n = len(texts)
        self.idf = np.array([math.log((1 + n) / (1 + df[t])) + 1 for t in sorted(df)], dtype=np.float32)
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for r, t in enumerate(texts):
            for tok, c in Counter(_tokens(t)).items():
                j = self.vocab.get(tok)
                if j is not None:
                    out[r, j] = (1 + math.log(c)) * self.idf[j]
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-9)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"vocab": self.vocab, "idf": self.idf.tolist()}), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "TfidfEmbedder":
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(d["vocab"], d["idf"])


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(ST_MODEL)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype=np.float32)


def sentence_transformers_available() -> bool:
    try:
        import sentence_transformers  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False

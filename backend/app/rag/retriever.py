"""Parameter-aware retrieval (P3-05, BR-11). Returns nothing rather than weak matches, so callers can
say "no source found" instead of inventing (BR-11)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel

from app.rag import vector_store
from app.utils import dictionaries

MIN_SCORE = {"tfidf": 0.08, "sentence-transformers": 0.30}
PARAM_BOOST = 0.25


class Source(BaseModel):
    chunk_id: int
    title: str
    source: str
    url: str
    text: str
    score: float


@lru_cache
def get_store() -> vector_store.VectorStore:
    return vector_store.load()


def retrieve(query: str, k: int = 4, parameter_id: str | None = None) -> list[Source]:
    store = get_store()
    q = query
    if parameter_id and (p := dictionaries.parameters().get(parameter_id)):
        q = f"{p['canonical_name']} {' '.join(p['synonyms'][:4])} {query}"
    hits = store.search(q, k=max(k * 3, 8))
    threshold = MIN_SCORE.get(store.embedder.name, 0.1)
    ranked: list[Source] = []
    for chunk, score in hits:
        s = score + (PARAM_BOOST if parameter_id and parameter_id in chunk.parameters else 0.0)
        if s >= threshold:
            ranked.append(Source(chunk_id=chunk.chunk_id, title=chunk.title, source=chunk.source, url=chunk.url,
                                 text=chunk.text, score=round(s, 4)))
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:k]

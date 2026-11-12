"""Vector index (FR-AI-7, P3-04): FAISS IndexFlatIP when installed, numpy dot-product otherwise.
Persisted under data/faiss_index/ (gitignored); rebuilt automatically if missing."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.rag.embeddings import SentenceTransformerEmbedder, TfidfEmbedder, sentence_transformers_available
from app.rag.ingest import Chunk, chunk_documents, load_documents

INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "faiss_index"


class VectorStore:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder):
        self.chunks = chunks
        self.embedder = embedder
        self.vectors = vectors.astype(np.float32)
        self._faiss = None
        try:
            import faiss  # type: ignore

            self._faiss = faiss.IndexFlatIP(self.vectors.shape[1])
            self._faiss.add(self.vectors)
        except Exception:
            pass

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        q = self.embedder.encode([query]).astype(np.float32)
        if self._faiss is not None:
            scores, idx = self._faiss.search(q, min(k, len(self.chunks)))
            return [(self.chunks[i], float(s)) for i, s in zip(idx[0], scores[0]) if i >= 0]
        scores = (self.vectors @ q[0])
        order = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in order]


def build(index_dir: Path = INDEX_DIR, prefer_st: bool = True) -> VectorStore:
    chunks = chunk_documents(load_documents())
    texts = [f"{c.title}. {c.text}" for c in chunks]
    if prefer_st and sentence_transformers_available():
        embedder = SentenceTransformerEmbedder()
    else:
        embedder = TfidfEmbedder().fit(texts)
    vectors = embedder.encode(texts)
    index_dir.mkdir(parents=True, exist_ok=True)
    np.save(index_dir / "vectors.npy", vectors)
    (index_dir / "chunks.json").write_text(json.dumps([c.model_dump() for c in chunks], indent=1), encoding="utf-8")
    (index_dir / "meta.json").write_text(json.dumps({"embedder": embedder.name, "count": len(chunks)}), encoding="utf-8")
    if isinstance(embedder, TfidfEmbedder):
        embedder.save(index_dir / "tfidf.json")
    return VectorStore(chunks, vectors, embedder)


def load(index_dir: Path = INDEX_DIR) -> VectorStore:
    meta_p = index_dir / "meta.json"
    if not meta_p.exists():
        return build(index_dir)
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    chunks = [Chunk(**c) for c in json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))]
    if meta["embedder"] == "tfidf":
        embedder = TfidfEmbedder.load(index_dir / "tfidf.json")
    elif sentence_transformers_available():
        embedder = SentenceTransformerEmbedder()
    else:
        return build(index_dir, prefer_st=False)
    return VectorStore(chunks, np.load(index_dir / "vectors.npy"), embedder)

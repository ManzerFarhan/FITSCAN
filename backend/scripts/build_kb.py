"""Build the RAG index from data/kb (P3-04). Usage: python scripts/build_kb.py [--tfidf]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.vector_store import build  # noqa: E402

if __name__ == "__main__":
    store = build(prefer_st="--tfidf" not in sys.argv)
    print(f"Indexed {len(store.chunks)} chunks with {store.embedder.name}")

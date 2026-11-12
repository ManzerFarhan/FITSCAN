"""KB ingestion: load source docs (kb_seed.yaml + *.md with front matter) and chunk them (FR-AI-7, P3-02)."""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
MAX_WORDS = 140


class KBDoc(BaseModel):
    title: str
    source: str
    url: str
    parameters: list[str] = Field(default_factory=list)
    text: str


class Chunk(BaseModel):
    chunk_id: int
    title: str
    source: str
    url: str
    parameters: list[str]
    text: str


def load_documents(kb_dir: Path = KB_DIR) -> list[KBDoc]:
    docs: list[KBDoc] = []
    # kb_seed.yaml first, then any other kb_*.yaml (e.g. kb_blood_tests.yaml) in name order.
    files = sorted(kb_dir.glob("kb_*.yaml"), key=lambda p: (p.name != "kb_seed.yaml", p.name))
    for f in files:
        docs += [KBDoc(**d) for d in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("documents", [])]
    for md in sorted(kb_dir.glob("*.md")):
        raw = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
            docs.append(KBDoc(text=m.group(2).strip(), **meta))
    return docs


def chunk_documents(docs: list[KBDoc], max_words: int = MAX_WORDS) -> list[Chunk]:
    chunks: list[Chunk] = []
    for d in docs:
        buf: list[str] = []
        for para in [p.strip() for p in d.text.split("\n") if p.strip()]:
            if buf and len(" ".join(buf + [para]).split()) > max_words:
                chunks.append(Chunk(chunk_id=len(chunks), title=d.title, source=d.source, url=d.url,
                                    parameters=d.parameters, text=" ".join(buf)))
                buf = []
            buf.append(para)
        if buf:
            chunks.append(Chunk(chunk_id=len(chunks), title=d.title, source=d.source, url=d.url,
                                parameters=d.parameters, text=" ".join(buf)))
    return chunks

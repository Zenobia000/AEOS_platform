"""Load the pilot tenant's knowledge as a single markdown blob.

W1 keeps this dumb on purpose: one customer's FAQ/SOP fits in context, so we
feed the whole thing as a cached system prompt instead of standing up pgvector.
RAG only earns its place at W2 when knowledge exceeds the context window.
"""

from __future__ import annotations

from pathlib import Path


def load_knowledge(path: str | Path) -> str:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"知識檔為空：{path}")
    return text

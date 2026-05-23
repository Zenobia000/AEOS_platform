"""StubEmbeddingClient 行為測試 — deterministic + L2-normalized + 1024-dim."""

from __future__ import annotations

import math

from app.embeddings import StubEmbeddingClient
from app.embeddings.client import EmbeddingResult


async def test_embed_returns_correct_dim() -> None:
    client = StubEmbeddingClient()
    result: EmbeddingResult = await client.embed(["hello"])

    assert len(result) == 1
    assert len(result.vectors[0]) == 1024


async def test_embed_l2_normalized() -> None:
    client = StubEmbeddingClient()
    result = await client.embed(["customer service question"])
    norm = math.sqrt(sum(x * x for x in result.vectors[0]))
    assert abs(norm - 1.0) < 1e-6


async def test_embed_deterministic() -> None:
    """同 text 永遠回同向量."""
    client = StubEmbeddingClient()
    r1 = await client.embed(["退貨期限"])
    r2 = await client.embed(["退貨期限"])
    assert r1.vectors == r2.vectors


async def test_embed_different_texts_different_vectors() -> None:
    client = StubEmbeddingClient()
    r = await client.embed(["A", "B"])
    assert r.vectors[0] != r.vectors[1]


async def test_embed_batch() -> None:
    client = StubEmbeddingClient()
    texts = ["a", "b", "c", "d"]
    result = await client.embed(texts)
    assert len(result.vectors) == 4
    assert all(len(v) == 1024 for v in result.vectors)


async def test_embed_model_label() -> None:
    client = StubEmbeddingClient(model="custom-stub")
    result = await client.embed(["x"])
    assert result.model == "custom-stub"


async def test_embed_total_tokens_approximates_length() -> None:
    client = StubEmbeddingClient()
    result = await client.embed(["abc", "defgh"])
    # Stub 用 char count 近似 token count
    assert result.total_tokens == 3 + 5

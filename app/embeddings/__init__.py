"""Embedding 子系統 — 把 text 轉成 1024-dim vector 給 pgvector.

依 db-schema.md §4.2 + MC-008 + skills/customer-service/faq-respond/v1.0.0/manifest.yaml：
- voyage-3-lite (1024-dim) 是 Phase 1 預設
- 介面層 (EmbeddingClient) 不綁特定 vendor；測試可注入 StubEmbeddingClient

Phase 1 簡化：
- StubEmbeddingClient: 用 SHA256 hash 產 deterministic 假向量（測試 / dev）
- VoyageEmbeddingClient: 真正打 voyage API（待 voyage API key 後可跑）
"""

from app.embeddings.client import EmbeddingClient, EmbeddingResult, StubEmbeddingClient

__all__ = ["EmbeddingClient", "EmbeddingResult", "StubEmbeddingClient"]

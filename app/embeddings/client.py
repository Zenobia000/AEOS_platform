"""EmbeddingClient interface + Stub 實作.

依 ADR-0001 風格：薄層 abstraction，application 層不直接依賴 vendor。
Phase 1 預設 voyage-3-lite (1024 dim)；StubEmbeddingClient 給 test/dev 用。
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from app.db.models.knowledge_card import EMBEDDING_DIM

DEFAULT_MODEL = "voyage-3-lite"


@dataclass(frozen=True)
class EmbeddingResult:
    """`embed()` 回傳 — 一個 batch 內 N 個 text 的向量 + 模型名稱."""

    vectors: tuple[tuple[float, ...], ...]
    model: str
    total_tokens: int = 0  # provider 回 usage 時填；test stub 不填

    def __len__(self) -> int:
        return len(self.vectors)


class EmbeddingClient(ABC):
    """Abstract embedding client. Phase 1: VoyageEmbeddingClient + StubEmbeddingClient."""

    @abstractmethod
    async def embed(
        self,
        texts: Sequence[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        """把 N 個 text 一次性轉成 N 個 1024-dim 向量."""
        raise NotImplementedError


class StubEmbeddingClient(EmbeddingClient):
    """測試用 deterministic embedding — 用 SHA256 hash 產假向量.

    保證：
    - 同 text 永遠回同向量（deterministic）
    - 不同 text 高機率不同向量
    - 向量 L2 norm = 1（適合 cosine similarity）
    """

    def __init__(self, *, dim: int = EMBEDDING_DIM, model: str = "stub-sha256") -> None:
        self._dim = dim
        self._model = model

    async def embed(
        self,
        texts: Sequence[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        vectors = tuple(self._hash_to_vector(t) for t in texts)
        return EmbeddingResult(
            vectors=vectors,
            model=model or self._model,
            total_tokens=sum(len(t) for t in texts),
        )

    def _hash_to_vector(self, text: str) -> tuple[float, ...]:
        # 用 SHA256 hash 64 bytes 反覆延伸到 dim*4 bytes (float32 大小)
        # 然後每 4 bytes 轉成一個 float，L2 normalize
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        needed = self._dim * 4
        buf = bytearray()
        counter = 0
        while len(buf) < needed:
            buf.extend(hashlib.sha256(seed + counter.to_bytes(4, "little")).digest())
            counter += 1
        raw = bytes(buf[:needed])

        floats: list[float] = []
        for i in range(self._dim):
            chunk = raw[i * 4 : i * 4 + 4]
            # signed int32 → [-1, 1]
            n = int.from_bytes(chunk, "little", signed=True)
            floats.append(n / 2**31)

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return tuple(x / norm for x in floats)

"""Worker process entrypoint — 跑 polling loop 直到 SIGINT/SIGTERM.

執行：
    uv run python -m app.worker

環境變數（透過 app/config.py 載入）:
- ANTHROPIC_API_KEY        — 若有設則用 AnthropicClient；否則用 StubLLM（不會
                              成功呼叫真實 LLM，僅 worker loop 可起 + draft/
                              test_run 會 fail，適合 dev demo 觀察 polling）
- DATABASE_URL / database_url — 從 .env 或 env var 載入（見 app/config.py）
- WORKER_INTERVAL_S        — polling 間隔秒（預設 1.0）

handles:
- SIGINT / SIGTERM → 設 stop_event，當前 iteration 完成後 graceful shutdown
- KeyboardInterrupt 同上

對應 MC-009 + MC-010 + MC-011 + S3 TestSet poll cycle。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

import httpx

from app.agent import InternalToolRegistry
from app.agent.builtin_tools import register_builtins
from app.db.session import get_sessionmaker
from app.llm.client import LLMClient, LLMResponse, LLMUsage
from app.skill import SkillLoader
from app.worker.draft_processor import DraftProcessor
from app.worker.loop import run_loop
from app.worker.outbound_processor import OutboundProcessor
from app.worker.test_runner import TestSetRunner

logger = logging.getLogger("aeos.worker")


class _StubLLM(LLMClient):
    """Fallback when ANTHROPIC_API_KEY missing — worker 仍能起，但每次 turn
    回固定字串。用於本機 demo 觀察 polling 機制；prod 必須設真 key。
    """

    async def complete(self, **_kwargs: Any) -> LLMResponse:
        return LLMResponse(
            text="[StubLLM: ANTHROPIC_API_KEY not set — set env var for real LLM]",
            tool_uses=[],
            stop_reason="end_turn",
            usage=LLMUsage(input_tokens=0, output_tokens=0),
            model="stub",
        )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_llm() -> LLMClient:
    """有 API key 用 AnthropicClient；沒有就 Stub 並 warn."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY not set — falling back to StubLLM. "
            "Drafts / test runs will not produce real answers. "
            "Set ANTHROPIC_API_KEY for real LLM."
        )
        return _StubLLM()
    from app.llm.anthropic_client import AnthropicClient

    logger.info("LLM client: AnthropicClient")
    return AnthropicClient(api_key=api_key)


async def _async_main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    interval = float(os.environ.get("WORKER_INTERVAL_S", "1.0"))
    logger.info(
        "AEOS worker starting (interval=%.1fs); poll cycles: idle / draft / outbound / test_run",
        interval,
    )

    llm = _build_llm()
    registry = InternalToolRegistry()
    register_builtins(registry)
    skill_loader = SkillLoader(root=_repo_root() / "skills")

    draft_processor = DraftProcessor(llm=llm, skill_loader=skill_loader, registry=registry)
    test_set_runner = TestSetRunner(llm=llm, skill_loader=skill_loader)

    sessionmaker = get_sessionmaker()

    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        # Windows / restricted envs 不支援 → 仍可 KeyboardInterrupt
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        outbound_processor = OutboundProcessor(http_client=http_client)
        try:
            await run_loop(
                sessionmaker,
                draft_processor=draft_processor,
                outbound_processor=outbound_processor,
                test_set_runner=test_set_runner,
                interval_s=interval,
                stop_event=stop_event,
            )
        finally:
            logger.info("AEOS worker stopped (graceful shutdown)")


def main() -> None:
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

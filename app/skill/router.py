"""SkillRouter — 決定 inbound message 由哪個 skill 處理（CR-0001 / ADR-0013）.

依 ADR-0013 hybrid routing 策略：
- 4 種 rule type: keyword / llm_intent / channel_match / explicit
- priority ASC 排序逐一評估
- 全 miss → fallback to is_default=true binding
- 無 default → raise NoSkillBoundError

設計原則：
- 不直接依賴 DraftProcessor；只回 SkillVersion，由 caller 接 SkillLoader
- LLMClient 可選注入；無 client 時 llm_intent rule 自動降為 always-miss
- 每次決策寫 audit_log (routing.matched / routing.fallback / routing.error)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.skill import Skill
from app.db.models.skill_binding import SkillBinding
from app.db.models.skill_version import SkillVersion
from app.llm.client import LLMClient, LLMMessage
from app.services import audit

logger = logging.getLogger(__name__)

# 預設 LLM intent classify 模型（ADR-0013 Haiku 4.5 — 便宜快）
DEFAULT_INTENT_MODEL = "claude-haiku-4-5-20251001"


class NoSkillBoundError(Exception):
    """employee 沒有 default skill 且所有 rule 都 miss — 視為配置錯誤。"""


@dataclass(frozen=True)
class RoutingDecision:
    """SkillRouter.route() 回傳結果。"""

    skill_version: SkillVersion
    skill_slug: str  # e.g. 'customer-service/faq-respond' (for SkillLoader.load)
    skill_version_str: str  # e.g. '1.0.0' (semver)
    binding_id: uuid.UUID
    matched_rule_type: str  # 'keyword' / 'llm_intent' / ... / 'default_fallback'
    matched_rule: dict[str, Any] | None  # 命中的 routing_rule（fallback 時為 None）


class SkillRouter:
    """Routing message → SkillVersion 的核心服務。"""

    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient | None = None,
        intent_model: str = DEFAULT_INTENT_MODEL,
    ) -> None:
        self._session = session
        self._llm = llm_client
        self._intent_model = intent_model

    async def route(
        self,
        *,
        message: str,
        employee_id: uuid.UUID,
        tenant_id: uuid.UUID,
        channel_id: str | None = None,
    ) -> RoutingDecision:
        """決定此 message 走哪個 skill。

        Args:
            message: 使用者訊息純文字
            employee_id: 此 conversation 的 employee
            tenant_id: tenant scope（給 audit）
            channel_id: channel_match rule 評估用（無則跳過該類 rule）

        Returns:
            RoutingDecision（含 SkillVersion + 命中資訊）

        Raises:
            NoSkillBoundError: employee 無 default 且全 rule miss
        """
        bindings = await self._load_bindings(employee_id)
        if not bindings:
            raise NoSkillBoundError(f"employee {employee_id} has no skill_binding")

        # 1) Priority sort（routing_rule.priority 預設 100 — 比 default 99 大表沒寫就排最後）
        sorted_bindings = sorted(
            bindings,
            key=lambda b: (
                int(b.routing_rule.get("priority", 100)),
                # 同 priority 時，is_default 排最後（給普通 rule 優先機會）
                1 if b.is_default else 0,
            ),
        )

        # 2) 逐一評估
        for binding in sorted_bindings:
            rule = binding.routing_rule or {}
            rule_type = rule.get("type")
            if not rule_type:
                continue  # 沒 type 視為 no-op；要走 default 也走 §3 fallback

            try:
                matched = await self._evaluate(rule, message, channel_id=channel_id)
            except Exception as exc:
                logger.warning("routing.evaluator_error type=%s err=%s", rule_type, exc)
                await audit.emit(
                    self._session,
                    event_type="routing.error",
                    tenant_id=tenant_id,
                    resource_type="skill_binding",
                    resource_id=str(binding.id),
                    payload={"rule_type": rule_type, "error": str(exc)},
                )
                continue

            if matched:
                sv, slug = await self._fetch_skill_version_with_slug(binding.skill_version_id)
                await audit.emit(
                    self._session,
                    event_type="routing.matched",
                    tenant_id=tenant_id,
                    resource_type="skill_version",
                    resource_id=str(sv.id),
                    payload={
                        "binding_id": str(binding.id),
                        "rule_type": rule_type,
                        "rule": rule,
                    },
                )
                return RoutingDecision(
                    skill_version=sv,
                    skill_slug=slug,
                    skill_version_str=normalize_version_for_loader(sv.version),
                    binding_id=binding.id,
                    matched_rule_type=rule_type,
                    matched_rule=rule,
                )

        # 3) Fallback to default
        default_binding = next((b for b in bindings if b.is_default), None)
        if default_binding is None:
            raise NoSkillBoundError(
                f"employee {employee_id} has no is_default binding and all rules missed"
            )

        sv, slug = await self._fetch_skill_version_with_slug(default_binding.skill_version_id)
        await audit.emit(
            self._session,
            event_type="routing.fallback",
            tenant_id=tenant_id,
            resource_type="skill_version",
            resource_id=str(sv.id),
            payload={"binding_id": str(default_binding.id)},
        )
        return RoutingDecision(
            skill_version=sv,
            skill_slug=slug,
            skill_version_str=normalize_version_for_loader(sv.version),
            binding_id=default_binding.id,
            matched_rule_type="default_fallback",
            matched_rule=None,
        )

    # ── Evaluators ──────────────────────────────────────

    async def _evaluate(
        self,
        rule: dict[str, Any],
        message: str,
        *,
        channel_id: str | None,
    ) -> bool:
        """Dispatch by rule.type → 對應 evaluator function。"""
        rule_type = rule.get("type")
        params = rule.get("params") or {}

        if rule_type == "keyword":
            return _eval_keyword(message, params)
        if rule_type == "channel_match":
            return _eval_channel_match(channel_id, params)
        if rule_type == "explicit":
            return _eval_explicit(params)
        if rule_type == "llm_intent":
            return await self._eval_llm_intent(message, params)

        # 未知 type 視為 miss（避免 admin 拼錯 type 全部 fallback）
        logger.warning("routing.unknown_rule_type type=%s", rule_type)
        return False

    async def _eval_llm_intent(self, message: str, params: dict[str, Any]) -> bool:
        """LLM intent classify — 沒注入 llm_client 自動 miss。"""
        if self._llm is None:
            return False
        intents = params.get("intents") or []
        if not intents:
            return False
        prompt = (
            "判斷以下使用者訊息屬於哪個 intent。\n"
            f"可選 intent: {', '.join(intents)}\n"
            "若不屬於上述任一個，回 'none'。\n"
            "**只回 intent 名稱本身，不要解釋。**\n\n"
            f"訊息：{message}"
        )
        try:
            resp = await self._llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                model=self._intent_model,
                max_tokens=32,
                temperature=0.0,
            )
            answer = (resp.text or "").strip().lower()
            return any(intent.lower() in answer for intent in intents)
        except Exception as exc:
            logger.warning("routing.llm_intent_error err=%s", exc)
            return False

    # ── Helpers ─────────────────────────────────────────

    async def _load_bindings(self, employee_id: uuid.UUID) -> list[SkillBinding]:
        result = await self._session.execute(
            select(SkillBinding).where(SkillBinding.employee_id == employee_id)
        )
        return list(result.scalars())

    async def _fetch_skill_version_with_slug(
        self, skill_version_id: uuid.UUID
    ) -> tuple[SkillVersion, str]:
        """JOIN Skill 拿 slug，給 caller 餵 SkillLoader.load(slug, version_str)。"""
        result = await self._session.execute(
            select(SkillVersion, Skill.slug)
            .join(Skill, SkillVersion.skill_id == Skill.id)
            .where(SkillVersion.id == skill_version_id)
        )
        row = result.one()
        return row[0], row[1]


def normalize_version_for_loader(db_version: str) -> str:
    """DB SkillVersion.version (e.g. '1.0.0') → SkillLoader 要的 'v1.0.0' 目錄名。

    skills/<slug>/<v1.0.0>/ 目錄帶 'v' 前綴；DB 存 semver 不帶。
    若 db_version 已經帶 'v' 則原樣返回（容錯）。
    """
    if not db_version:
        return db_version
    return db_version if db_version.startswith("v") else f"v{db_version}"


# ── Pure-function evaluators (testable independently) ──


def _eval_keyword(message: str, params: dict[str, Any]) -> bool:
    """任一 keyword 子字串命中即 match。case-insensitive。"""
    keywords = params.get("keywords") or []
    if not keywords:
        return False
    lower_msg = message.lower()
    return any(kw.lower() in lower_msg for kw in keywords if kw)


def _eval_channel_match(channel_id: str | None, params: dict[str, Any]) -> bool:
    """channel_id 完全相等比對。"""
    expected = params.get("channel_id")
    if not expected or not channel_id:
        return False
    return bool(channel_id == expected)


def _eval_explicit(params: dict[str, Any]) -> bool:
    """純語意 disable — `{"never_match": true}` → 永遠不 match."""
    if params.get("never_match"):
        return False
    return False  # explicit type 預設亦不 match

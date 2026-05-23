"""AgentContext — Frozen Runtime snapshot per turn.

依 MC-009 (Employee Runtime) + engineering-charter §2 (Frozen Runtime):
- conversation 開始時把 employee.runtime_snapshot 釘住，整段對話不會
  因 employee config 變更而改變行為
- 本 dataclass 是 immutable 的「對話一回合」context
- DB session 由外層注入（hooks 可寫 audit log / 讀 policy）
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

ToolDecisionAction = Literal["allow", "block"]


@dataclass(frozen=True)
class ToolDecision:
    """Policy hook 對某個 tool call 的決策."""

    action: ToolDecisionAction
    reason: str = ""
    rule_name: str | None = None

    @classmethod
    def allow(cls, reason: str = "") -> ToolDecision:
        return cls(action="allow", reason=reason)

    @classmethod
    def block(cls, reason: str, rule_name: str | None = None) -> ToolDecision:
        return cls(action="block", reason=reason, rule_name=rule_name)

    @property
    def is_allowed(self) -> bool:
        return self.action == "allow"


@dataclass(frozen=True)
class AgentContext:
    """單次 turn 的不可變 context.

    依 MC-009：每次對話一回合（user message → AI response）新建一個
    context，整個 turn 期間欄位不可變。Hook 可讀但不可寫。
    """

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    employee_id: uuid.UUID
    employee_version: str
    skill_version_id: uuid.UUID | None
    runtime_snapshot: Mapping[str, Any] = field(default_factory=dict)
    session: AsyncSession | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

"""PolicyHook — 對 tool call 做 MC-006 Tool Registry policy 評估.

Phase 1 簡化策略：
- 從 ctx.runtime_snapshot['policy_refs'] 取出該 employee 適用的 policy
- 每個 policy 是 YAML rule（DB 表 tool_policy.rule_yaml）
- Phase 1 不跑完整 DSL，只支援兩種 rule 形態：
  1. `block_risk_tier`: 阻擋指定 risk_tier 的 tool 呼叫
  2. `block_tool`: 阻擋指定 tool slug

完整 YAML DSL 與 condition 邏輯運算符（MC-006）是 Phase 2 工作。
"""

from __future__ import annotations

from typing import Any

import yaml
from sqlalchemy import select

from app.agent.context import AgentContext, ToolDecision
from app.agent.hook import AgentHook
from app.db.models.tool import Tool
from app.db.models.tool_policy import ToolPolicy


class PolicyHook(AgentHook):
    """讀 DB tool_policy（按 priority 排序）+ runtime_snapshot 限制做評估."""

    async def before_tool_call(
        self,
        ctx: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolDecision:
        if ctx.session is None:
            return ToolDecision.allow()

        # 取 tool risk_tier
        tool_row = (
            await ctx.session.execute(select(Tool).where(Tool.slug == tool_name))
        ).scalar_one_or_none()
        if tool_row is None:
            return ToolDecision.block(
                reason=f"unknown tool slug: {tool_name}",
                rule_name="tool_not_registered",
            )
        if not tool_row.enabled:
            return ToolDecision.block(
                reason=f"tool {tool_name} is disabled",
                rule_name="tool_disabled",
            )

        # 取適用該 tenant 的 policies（含 global），依 priority 高到低
        policies = (
            (
                await ctx.session.execute(
                    select(ToolPolicy)
                    .where(ToolPolicy.enabled.is_(True))
                    .order_by(ToolPolicy.priority.desc())
                )
            )
            .scalars()
            .all()
        )

        for policy in policies:
            decision = _evaluate_policy(policy, tool_row.slug, tool_row.risk_tier)
            if decision is not None and not decision.is_allowed:
                return decision

        return ToolDecision.allow()


def _evaluate_policy(
    policy: ToolPolicy,
    tool_slug: str,
    risk_tier: str,
) -> ToolDecision | None:
    """Phase 1 簡化 evaluator：只認 block_risk_tier / block_tool 兩種 rule.

    YAML 格式範例：
        block_risk_tier: restricted
        block_tool: lookup_pii_data
    """
    try:
        rule = yaml.safe_load(policy.rule_yaml) or {}
    except yaml.YAMLError:
        # malformed rule → 視為不適用（不阻擋，但 audit 看得到）
        return None

    if not isinstance(rule, dict):
        return None

    blocked_tier = rule.get("block_risk_tier")
    if blocked_tier == risk_tier:
        return ToolDecision.block(
            reason=f"policy '{policy.name}' blocks risk_tier={risk_tier}",
            rule_name=policy.name,
        )

    blocked_slug = rule.get("block_tool")
    if blocked_slug == tool_slug:
        return ToolDecision.block(
            reason=f"policy '{policy.name}' blocks tool {tool_slug}",
            rule_name=policy.name,
        )

    return None

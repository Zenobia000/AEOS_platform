"""Skill loader — 從 skills/ git monorepo 讀 manifest + prompt.

依 ADR-0003 + MC-005：git 是 source of truth；DB skill_version row
是查詢鏡像。loader 把 git filesystem 內的 manifest.yaml + system.md
轉成 application 層的 `LoadedSkill` DTO。
"""

from app.skill.loader import LoadedSkill, SkillLoader
from app.skill.router import (
    NoSkillBoundError,
    RoutingDecision,
    SkillRouter,
)

__all__ = [
    "LoadedSkill",
    "NoSkillBoundError",
    "RoutingDecision",
    "SkillLoader",
    "SkillRouter",
]

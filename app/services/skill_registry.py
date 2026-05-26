"""SkillRegistryService — Git → DB sync.

對應 MC-005 §Interface SkillRegistryService.sync_from_git。
Phase 1 後續 #24 落地：掃 skills/ git tree → upsert skill / skill_version DB rows
（DB 是查詢鏡像，git 是 source of truth — ADR-0003）。

不在 Phase 1 範圍：
- Event-driven sync（git webhook → auto sync）→ Phase 2
- Skill quality gate evaluation → 由 TestSetRunner 跑後另寫 skill_version.test_pass_rate
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.skill import Skill
from app.db.models.skill_version import SkillVersion


@dataclass(frozen=True)
class SyncResult:
    skills_inserted: int
    skills_updated: int
    versions_inserted: int
    versions_skipped: int  # 已存在不動
    errors: list[str]


def _read_manifest(manifest_path: Path) -> dict[str, Any]:
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}


def _normalize_version(version_dirname: str) -> str:
    """目錄名 'v1.0.0' → DB 存 '1.0.0'（移除 'v' 前綴；對映 router 反向 helper）。"""
    return version_dirname[1:] if version_dirname.startswith("v") else version_dirname


async def sync_from_git(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    skills_root: Path | str,
) -> SyncResult:
    """掃 `<skills_root>/<vertical>/<slug>/<version>/manifest.yaml` → upsert DB.

    Args:
        session: async DB session（caller 管 transaction）
        tenant_id: 該 sync 行為的 tenant scope（skill.tenant_id 全套這個）
        skills_root: git monorepo 根目錄（通常 ./skills）

    Returns:
        SyncResult — 統計 + errors

    特性：
    - 同 (skill.tenant_id, slug) 已存在 → update name/vertical/description；不存在 → insert
    - 同 (skill_version.skill_id, version) 已存在 → 跳過（DB 為事實鏡像，不覆寫）
    - 若 manifest 缺欄位或解析失敗 → 列入 errors 但不中斷
    - `_template` / `.git` / 隱藏目錄 → skip
    """
    root = Path(skills_root)
    if not root.is_dir():
        return SyncResult(0, 0, 0, 0, [f"skills_root not a dir: {root}"])

    skills_inserted = 0
    skills_updated = 0
    versions_inserted = 0
    versions_skipped = 0
    errors: list[str] = []

    for vertical_dir in sorted(root.iterdir()):
        if not vertical_dir.is_dir():
            continue
        if vertical_dir.name.startswith(("_", ".")):
            continue

        for slug_dir in sorted(vertical_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            if slug_dir.name.startswith(("_", ".")):
                continue

            slug = f"{vertical_dir.name}/{slug_dir.name}"

            for version_dir in sorted(slug_dir.iterdir()):
                if not version_dir.is_dir():
                    continue
                manifest_path = version_dir / "manifest.yaml"
                if not manifest_path.is_file():
                    errors.append(f"missing manifest: {manifest_path}")
                    continue

                try:
                    manifest = _read_manifest(manifest_path)
                except yaml.YAMLError as exc:
                    errors.append(f"yaml parse {manifest_path}: {exc}")
                    continue

                skill_meta = manifest.get("skill", {}) or {}
                # Upsert skill row
                skill = (
                    await session.execute(
                        select(Skill).where(
                            Skill.tenant_id == tenant_id,
                            Skill.slug == slug,
                        )
                    )
                ).scalar_one_or_none()
                if skill is None:
                    skill = Skill(
                        tenant_id=tenant_id,
                        slug=slug,
                        vertical=vertical_dir.name,
                        name=skill_meta.get("name") or slug,
                        description=skill_meta.get("description"),
                        owner=skill_meta.get("owner"),
                    )
                    session.add(skill)
                    await session.flush()
                    skills_inserted += 1
                else:
                    new_name = skill_meta.get("name") or skill.name
                    new_desc = skill_meta.get("description")
                    changed = (
                        skill.name != new_name
                        or skill.vertical != vertical_dir.name
                        or skill.description != new_desc
                    )
                    if changed:
                        skill.name = new_name
                        skill.vertical = vertical_dir.name
                        skill.description = new_desc
                        await session.flush()
                        skills_updated += 1

                # Insert skill_version if not exists（已存在不覆寫 — 視 git 內容為新 commit 才更）
                version_str = _normalize_version(version_dir.name)
                existing = (
                    await session.execute(
                        select(SkillVersion).where(
                            SkillVersion.skill_id == skill.id,
                            SkillVersion.version == version_str,
                        )
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    versions_skipped += 1
                    continue

                sv = SkillVersion(
                    skill_id=skill.id,
                    tenant_id=tenant_id,
                    version=version_str,
                    status=manifest.get("status", "draft"),
                    prompt_template_ref=manifest.get("prompt_template_ref") or "system.md",
                    tool_bindings=list(manifest.get("tool_bindings") or []),
                    policy_refs=list(manifest.get("policy_refs") or []),
                    test_set_ref=manifest.get("test_set_ref"),
                )
                session.add(sv)
                await session.flush()
                versions_inserted += 1

    return SyncResult(
        skills_inserted=skills_inserted,
        skills_updated=skills_updated,
        versions_inserted=versions_inserted,
        versions_skipped=versions_skipped,
        errors=errors,
    )

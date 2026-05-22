"""SkillLoader — 從 skills/<slug>/<version>/{manifest,system,tools} 讀檔.

對應 db-schema.md §3.2 + MC-005 + skills/README.md 的 git monorepo 結構：

    skills/
    └── customer-service/
        └── faq-respond/
            └── v1.0.0/
                ├── manifest.yaml      ← 主 metadata
                ├── system.md          ← system prompt
                └── tools.yaml         ← tool schemas

Phase 1 簡化：
- 同步檔案讀（skills/ 是本地 mount，不走 network）
- 不做 schema validation（Pydantic v2 schema 留 S3 quality gate 補）
- 不快取（後續可加 LRU；prod skill 變動透過 atomic symlink swap）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SKILLS_ROOT = Path("skills")


class SkillNotFoundError(FileNotFoundError):
    """skill_slug/version 在 git tree 找不到對應檔."""


@dataclass(frozen=True)
class LoadedSkill:
    """從 git 讀進 application 層的 skill snapshot。"""

    slug: str
    version: str
    name: str
    description: str | None
    system_prompt: str
    tool_bindings: tuple[str, ...]
    policy_refs: tuple[str, ...]
    io_contract: dict[str, Any] | None
    quality_gate_targets: dict[str, Any] = field(default_factory=dict)


class SkillLoader:
    """從 skills/ git tree 讀取 LoadedSkill。"""

    def __init__(self, root: Path | str = DEFAULT_SKILLS_ROOT) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def load(self, slug: str, version: str) -> LoadedSkill:
        """讀 skills/<slug>/<version>/ → LoadedSkill.

        Args:
            slug: 'vertical/skill-name' (e.g. 'customer-service/faq-respond')
            version: semver (e.g. 'v1.0.0')

        Raises:
            SkillNotFoundError: 對應目錄或檔案缺失
        """
        version_dir = self._root / slug / version
        if not version_dir.is_dir():
            raise SkillNotFoundError(f"skill version dir not found: {version_dir}")

        manifest_path = version_dir / "manifest.yaml"
        prompt_path = version_dir / "system.md"

        if not manifest_path.is_file():
            raise SkillNotFoundError(f"manifest.yaml missing: {manifest_path}")
        if not prompt_path.is_file():
            raise SkillNotFoundError(f"system.md missing: {prompt_path}")

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        prompt = prompt_path.read_text(encoding="utf-8")

        skill_meta = manifest.get("skill", {}) if isinstance(manifest, dict) else {}

        return LoadedSkill(
            slug=str(manifest.get("id", slug)),
            version=str(manifest.get("version", version.lstrip("v"))),
            name=str(skill_meta.get("name", slug)),
            description=skill_meta.get("description"),
            system_prompt=prompt,
            tool_bindings=tuple(manifest.get("tool_bindings", []) or []),
            policy_refs=tuple(manifest.get("policy_refs", []) or []),
            io_contract=manifest.get("io_contract"),
            quality_gate_targets=manifest.get("quality_gate_targets", {}) or {},
        )

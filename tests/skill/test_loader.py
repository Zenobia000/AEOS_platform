"""SkillLoader 行為測試 — 讀 skills/customer-service/faq-respond/v1.0.0/."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.skill import LoadedSkill, SkillLoader
from app.skill.loader import SkillNotFoundError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_load_real_faq_skill() -> None:
    """讀真實 skills/customer-service/faq-respond/v1.0.0/."""
    loader = SkillLoader(root=_repo_root() / "skills")
    skill = loader.load("customer-service/faq-respond", "v1.0.0")

    assert isinstance(skill, LoadedSkill)
    assert skill.version == "1.0.0"
    assert "customer-service" in skill.slug
    assert "faq-respond" in skill.slug
    assert "search_knowledge" in skill.tool_bindings
    assert "request_human_handoff" in skill.tool_bindings
    assert skill.system_prompt  # 非空
    assert "AI 客服" in skill.system_prompt or "客服" in skill.system_prompt


def test_load_missing_version_raises(tmp_path: Path) -> None:
    loader = SkillLoader(root=tmp_path)
    with pytest.raises(SkillNotFoundError):
        loader.load("vertical/skill", "v9.9.9")


def test_load_missing_manifest_raises(tmp_path: Path) -> None:
    version_dir = tmp_path / "a/b/v1.0.0"
    version_dir.mkdir(parents=True)
    (version_dir / "system.md").write_text("hi")
    loader = SkillLoader(root=tmp_path)
    with pytest.raises(SkillNotFoundError, match="manifest"):
        loader.load("a/b", "v1.0.0")


def test_load_missing_prompt_raises(tmp_path: Path) -> None:
    version_dir = tmp_path / "a/b/v1.0.0"
    version_dir.mkdir(parents=True)
    (version_dir / "manifest.yaml").write_text("id: a/b\nversion: 1.0.0\n")
    loader = SkillLoader(root=tmp_path)
    with pytest.raises(SkillNotFoundError, match=r"system\.md"):
        loader.load("a/b", "v1.0.0")


def test_load_handles_missing_optional_fields(tmp_path: Path) -> None:
    """manifest 缺 optional 欄位（tool_bindings/policy_refs 等）→ default 空."""
    version_dir = tmp_path / "v/x/v1.0.0"
    version_dir.mkdir(parents=True)
    (version_dir / "manifest.yaml").write_text("id: v/x\nversion: 1.0.0\nskill:\n  name: Minimal\n")
    (version_dir / "system.md").write_text("you are minimal")

    loader = SkillLoader(root=tmp_path)
    skill = loader.load("v/x", "v1.0.0")

    assert skill.name == "Minimal"
    assert skill.tool_bindings == ()
    assert skill.policy_refs == ()
    assert skill.io_contract is None
    assert skill.system_prompt == "you are minimal"

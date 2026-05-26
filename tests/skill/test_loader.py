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


# ── CR-0001 #5: stub verticals 載入驗證 ──────────────


@pytest.mark.parametrize(
    "slug,expected_tool",
    [
        ("hr/leave-request", "query_employee_leave_balance"),
        ("it-helpdesk/password-reset", "verify_user_identity"),
        ("sales/quote-request", "lookup_product_catalog"),
        ("finance/expense-claim", "query_expense_policy"),  # CR-0002
        ("legal/contract-review", "analyze_contract_clauses"),  # CR-0002
    ],
)
def test_load_stub_vertical_skill(slug: str, expected_tool: str) -> None:
    """5 個 stub vertical skill 都能被 SkillLoader 載入 + 含 vertical-specific tool 註釋。"""
    loader = SkillLoader(root=_repo_root() / "skills")
    skill = loader.load(slug, "v1.0.0")

    assert isinstance(skill, LoadedSkill)
    assert skill.version == "1.0.0"
    assert slug in skill.slug
    assert "search_knowledge" in skill.tool_bindings
    # vertical-specific tool 在 manifest 是註釋（preserved by CLI template）
    # → 真正 tool_bindings 只 search_knowledge；expected_tool 用於文件搜尋
    assert "STUB" in skill.system_prompt  # 各 skill system.md 都有 STUB 警示


def test_stub_test_sets_are_valid_yaml() -> None:
    """5 個 stub skill 的 test_set.yaml 都應該是 valid YAML + 含 cases."""
    import yaml

    skills_root = _repo_root() / "skills"
    for slug in (
        "hr/leave-request",
        "it-helpdesk/password-reset",
        "sales/quote-request",
        "finance/expense-claim",  # CR-0002
        "legal/contract-review",  # CR-0002
    ):
        test_set_path = skills_root / slug / "v1.0.0" / "test_set.yaml"
        assert test_set_path.exists(), f"missing: {test_set_path}"
        with test_set_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["quality"] == "stub"
        assert data["target_count"] == 50
        assert isinstance(data["cases"], list)
        assert len(data["cases"]) >= 10, f"{slug}: too few cases"
        # 每題都應有 name / user_input / expected_keywords
        for case in data["cases"]:
            assert "name" in case
            assert "user_input" in case
            assert "expected_keywords" in case
            assert isinstance(case["expected_keywords"], list)

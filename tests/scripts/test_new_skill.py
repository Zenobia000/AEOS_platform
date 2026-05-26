"""new_skill CLI 單元測試 — CR-0001 #4.

不需 DB；驗證：
- 從 template 產生 4 個檔
- placeholder 正確替換
- 重複建立不覆寫（FileExistsError）
- --force 重建
- CLI main() exit code
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.new_skill import (
    create_skill,
    main,
    render_placeholders,
)


@pytest.fixture
def fake_template(tmp_path: Path) -> Path:
    """建一個簡單的 template 目錄供測試用。"""
    template = tmp_path / "_template" / "v0.0.0"
    template.mkdir(parents=True)
    (template / "manifest.yaml").write_text(
        "id: {{VERTICAL}}/{{SLUG}}\nname: {{NAME}}\n", encoding="utf-8"
    )
    (template / "system.md").write_text("# {{NAME}}\n\n{{DESCRIPTION}}\n", encoding="utf-8")
    (template / "tools.yaml").write_text("tools: []\n", encoding="utf-8")
    (template / "test_set.yaml").write_text("quality: stub\ncases: []\n", encoding="utf-8")
    return template


def test_render_placeholders_basic() -> None:
    out = render_placeholders(
        "Hello {{NAME}}, vertical={{VERTICAL}}",
        {"NAME": "Bob", "VERTICAL": "hr"},
    )
    assert out == "Hello Bob, vertical=hr"


def test_render_placeholders_no_match_kept_literal() -> None:
    out = render_placeholders("{{UNKNOWN}}", {"NAME": "x"})
    assert out == "{{UNKNOWN}}"


def test_create_skill_produces_4_files(tmp_path: Path, fake_template: Path) -> None:
    target_root = tmp_path / "skills"
    out = create_skill(
        "hr",
        "leave-request",
        name="請假助手",
        description="協助員工請假。",
        target_root=target_root,
        template_dir=fake_template,
    )

    assert out == target_root / "hr" / "leave-request" / "v1.0.0"
    assert (out / "manifest.yaml").exists()
    assert (out / "system.md").exists()
    assert (out / "tools.yaml").exists()
    assert (out / "test_set.yaml").exists()


def test_create_skill_placeholder_replaced(tmp_path: Path, fake_template: Path) -> None:
    target_root = tmp_path / "skills"
    out = create_skill(
        "hr",
        "leave-request",
        name="請假助手",
        description="協助員工請假。",
        target_root=target_root,
        template_dir=fake_template,
    )

    manifest = (out / "manifest.yaml").read_text(encoding="utf-8")
    assert "hr/leave-request" in manifest
    assert "請假助手" in manifest
    assert "{{" not in manifest  # 沒漏的 placeholder

    sys_md = (out / "system.md").read_text(encoding="utf-8")
    assert "請假助手" in sys_md
    assert "協助員工請假" in sys_md


def test_create_skill_existing_dir_raises(tmp_path: Path, fake_template: Path) -> None:
    target_root = tmp_path / "skills"
    create_skill(
        "hr",
        "leave-request",
        name="x",
        description="y",
        target_root=target_root,
        template_dir=fake_template,
    )

    with pytest.raises(FileExistsError):
        create_skill(
            "hr",
            "leave-request",
            name="x",
            description="y",
            target_root=target_root,
            template_dir=fake_template,
        )


def test_create_skill_template_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        create_skill(
            "hr",
            "leave-request",
            name="x",
            description="y",
            target_root=tmp_path / "skills",
            template_dir=tmp_path / "no-such-template",
        )


def test_main_returns_1_on_dup_dir(
    tmp_path: Path, fake_template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI main() 在目錄重複時應 exit code 1。"""
    target_root = tmp_path / "skills"
    monkeypatch.setattr("scripts.new_skill.SKILLS_DIR", target_root)
    monkeypatch.setattr("scripts.new_skill.TEMPLATE_DIR", fake_template)

    code1 = main(
        [
            "hr",
            "leave-request",
            "--name",
            "x",
            "--description",
            "y",
        ]
    )
    assert code1 == 0

    code2 = main(
        [
            "hr",
            "leave-request",
            "--name",
            "x",
            "--description",
            "y",
        ]
    )
    assert code2 == 1


def test_main_force_rebuilds(
    tmp_path: Path, fake_template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_root = tmp_path / "skills"
    monkeypatch.setattr("scripts.new_skill.SKILLS_DIR", target_root)
    monkeypatch.setattr("scripts.new_skill.TEMPLATE_DIR", fake_template)

    main(["hr", "leave-request", "--name", "原版", "--description", "原"])
    code = main(
        [
            "hr",
            "leave-request",
            "--name",
            "新版",
            "--description",
            "新",
            "--force",
        ]
    )
    assert code == 0
    target = target_root / "hr" / "leave-request" / "v1.0.0"
    manifest = (target / "manifest.yaml").read_text(encoding="utf-8")
    assert "新版" in manifest
    assert "原版" not in manifest


def test_real_template_renders_without_leftover_cli_placeholders(
    tmp_path: Path,
) -> None:
    """用 repo 內真實 skills/_template/ 跑一次，確認 CLI 應替換的 4 個 placeholder
    （VERTICAL / SLUG / NAME / DESCRIPTION）都被替換；runtime placeholder
    （如 {{tenant_name}}）保留是預期行為（執行期才填）。"""
    out = create_skill(
        "test-vertical",
        "test-slug",
        name="Test Skill",
        description="for CLI test only",
        target_root=tmp_path / "skills",
    )

    cli_placeholders = ["{{VERTICAL}}", "{{SLUG}}", "{{NAME}}", "{{DESCRIPTION}}"]
    for f in out.iterdir():
        if not f.is_file():
            continue
        content = f.read_text(encoding="utf-8")
        for ph in cli_placeholders:
            assert ph not in content, f"{f.name}: CLI placeholder 未替換: {ph}"

    # 驗證真實值有寫入
    manifest = (out / "manifest.yaml").read_text(encoding="utf-8")
    assert "test-vertical/test-slug" in manifest
    assert "Test Skill" in manifest

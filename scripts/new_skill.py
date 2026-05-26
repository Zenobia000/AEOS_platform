"""new_skill CLI — 從 skills/_template/ 產生新 vertical/slug skill scaffold.

CR-0001 §9 #4 落地 — AUTHORING-GUIDE 心法的「主動發起 (Proactive Design)」入口：
透過 CLI 確保新 skill 一律從 template 起步、命名 + 結構一致。

Usage:
    python -m scripts.new_skill <vertical> <slug> --name "<Display Name>" --description "<desc>"

範例：
    python -m scripts.new_skill hr leave-request \\
      --name "請假請求助手" \\
      --description "協助員工查詢請假政策、可用天數，並引導申請流程。"

產出：
    skills/<vertical>/<slug>/v1.0.0/{manifest.yaml,system.md,tools.yaml,test_set.yaml}

設計：
- 不覆寫既有目錄（保護未提交的 in-progress skill）
- placeholder 用 {{VAR}} 雙花括號避免與 jinja / shell 衝突
- 只生骨架；50 題 test_set 由後續 #5 stub-verticals branch 用 AI 補
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "skills" / "_template" / "v0.0.0"
SKILLS_DIR = REPO_ROOT / "skills"


def render_placeholders(text: str, mapping: dict[str, str]) -> str:
    """簡易 placeholder 替換。{{KEY}} → mapping[KEY]。"""
    for key, value in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def create_skill(
    vertical: str,
    slug: str,
    *,
    name: str,
    description: str,
    target_root: Path = SKILLS_DIR,
    template_dir: Path = TEMPLATE_DIR,
) -> Path:
    """產生新 skill 目錄。回傳目錄路徑。

    Raises:
        FileExistsError: 目標目錄已存在
        FileNotFoundError: template 目錄不存在
    """
    if not template_dir.exists():
        raise FileNotFoundError(f"template missing: {template_dir}")

    target = target_root / vertical / slug / "v1.0.0"
    if target.exists():
        raise FileExistsError(f"skill 目錄已存在不覆寫: {target.relative_to(target_root.parent)}")

    target.mkdir(parents=True)
    mapping = {
        "VERTICAL": vertical,
        "SLUG": slug,
        "NAME": name,
        "DESCRIPTION": description,
    }

    for src_file in template_dir.iterdir():
        if not src_file.is_file():
            continue
        dst_file = target / src_file.name
        rendered = render_placeholders(src_file.read_text(encoding="utf-8"), mapping)
        dst_file.write_text(rendered, encoding="utf-8")

    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.new_skill",
        description="從 skills/_template 產生新 vertical/slug skill scaffold (CR-0001 #4)。",
    )
    parser.add_argument(
        "vertical",
        help="vertical 名稱（如 hr / it-helpdesk / sales）。對應 skill.vertical 欄位。",
    )
    parser.add_argument(
        "slug",
        help="skill slug（如 leave-request / password-reset）。對應 skill.slug 後段。",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Display name（中文 OK），用於 manifest 與 system.md。",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="一句話描述此 skill 的職責。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="若目標目錄已存在，刪除後重建（危險）。",
    )

    args = parser.parse_args(argv)

    # 從 module-level 重新查（讓 monkeypatch 生效）
    import scripts.new_skill as _mod

    skills_dir = _mod.SKILLS_DIR
    template_dir = _mod.TEMPLATE_DIR

    target = skills_dir / args.vertical / args.slug / "v1.0.0"

    if args.force and target.exists():
        shutil.rmtree(target)

    try:
        out = create_skill(
            args.vertical,
            args.slug,
            name=args.name,
            description=args.description,
            target_root=skills_dir,
            template_dir=template_dir,
        )
    except FileExistsError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        print("→ 加 --force 強制重建（將刪掉現有檔案）", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    try:
        rel = out.relative_to(REPO_ROOT)
    except ValueError:
        rel = out  # tmp dir (e.g. tests) — just use absolute
    print(f"✅ 已建立 skill scaffold: {rel}")
    print()
    print("下一步：")
    print(f"  1. 編輯 {rel}/system.md 寫具體 prompt（依 AUTHORING-GUIDE §5）")
    print(f"  2. 編輯 {rel}/tools.yaml 加 vertical-specific tools（in-mem stub OK）")
    print(f"  3. 編輯 {rel}/test_set.yaml 加 50 題 test case（標 quality: stub）")
    print("  4. git add + commit + 由 SkillLoader 從 git tree 讀進 DB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

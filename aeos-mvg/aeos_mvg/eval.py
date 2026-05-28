"""W1 B1 gate: run the test set offline through draft→judge, print pass rate.

This is the W1 deliverable (foundation/02 §8): prove B1 (messy knowledge →
usable draft) before touching LINE or DB. No DB, no channel — pure offline.

    poetry run python -m aeos_mvg.eval
    poetry run python -m aeos_mvg.eval --knowledge data/knowledge.md --testset data/testset.csv
"""

from __future__ import annotations

import argparse
import csv

from .knowledge import load_knowledge
from .llm import generate_draft, judge_draft

# Thresholds from foundation/03-validation-and-kill (北極星數字 = 原樣 approve 率)
APPROVE_GO = 0.50   # K1: 原樣 approve ≥ 50%
ADOPT_GO = 0.70     # 總採用 (approve+edit) ≥ 70%
ADOPT_KILL = 0.40   # 總採用 < 40% → KILL


def load_testset(path: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            q = (r.get("question") or "").strip()
            ref = (r.get("reference") or "").strip()
            if q:
                rows.append((q, ref))
    if not rows:
        raise SystemExit(f"測試集為空或缺 question 欄：{path}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="對測試集離線打 B1（知識可用性 + 草稿採用率）")
    parser.add_argument("--knowledge", default="data/knowledge.md")
    parser.add_argument("--testset", default="data/testset.csv")
    args = parser.parse_args()

    knowledge = load_knowledge(args.knowledge)
    rows = load_testset(args.testset)

    counts = {"approve": 0, "edit": 0, "reject": 0}
    needs_human = 0
    cache_read = cache_write = tokens_in = tokens_out = 0

    print(f"== 對 {len(rows)} 題跑 draft→judge ==\n")
    for i, (q, ref) in enumerate(rows, 1):
        d = generate_draft(q, knowledge)
        u = d.usage
        cache_read += getattr(u, "cache_read_input_tokens", 0) or 0
        cache_write += getattr(u, "cache_creation_input_tokens", 0) or 0
        tokens_in += u.input_tokens
        tokens_out += u.output_tokens
        if d.needs_human:
            needs_human += 1
        v = judge_draft(q, d.text, ref)
        counts[v.verdict] += 1
        flag = "⚠needs_human " if d.needs_human else ""
        print(f"[{i:>2}] {v.verdict:<7} {flag}| {q[:42]}")

    total = len(rows)
    approve_rate = counts["approve"] / total
    adopt_rate = (counts["approve"] + counts["edit"]) / total

    print("\n== 結果 ==")
    print(
        f"approve(原樣) {counts['approve']}  edit {counts['edit']}  "
        f"reject {counts['reject']}  needs_human {needs_human}"
    )
    print(f"北極星 K1 原樣 approve 率 = {approve_rate:.0%}  (GO ≥ {APPROVE_GO:.0%})")
    print(f"總採用率(approve+edit) = {adopt_rate:.0%}  (GO ≥ {ADOPT_GO:.0%} / KILL < {ADOPT_KILL:.0%})")
    print(f"\nprompt cache: read={cache_read} write={cache_write}  (read 越高=知識快取生效，控成本)")
    print(f"tokens: in={tokens_in} out={tokens_out}")

    print("\n== B1 裁決 ==")
    if approve_rate >= APPROVE_GO and adopt_rate >= ADOPT_GO:
        print("🟢 GO — 草稿可用性達標，B1 朝成立")
    elif adopt_rate < ADOPT_KILL:
        print("🔴 KILL 訊號 — 總採用 < 40%，核心轉換不成立（見 foundation/03）")
    else:
        print("🟡 PIVOT — 介於之間，限再調 2 輪 prompt/知識，調不上去轉 KILL")


if __name__ == "__main__":
    main()

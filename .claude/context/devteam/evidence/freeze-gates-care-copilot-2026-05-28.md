# Evidence: Freeze Gates 1-7 — care-copilot

> **日期**: 2026-05-28 · **Owner**: facilitator（補跑） · **Intensity**: strict(1/4/5a/5b/7)

## 裁決摘要
| Gate | 狀態 | 條件 |
|:--|:--:|:--|
| 1 PRD / 2 UX / 3 Spec / 4 NFR+ADR / 5b Schema | 🟢 frozen | — |
| 5a API | 🟢 frozen | W2: idempotency + x-governance |
| 6 Test | 🟢 frozen | pre-B1: test-data-strategy |
| 7 Release | 🔴 blocked | ①法務 sign-off ②簽 pilot 取真資料(OQ-002) |

## 機械證據
- `scripts/check-doc-consistency.sh`：8/8 通過（斷連結/命名/ID/TC-SEC/meta parity/鐵律/orphan FR/UC）。
- `docs/traceability-matrix.md`：FR×UC×BR×endpoint×test×ADR×鐵律 對齊，orphan=0。

## Review report
→ `.claude/context/devteam/reviews/freeze-gates-care-copilot-2026-05-28.md`（per-gate evidence checklist + critique 來源 + 逐 gate 裁決）

## 業主後續（解 Gate 6/7 前置）
REL-1 法務 sign-off · REL-2 簽 Synergy pilot(OQ-002) · REL-3 補 test-data-strategy（見 state.json pending_user_decisions）

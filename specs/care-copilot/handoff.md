# Handoff — care-copilot 最薄切片（給接手 coding agent）

> **Date**: 2026-05-28 · **Feature**: care-copilot · **Scope**: AEOS 核心 + Care Copilot pack #1，最薄切片（訊息草稿 / 合規低語 / 活檔案）。
> **底層 runtime**：nanobot（Python，AEOS 凍結+多租戶+Tool Gateway 包覆，ADR-0011）。
> **不做**：11 工具全展開、客戶端 App、LINE 官方 API、訂單系統。

---

## 1. 一句話

把直銷商的混亂客戶知識，量產成可審核、合規、有溫度的草稿回覆。驗證賭注 B1（混亂知識→可用草稿），北極星數字 = **草稿原樣 approve 率**。

## 2. 規範包（全部 frozen-candidate，Status 見各檔）

| 類別 | 文件 |
|:---|:---|
| 理念 / 賭注 | `docs/foundation/00-the-bet.md`、`03-validation-and-kill.md`、`01-north-star.md` |
| PRD | `docs/prd/ai-cs-mvg.md`（+ 來源 `docs/foundation/pilot_run.md`） |
| 可行性 / 選型 | `docs/architecture/feasibility-AEOS-x-care-copilot.md` |
| ADR | `docs/architecture/adr/ADR-0011`(nanobot runtime)・`0012`(vertical pack)・`0013`(結構化 contact) |
| 架構 | `docs/architecture/nfr-care-copilot.md`・`c4-care-copilot.md` |
| 分析 / 流程 | `docs/analysis/system-spec-care-copilot.md`・`docs/ux/user-flow-care-copilot.md` |
| 設計 | `docs/api/openapi-care-copilot.yaml`・`docs/data/erd-care-copilot.md` |
| 測試 | `docs/qa/test-plan-care-copilot.md` |
| 運維 | `docs/ops/runbook-care-copilot.md`・`release-readiness-care-copilot.md` |
| W1 起點骨架 | `aeos-mvg/`（Python + Anthropic SDK + prompt caching，eval 已實跑 🟢） |

## 3. 開工順序（最快看到真實草稿）

```
W1  ① 複用 aeos-mvg：ingest 活檔案 + draft + eval → 對真測試集打 B1（不用等 LINE）
       └─ pass rate <50% 且補救無效 → 立即停（foundation/03 硬閘門）
    ② LLM 層換 nanobot 原生 multi-provider（取代直呼 Anthropic SDK，§13）
W2  ③ 結構化 contact（活檔案 7 欄位 + 時間軸，ADR-0013）+ KnowledgeRouter 兩路
    ④ 合規低語 Policy gate（green/yellow/red，pack 詞庫）
    ⑤ expert 審核台（最簡 web，approve/edit/reject）+ audit
    ⑥ nanobot 治理包覆（Frozen + RLS + Tool Gateway）+ killswitch
W3  ⑦ 接 1 位真實 Synergy 教練的真知識，跑 Draft Mode，量採用率
```

## 4. 不可違反的鐵律
1. 學習/生產分離（Frozen，ADR-0011）2. 草稿模式（AI 不自動發）3. Kill switch 30s 4. Audit 全覆蓋 5. 跨租戶 0 串（RLS，紅隊必過）6. 外送 0 踩線（合規 gate）

## 5. 兩軌邊界（ADR-0012）
- 🟦 **core（垂直無關，可複用到下個垂直）**：runtime 包覆 / Policy 引擎 / 多租戶 / 知識治理 / audit / eval / 結構化 contact 模型
- 🟨 **pack（垂直特定）**：直銷領域語意 / FTC-FDA 詞庫 / 3 語氣 prompt / persona

## 6. 唯一未決硬閘門（非技術）
- **OQ-002**：簽下 ≥1 位真實 Synergy 教練提供真資料 → 才能打真 B1（market bet，見 release-readiness）。在此之前 `aeos-mvg/data/` 範例只證產線會動。

## 7. Frozen artifacts（待業主簽核 freeze gate 後鎖版）
ADR-0011/0012/0013（Proposed）、NFR、C4、System Spec、User Flow、OpenAPI、ERD、Test Plan、Runbook、Release Readiness 皆 draft/proposed，等 multi-role review + 業主簽核轉 frozen。

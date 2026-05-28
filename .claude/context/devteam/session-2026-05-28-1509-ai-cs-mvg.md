# DevTeam Session: 2026-05-28-1509-ai-cs-mvg

> **日期**: 2026-05-28
> **Feature**: ai-cs-mvg（AI 客服 7 日上線 MVG / Draft Mode）
> **問題**: 把混亂企業知識在 7 天內量產成人類只簽核一次的 AI 客服員工，驗證賭注 B1（真實知識→可用草稿採用率）
> **路由起點**: P0_DISCOVERY（跳過 bootstrap，直進 PRD）
> **理念地基**: docs/foundation/00~03（提煉自 _0to1 + 北極星；舊 81 份 corpus 退役於 _legacy-dev_docs/）

---

## Narrative

### 2026-05-28 — Session 初始化（devteam-router）

- 業主指令：dev_docs 做廢、理念提煉重置到 docs/、啟動專案初始化
- 決策：① dev_docs 提煉後退役為 `_legacy-dev_docs/`（唯讀歸檔）② 跳過 bootstrap 直進 PRD
- 已建立 `docs/foundation/`（the-bet / north-star / mvg-build-sheet / validation-and-kill）作為專案憲法
- 路由：`current_phase = P0_DISCOVERY`、`bootstrap_done = true`、`next_driver = devteam-pm`
- 下一步：devteam-pm 依 foundation 產出**精簡版 PRD**（對齊 _0to1 最薄切片，不回到舊 PRD-001 的厚度）

## [2026-05-28T07:09:26Z] devteam-pm

產出 PRD draft v1（docs/prd/ai-cs-mvg.md）+ stakeholder map（docs/governance/stakeholders.md）。

- 已填節數：11/11（全節有內容；4 個 Open Question 待業主裁決）
- KPI：北極星 K1 = 草稿原樣 approve 率 ≥ 50%；K2~K4 + 2 counter-metrics
- Open Questions：4（OQ-001 KPI 門檻確認 / OQ-002 pilot 是誰 / OQ-003 審核介面 / OQ-004 動態查詢邊界）
- ASSUMPTION：以 _0to1 foundation 為唯一輸入，未編造數值；TBD 留 Open Questions
- 下游 deps：2（ux/user-flow、analysis/system-spec）
- 註記：devteam_knowledge_base 一度缺失，業主重新提供後重跑；本次已正規讀取 voice-profiles(pm) + templates/prd.md

下一步建議：執行 `/devteam-freeze Gate1_PRD` 進行 multi-role review（ba + sa + ux），或先 `/devteam-pm "補/改 X"` 迭代 Open Questions。

## [2026-05-28] Feasibility Spike — AEOS × Care Copilot × pi（router）

業主帶入 `docs/foundation/pilot_run.md`（Care Copilot 完整 PRD v0.3，11 工具直銷關懷 copilot），釐清後真正意圖 = **評估 AEOS 架構能滿足客戶需求多少（fit-gap / 可行性），本質目標是 AEOS 跨所有垂直的平台**。AEOS = 方法論 + 治理運行平台；pi（github.com/earendil-works/pi）= 底層執行引擎。

- 產出：`docs/architecture/feasibility-AEOS-x-care-copilot.md`（feasibility spike v1）
- 核心發現：**客戶 PRD 獨立收斂到 AEOS ~70% 治理原語**（多租戶/合規 sidecar/學習紀錄/多模型/草稿不自動送）→ 強化「AEOS 可跨垂直」命題
- pi 評估：取 `pi-ai`(多模型抽象) OK；`pi-agent-core` 對 single-shot 工具 overkill 且 TS/Python 分裂 → pilot 不採主 runtime
- 裁決：✅ 可行，建議先做最薄垂直切片 spike（訊息草稿+合規低語+活檔案），可複用 `aeos-mvg/` W1 骨架
- gap → backlog：結構化 contact 知識模型 / 排程層 / **vertical pack 可插拔抽象**（橫向化關鍵）
- 路由：未開新正式 session（feasibility 先行）；若推進 → `/devteam-arch` 正式化 §8 ADR 候選

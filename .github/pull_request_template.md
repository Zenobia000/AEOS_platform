<!--
PR 標題：<type>(<scope>): <subject>  例：feat(kb): add PDF ingest pipeline
type：feat / fix / refactor / docs / test / chore / perf / ci
詳細規範見 .claude/rules/git-workflow.md
-->

## Background（WHY）

<!--
- 為什麼做這個 PR？解決什麼問題、現狀有什麼痛點？
- 若不做會怎樣？
- 關聯 issue / CR / ADR：
-->

## Changes（WHAT）

<!--
- 列出關鍵決策與取捨（不是檔案清單，diff 已經能看）
- 為什麼選方案 A 而非 B
-->

## Impact

<!--
- 受影響的模組 / API / Flow（引 BF-/UF-/SF-/MC-/API- ID）
- 破壞性變更（breaking changes）— 明確標記
- 後續需要的動作（migration、redeploy、document update）
-->

## Test Plan

<!-- 具體驗證步驟 checklist -->

- [ ] `uv run pytest` 全綠
- [ ] `uv run ruff check .` 全綠
- [ ] `uv run mypy app tests` 全綠
- [ ] 覆蓋率 ≥ 80%（CI 自動 gate）
- [ ] 對應 AC 的 acceptance test 全綠（若觸及 UF-001 ~ UF-005）
- [ ] 本地手動驗證（描述步驟）：
- [ ] 文檔同步（若觸 tier-2 contract，需跑 `sunnydata-doc-freshness` skill）

## Change Governance

<!-- 觸及 flow/contract/data/architecture 時必填 -->

- [ ] 不涉及 flow / contract / data / architecture（無需 CIA）
- [ ] 涉及上述，已產出 CIA → `docs/4-exploration/CR-NNNN-*.md`
- [ ] CIA §8「Human Decisions Required」已由 owner 填寫

## Reviewers / Notes

<!--
- 建議的 reviewer：
- 特別請 reviewer 留意的部分：
-->

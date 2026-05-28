# Release Readiness — care-copilot（Pilot Go-Checklist）

> **Status**: draft · **Owner**: `devteam-ops` · **Date**: 2026-05-28 · **Feature**: care-copilot
> Pilot 上線前檢核。對應 Gate 7。Go = 全部勾選 + 業主簽核。

---

## Go-Checklist

### 技術（產線會動）
- [ ] B1 eval 對**真**測試集可跑、出採用率（非範例）
- [ ] 全鏈路 e2e：收訊→草稿→審核→稽核 跑通一次
- [ ] Kill switch 實測 30s 內全停
- [ ] 跨租戶隔離紅隊測試通過（0 串）
- [ ] 合規鐵律：高風險詞攔截、外送 0 踩線
- [ ] 稽核 100% 可還原
- [ ] nanobot 凍結確認（生產不自我擴展）
- [ ] 成本監控 + circuit breaker 就緒（≤$0.30/直銷商/日）

### 法務 / 合規（pilot 前必備）
- [ ] DPA 簽署（碰真客戶資料前）
- [ ] FTC/FDA 詞庫經法務 review

### 市場（OQ-002 硬閘門）
- [ ] **≥1 位真實簽下的 Synergy 教練**，願給真知識 + 真對話
- [ ] 教練 onboarding（建活檔案、操作審核台）

### 觀測 / 運維
- [ ] P0 告警就緒（跨租戶/踩線 > 0）
- [ ] 單一 oncall + incident 流程（Runbook）
- [ ] 資料備份/復原（最壞 15 分鐘）

## Rollout
- 對 1 個 pilot 直接上 **Draft Mode**（人類審每一則，無 canary 需求 — 單 pilot 規模）。
- Rollback：killswitch 30s 全停。

## Go/No-Go
- **Go** ：上述全勾 + 業主簽 foundation/03 殺死條件承諾。
- **No-Go**：任一鐵律項（隔離/踩線/凍結）未過。

> 簽核：CEO ___________  日期 ___________

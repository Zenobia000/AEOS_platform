# NFR Matrix — care-copilot（最薄切片 / Pilot）

> **Status**: draft · **Owner**: `devteam-arch` · **Date**: 2026-05-28 · **Feature**: care-copilot
> 範圍：AEOS 核心 + Care Copilot 最薄切片（訊息草稿 / 合規低語 / 活檔案）。Pilot 期目標，非 GA。
> 來源：`docs/prd/ai-cs-mvg.md` §7、`docs/foundation/pilot_run.md` §6、ADR-0011/0012/0013。

---

## 9 維度 NFR Matrix

| Dimension | Requirement | Pilot 目標（量測） | Critique persona |
|:---|:---|:---|:---|
| **Performance** | 草稿生成 / 合規檢查延遲 | 草稿 p95 < 5s（人類審，非即時自動發）；合規 regex sidecar < 50ms | sre |
| **Availability** | 核心可用度 | Pilot best-effort，單容器；無正式 SLO；killswitch 保底 | sre |
| **Reliability** | 草稿失敗處理 | LLM 失敗 → graceful 標 `[需人工]` + nanobot fallback_models 重試；無靜默失敗 | sre |
| **Scalability** | 規模假設 | 1 tenant、數名 expert、~100 contacts/教練 → **不需水平擴展**（過早即浪費） | sre |
| **Security** | auth / 隔離 | LINE webhook HMAC 驗簽（W2）；secrets 不進 git；DB TLS；`tenant_id` 強制 RLS scope | (security) |
| **Privacy** | PII / 保留 | contact 含 PII；保留隨 DPA（匯出 30 天 / 刪除 7 天）；**不爬 LINE 歷史**（直銷商主動補） | dba |
| **Accessibility** | expert 審核台 | Pilot 內部工具，WCAG `<TBD>`（升 open question，GA 前補） | ux |
| **Auditability** | 全稽核 | 每草稿/每訊息記 `used_chunks + model + decision + decided_by`；**100% 紀錄**；保留隨 DPA | dba |
| **Operability** | MTTR / killswitch | killswitch **30s 內全停**；MTTR best-effort；單一 oncall（CEO） | sre |
| **Cost** | AI 成本上限 | **≤ $0.30 / 直銷商 / 日**（prompt caching + 模型分層 haiku/opus + Quota circuit breaker） | sre |

> [!IMPORTANT]
> 鐵律 NFR（blast radius 致命，1 次都不行）：**跨 tenant 違規 = 0**、**外送踩 FTC/FDA 線 = 0**、**未審自動發訊 = 0**。

## Open Questions（升級）
- **OQ-NFR-1**：expert 審核台 WCAG 等級（pilot 內部工具是否需 AA？）→ ux + 業主，GA 前。

---

> 對映 Gate 4：本 matrix + C4（`c4-care-copilot.md`）+ ADR-0011~0013 + failure modes/observability 共同構成 NFR/ADR baseline。

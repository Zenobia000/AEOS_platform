# NFR Matrix — care-copilot（最薄切片 / Pilot）

> **📋 Status**: draft
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: `devteam-arch`
> **🔖 Version**: v1
> **🎯 Scope**: AEOS 核心 + Care Copilot 最薄切片（訊息草稿 / 合規低語 / 活檔案）。Pilot 期目標，非 GA
> **🔗 Related**: `docs/prd/ai-cs-mvg.md` §7 · `docs/foundation/pilot_run.md` §6 · ADR-0001/0002/0003

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

> 對映 Gate 4：本 matrix + C4（`c4-care-copilot.md`）+ ADR-0001~0004 + failure modes/observability 共同構成 NFR/ADR baseline。

---

## Review 修正 R2（2026-05-28 multi-role review，B-7 arch×sre）
- **Availability baseline（非全 best-effort）**：pilot 核心日間 best-effort，但 **killswitch 觸發後 recovery < N 分鐘**（恢復決策人 = CEO）。
- **killswitch 驗證**：加 `killswitch_active` 心跳 metric + 觸發後 30s 內無新草稿的自動 assert（防 flag 設了 runtime 沒讀到的假停）。
- **P0 SLI 偵測來源（非人工）**：跨租戶違規 = RLS 拒絕事件計數；外送踩線 = 詞庫攔截計數；**>0 自動觸發 killswitch**。
- **Cost 觸頂終態**：circuit breaker 降階後仍超限 → 定義終態（拒服務 / 排隊 / 告警續跑）;加 burn rate alert（50%/80%）。
- **RPO**：補備份頻率（RPO），與 RTO 15 分鐘並列，還原實測納 Go-checklist。

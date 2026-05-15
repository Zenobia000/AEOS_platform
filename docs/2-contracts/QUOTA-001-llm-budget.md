---
id: QUOTA-001
title: LLM Cost / Rate-Limit / Budget Policy
status: active
type: quota-policy
created: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
owner: CTO
tier: 2
related: [ADR-0001, NFR-001, OBS-001, PILOT-001, SAD-v0.1]
---

# QUOTA-001 — LLM 成本/速率/預算政策

> **LLM token 失控是 Pilot 殺手。** 沒有此政策 = 一次 prompt injection 或一次 ingest bug 就燒掉一個月毛利。每個 tenant、每個 endpoint 都必須有硬上限。

## 1. 預算模型

### 1.1 單 tenant 月度預算

依 PILOT-001 §2.2「單 tenant 月毛利率 ≥ 50%」反推：

| 客戶月費 | LLM 預算上限 | 其他成本（infra / vendor） | 毛利目標 |
|---|---|---|---|
| US$ 500 / month | US$ 150 (30%) | US$ 100 (20%) | US$ 250 (50%) |
| US$ 1,000 / month | US$ 300 (30%) | US$ 200 (20%) | US$ 500 (50%) |
| US$ 2,000 / month | US$ 600 (30%) | US$ 400 (20%) | US$ 1,000 (50%) |

LLM 預算 = 月費的 **30%**（hard cap）。超出 = 啟動 §6 降級。

### 1.2 預算翻譯成 Token

假設使用 OpenAI gpt-4o-mini（Phase 1 主模型，依 ADR-0001）：

- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens
- 平均一次對話：~2K input + ~300 output = ~$0.00048

US$ 150 預算 ≈ **312,500 次對話**（單 tenant 月）

這提供了大量空間，但**單一濫用事件**（如無限迴圈、prompt injection 觸發深度 reasoning）能在幾分鐘內燒掉一個月預算。因此需要 §3 多層 rate limit。

## 2. 模型選用層級（依 ADR-0001 + 成本分層）

| Tier | 模型 | 用途 | 成本（每 1M token） | Phase 1 比例目標 |
|---|---|---|---|---|
| **T1 — Lite** | gpt-4o-mini / claude-haiku-4-5 | 90% 對話、分類、簡單 RAG | $0.15 / $0.60 | 90% |
| **T2 — Standard** | gpt-4o / claude-sonnet-4-6 | 複雜推理、多步驟 task | $2.50 / $10 | 9% |
| **T3 — Heavy** | claude-opus-4-7 | 僅疑難案件、人工觸發 | $15 / $75 | 1%（每 tenant 限 50 次/月） |

**默認**：T1。升級 T2/T3 必須由 router 明確決定 + log 升級理由。

## 3. 多層 Rate Limit

```
┌──────────────────────────────────────────────────────┐
│ L1: Per-User Rate Limit                              │
│  └─ 60 messages / hour（防終端使用者濫用）            │
│  └─ 超出 → 拒絕 + 友善提示                            │
├──────────────────────────────────────────────────────┤
│ L2: Per-Tenant Rate Limit                            │
│  └─ Daily soft cap: 預算的 1/30 * 1.2 (寬限)        │
│  └─ Daily hard cap: 預算的 1/30 * 2.0               │
│  └─ Monthly hard cap: 100% 預算（觸發 §6）           │
├──────────────────────────────────────────────────────┤
│ L3: Per-Endpoint Rate Limit                          │
│  └─ /webhook: 100 req/s (全域)                       │
│  └─ /kb/upload: 10 req/min per tenant                │
│  └─ /tests/run: 1 concurrent per tenant              │
├──────────────────────────────────────────────────────┤
│ L4: LLM Provider Rate Limit                          │
│  └─ Respect provider RPS / TPM headers               │
│  └─ Circuit breaker on 429 → fallback provider       │
├──────────────────────────────────────────────────────┤
│ L5: System Circuit Breaker                           │
│  └─ Global LLM spend rate > $50/hour → P0 alert     │
│  └─ Global LLM spend rate > $200/hour → 自動降級     │
└──────────────────────────────────────────────────────┘
```

實作位置：`services/quota-guard/`（中介層，所有 LLM 呼叫必經）。

## 4. Token 上限規則

### 4.1 單次呼叫上限

| 場景 | max_tokens (output) | max prompt tokens | 備註 |
|---|---|---|---|
| 對話回覆 | 500 | 4,000 | 含 RAG context |
| 摘要生成 | 1,000 | 16,000 | 客戶內部報表 |
| KB ingest 標籤化 | 200 | 2,000 | 每分頁 |
| Test set 評分 | 100 | 2,000 | yes/no + 簡短理由 |
| 疑難案件 reasoning | 2,000 | 8,000 | 需 router 顯式升 T2/T3 |

超出 → 拒絕 + log `quota.over_limit`。

### 4.2 Context window 管理

- 對話歷史超過 8K token → 自動摘要前 N 輪（保留最近 5 輪原文）
- RAG retrieval 最多 top-5 chunks，每 chunk ≤ 500 token
- System prompt 限 ≤ 1,000 token；超出 PR review block
- 記憶四層模型與 context 注入策略見 `ADR-0010-memory-architecture.md`

## 5. 監控與告警（對應 OBS-001 §3 §7）

| Metric | 閾值 | 告警 |
|---|---|---|
| `aeos_llm_cost_usd_total` per tenant 日累計 | > 1.2x daily soft cap | Slack warn |
| `aeos_llm_cost_usd_total` per tenant 日累計 | > 2x daily soft cap | P1 |
| `aeos_llm_cost_usd_total` per tenant 月累計 | > 100% monthly budget | P1 + §6 降級 |
| 全系統小時消費 | > $50/hour | P1 |
| 全系統小時消費 | > $200/hour | P0 + 自動降級 |
| 單次呼叫 token 異常 | output > max_tokens * 0.95 持續 | Slack（疑似 prompt injection） |
| T3 模型使用 | 超 50 次/tenant/月 | Slack |

Dashboard：OBS-001 D3 LLM Cost & Usage。

## 6. 降級策略（當觸發預算上限）

依嚴重度漸進：

### Level 1 — Soft Throttle（日預算 100%~120%）

- 限制單 user 速率減半（30 msg/hour）
- 限制 T2/T3 模型使用（強制 T1）
- 通知 tenant admin
- **不影響服務可用性**

### Level 2 — Hard Throttle（日預算 120%~150% 或 月預算 80%）

- 暫停非關鍵 LLM 任務（KB ingest 標籤化、test set 重跑）
- 對話強制 T1，最簡短回覆模式
- 通知 tenant admin + 提供加購 quota 連結
- email 提醒 CEO

### Level 3 — Emergency Cut-off（日預算 200% 或 月預算 100%）

- LLM 呼叫返回 fallback message：「系統繁忙，已通知客服。」
- 對話 escalate 到人工
- P0 incident channel
- CEO 介入：要求 tenant 加購 or 暫停服務

### 緊急手動降級指令

```bash
# 暫停單 tenant LLM 呼叫
./scripts/quota.sh suspend <tenant_id>

# 強制全系統 T1
./scripts/quota.sh force-tier T1

# 解除
./scripts/quota.sh resume <tenant_id>
```

## 7. Prompt Injection / 異常使用防護

LLM 預算最大殺手是 prompt injection 觸發深度 reasoning loop。對策：

| 風險 | 對策 |
|---|---|
| Prompt 含「ignore previous」「reveal system」等 | Pre-filter regex；標記 + log；超過閾值 escalate |
| 無限工具呼叫（agent loop） | 每對話最多 5 次 tool call；超出強制 reply |
| 異常長 input | input > 8K token 切片或拒絕 |
| 短時間同 user 多次重發 | L1 rate limit 兜底 |
| Markdown / code injection 在 RAG context | RAG chunk 必過 sanitization |

Threat model 完整覆蓋見 SEC-001。

## 8. 加購 / Top-up 機制

Pilot 期暫不開放自助加購，但需明文：

- 達 80% 月預算 → email tenant admin
- 達 100% 月預算 → CS 主動聯繫，提供加購選項
- 加購單位：US$ 100 / 50,000 messages（簡化計算）
- 加購後即時生效，30 天有效

GA 期再做 self-serve top-up 流程。

## 9. Cost Attribution

每個 LLM 呼叫必須有以下 metadata 進 `aeos_llm_tokens_total` metric：

```
{
  tenant_id,
  user_id (hashed),
  model,
  feature: "conversation | ingest | test_run | admin",
  trigger: "webhook | scheduled | manual",
  cost_usd
}
```

讓 OBS-001 D3 dashboard 能 drill down：哪個 tenant、哪個 feature、哪次觸發吃掉預算。

## 10. 月度 Review

每月 1 號自動產出報告：

- 每 tenant 實際 LLM 成本 vs 預算
- T1/T2/T3 模型使用佔比
- Top 10 cost 對話（hashed）
- 異常事件清單（rate limit 觸發、降級觸發）
- 預測：依目前趨勢，下月預算是否會破

報告寄 CTO + CEO；發現 tenant 月 LLM 成本 > 月費 25% 連續 2 個月 → 觸發定價 review。

## 11. 實作優先序

| Week | 交付 |
|---|---|
| W1 | quota-guard 中介層基礎（per-tenant counter） |
| W2 | L1 + L2 rate limit；OBS-001 metric 接入 |
| W3 | L4 circuit breaker + fallback provider 切換 |
| W4 | §6 降級腳本；alert 全接入 |
| W5 | §7 prompt injection 防護（regex pre-filter） |
| W6 | Token 上限 §4；context window 摘要 |
| W8 | §10 月度自動報告 |

## 12. PR Review Checklist（與本政策相關）

- [ ] 新 LLM 呼叫是否走 quota-guard 中介層？
- [ ] max_tokens 是否設定且符合 §4？
- [ ] 是否標記正確 feature label？
- [ ] 新 prompt 是否評估 injection 風險？
- [ ] 新 batch / 異步任務是否有 quota check？

---

**See also**:
- `ADR-0001-llm-provider-strategy.md` — provider 選擇與 fallback
- `NFR-001-non-functional-requirements.md` §5 — 成本目標基線
- `OBS-001-observability-spec.md` §3 §7 — metric & alert
- `PILOT-001-success-criteria.md` §2.2 §3 K3 — 商業健康與 kill criteria
- `SAD-v0.1.md` — 系統架構中 quota-guard 位置
- `SEC-001-threat-model.md` (TODO) — prompt injection 完整 threat model

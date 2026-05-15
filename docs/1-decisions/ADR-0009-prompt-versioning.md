---
id: ADR-0009
title: Prompt and Skill Versioning Strategy
status: accepted
date: 2026-05-15
deciders: CTO
tier: 1
---

# ADR-0009 — Prompt / Skill 版本化策略

## Context

LLM 系統的「行為」由 prompt + skill（agent 工具集）決定。一行 prompt 改動可能：
- 讓全部客戶體驗瞬間變差（無 type check、無 unit test 能 100% 抓）
- 改變對話風格（客戶覺得「我的 AI 員工變了個人」）
- 突破 / 解開既有 guardrail（安全災難）

需求：
- 每個 prompt 改動可追溯、可 review、可回滾
- A/B 測試能力（部分流量試新 prompt）
- 每 tenant 可自訂 prompt（系統級 + tenant 級疊加）
- 版本與 code release 解耦（prompt 修改不需 redeploy）
- 50 題 test set 必須對應 prompt 版本（不同版本分數不能混算）

## Decision

### 1. Prompt 儲存與版本

**所有 prompt 進 git，以結構化檔案儲存**（不寫死在 code）：

```
prompts/
├── system/
│   ├── agent-base.yaml          # v1.2.0
│   ├── escalation-judge.yaml    # v0.8.0
│   └── rag-summarizer.yaml      # v1.0.0
├── tools/
│   └── ...
└── tenants/                      # per-tenant overrides
    └── <tenant_id>/
        ├── agent-base.yaml      # tenant 自訂層
        └── glossary.yaml
```

每個 yaml 必含 frontmatter：

```yaml
id: agent-base
version: 1.2.0
status: active           # draft | active | deprecated
created: 2026-05-15
authors: [cto]
test_set_ref: ts-v3      # 對應的 50 題版本
guardrails: [no-pii-echo, no-political, no-medical-advice]
---
You are a customer service agent for {{tenant.business_name}}.
...
```

### 2. 版本號規則（SemVer 變體）

| 變動類型 | 版本 bump | 例 |
|---|---|---|
| 語氣 / 風格小調整 | patch（1.2.0 → 1.2.1）| 加「請」字 |
| 新增 instruction / 新 skill 暴露 | minor（1.2.0 → 1.3.0）| 加上「會議室預約能力」 |
| 改變 escalation rule / 主要 persona / breaking output 格式 | major（1.2.0 → 2.0.0）| 從「禮貌助理」變「專業顧問」 |

Major bump → **必須**全部 test set 重跑且通過率不降。

### 3. 系統 vs Tenant 兩層

```
final_prompt = compose(
    system_prompt[v=current],
    tenant_overrides[tenant_id],
    runtime_context (RAG, user, history)
)
```

- **System layer**：CTO / LLM eng 維護，全 tenant 共用
- **Tenant layer**：tenant 自訂部分（業務術語、tone、特殊規則）
  - 不可覆蓋安全 guardrail
  - 不可超過 1,000 token（防注入式擴大攻擊面）
  - tenant admin 在後台編輯 → 自動產生 git commit by bot

### 4. Release Flow

```
┌────────────────────────────────────┐
│ 1. Draft 改 prompt yaml on branch  │
│    status: draft                    │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 2. CI 自動跑 test set（與當前 active │
│    版本比較）                        │
│    - Pass rate 不降                  │
│    - Latency 不顯著增加              │
│    - Cost 不超 +10%                  │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 3. PR review                        │
│    - CTO + LLM eng                  │
│    - 必含「為什麼改」description     │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 4. Merge → status: active           │
│    舊 active → status: deprecated   │
│    （保留可 rollback 30 天）         │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 5. 自動部署 to prompt registry      │
│    （不需 redeploy app；hot reload） │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 6. Canary：10% 流量 24h             │
│    監控 PILOT-001 KPI                │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│ 7. 全量 ramp 或 rollback            │
└────────────────────────────────────┘
```

### 5. 運行時取用

- App 啟動時不載入 prompt（每次呼叫從 registry 取）
- Prompt registry：Redis cache + Postgres `prompts` table（git-synced）
- 取用 latency：< 5ms（cache hit）
- 失敗 fallback：使用 last-known-good 版本

### 6. A/B Test

```yaml
# prompts/system/agent-base.yaml
version: 1.3.0
ab_test:
  enabled: true
  variants:
    - id: control
      weight: 80
      content: |
        (current prompt text)
    - id: variant_a
      weight: 20
      content: |
        (new prompt text)
  metric: auto_reply_rate
  min_sample: 1000
  duration_days: 7
```

- 同 user 在 A/B 期間綁定同 variant（hash of user_id）
- 結果寫入 OBS-001 metric `aeos_ab_test_outcome`
- 達 min_sample 後自動產生比較報告
- CTO / LLM eng 決定 promote 哪個 variant

### 7. Rollback

```bash
# 緊急 rollback
./scripts/prompt-rollback.sh agent-base 1.2.0
```

- 立即生效（hot reload）
- 自動加 incident 標記 + Slack 通知
- 寫入 audit log

### 8. Guardrail 與 Safety Layer

Prompt 不可單獨設定行為；以下 guardrail 由 **獨立 policy layer** 執行，與 prompt 解耦：

- PII echo 偵測
- 政治 / 醫療 / 法律建議拒答
- Prompt injection 偵測（QUOTA-001 §7）
- 知識邊界（超出 KB 範圍 → escalate）

新增 / 修改 guardrail → 走 ADR 流程（非 prompt PR）。

### 9. Test Set 對應

對應 TEST-001 §1.2：

- 每個 prompt major 版本必須對應 test set 版本
- Test set 改動 → 同步通知所有依賴 prompt 重評
- 跨版本比較 pass rate 必須註明 test set 版本

### 10. Audit

每次 prompt 變更必須進 audit log（OBS-001 §4.2）：

```json
{
  "event": "prompt.change",
  "prompt_id": "agent-base",
  "from_version": "1.2.0",
  "to_version": "1.3.0",
  "actor": "<user_id>",
  "tenant_id": null,  // null = system layer
  "diff_hash": "sha256:...",
  "approved_by": ["<reviewer_user_id>"]
}
```

## Consequences

### 正向

- Prompt 改動可追溯如 code
- 出問題能 5 秒回滾
- A/B 能力支撐持續優化
- Tenant 客製化邊界清晰

### 負向

- Prompt registry 需開發（estim 1 週）
- Hot reload 引入運行時複雜度
- CI test set 跑得慢（每個 prompt PR + 50 題 × tenant 數 = 燒 token）
  - 緩解：用 cached LLM response for stable test set（不每次都打真 API）

### 風險與緩解

| 風險 | 緩解 |
|---|---|
| Prompt registry 故障 → app 無法運作 | Fallback to git-checked-in last-known-good；local cache |
| Tenant 自訂 prompt 注入攻擊 | 1000 token 上限 + 禁用「ignore previous」等模式 + 安全層獨立 |
| A/B 期間 KPI 假性下降 | min_sample 統計顯著性 + 預設 conservative 樣本量 |
| Prompt PR 太頻繁 → reviewer 疲勞 | 設「小改 patch 可單人 review」「major 雙人 review」 |
| 50 題 test set 跑爆 LLM 預算 | 用 stable test set fixture + record-replay；only diff prompts trigger fresh run |

## Alternatives Considered

| 方案 | 為何不選 |
|---|---|
| Prompt 寫死 code 內 | 改動需 redeploy；無 A/B；無 hot fix |
| LangSmith / Helicone | 主要 trace tool；versioning 弱；vendor lock |
| Custom UI for prompt 編輯（Phase 1）| Pilot 期 over-engineer；先用 git PR 流程 |
| 純資料庫 prompt 存儲（無 git） | 失去 code review + history + diff |

## Implementation Notes

- 主程式碼：`services/prompt-registry/`
- DB schema：`prompts(id, version, status, content, frontmatter, ...)` + `prompt_audit_log`
- CI workflow：`.github/workflows/prompt-test.yml`
- Hot reload：Redis pub/sub on `prompt.changed`
- Tenant override UI：`admin-console/prompts/`（Phase 1 末上線）

## Related

- TEST-001 — Test set 對應版本
- OBS-001 §4.2 — Audit log
- QUOTA-001 §7 — Prompt injection 防護
- ADR-0002 — Agent runtime（prompt 是 agent 行為核心）
- ADR-0003 — Skill registry（同樣 versioning 邏輯）
- PROC-001 — Change management（prompt 是 change subject）
- SEC-001 — Threat model（prompt 攻擊面）

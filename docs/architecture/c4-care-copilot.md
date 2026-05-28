# C4 — care-copilot（L1 + L2 / 最薄切片）

> **Status**: draft · **Owner**: `devteam-arch` · **Date**: 2026-05-28 · **Feature**: care-copilot
> 範圍：AEOS 核心（垂直無關）+ Care Copilot pack #1（垂直特定）。最薄切片（草稿/合規/活檔案）。
> 對映 ADR-0001（nanobot runtime）/ ADR-0002（vertical pack 邊界）/ ADR-0003（結構化 contact）。

---

## L1 — System Context

**Our System 一句話責任**：把直銷商的混亂客戶知識，量產成可審核、合規、有溫度的草稿回覆（員工端工具）。

```
        直銷商 / expert (主 actor)          終端客戶 (LINE，間接，pilot 手動貼)
                │ 貼知識 / 審草稿                       ▲ 收到 approve 後的回覆
                ▼                                      │
   ┌──────────────────────────────────────────────────────────┐
   │  AEOS 平台(治理核心) + Care Copilot vertical pack #1       │
   │  「混亂知識 → 可審核/合規/有溫度草稿」                     │
   └───────┬───────────────────────────────┬──────────────────┘
           │ LLM (多模型)                   │ 合規/法務
           ▼                                ▼
     Anthropic API                    DPA / 法務(詞庫 review)
   (opus 草稿 / haiku judge)          (FTC/FDA 紅線)
```

**邊界澄清**：Pilot **不**整合 LINE 官方 API（草稿 + 手動貼）；**不**做客戶端 App（健康問卷除外，不在最薄切片）；**不**接訂單系統（動態查詢 out, OQ-004）。

---

## L2 — Container

**雙軌**：🟦 AEOS 核心（垂直無關，可複用）/ 🟨 Care Copilot pack（垂直特定）。

| Container | 軌 | Tech | 責任 | 對映 ADR |
|:---|:--|:---|:---|:---|
| **nanobot Runtime** | 🟦 | Python(nanobot) | agent loop + MCP 整合；被 AEOS 凍結 | ADR-0001 |
| **Governance Harness** | 🟦 | Python | Frozen + Policy Engine(合規低語) + Tool Gateway + Audit | ADR-0001, 原則3/4 |
| **Tenant Manager** | 🟦 | Postgres RLS | 多租戶隔離（blast radius 限單 tenant） | legacy ADR-0007 |
| **Knowledge Store** | 🟦 | Postgres+pgvector | KnowledgeRouter 三路：結構化 contact / doc-RAG / policy | ADR-0003, §6.3 |
| **LLM Adapter** | 🟦 | nanobot 原生 | openai+anthropic+fallback；prompt caching；模型分層 | §13 |
| **Vertical Pack（Care Copilot）** | 🟨 | manifest(資料) | 直銷領域模型 + FTC/FDA 詞庫 + 3 skills（草稿/合規/活檔案）+ persona | ADR-0002 |
| **Expert Review（W2）** | 🟨 | 最簡 web | approve/edit/reject；approve→回發 | PRD FR-004 |
| **Eval（W1）** | 🟦 | CLI | 離線打 B1（draft→judge→採用率） | `aeos-mvg/` |

### Inter-container（protocol / sync / idempotency / failure）

| Edge | Protocol | Sync | Failure 策略 |
|:---|:---|:---|:---|
| Runtime → LLM Adapter | in-proc | sync | timeout + fallback_models 重試（KB-10 §1） |
| Runtime → Policy(合規) | in-proc | sync | sidecar <50ms；紅燈強制擋(gate)，不可繞過 |
| Runtime → Knowledge | SQL/RLS | sync | 檢索缺漏 → 草稿標 `[需人工]`（不幻覺） |
| Runtime → Audit | append-only | sync | 寫入失敗 = 整筆操作回滾（不允許靜默成功） |
| 全體 → Tenant scope | RLS | — | 跨 tenant = 預設 deny；紅隊必過 |

**Trust boundary**：外部系統憑證只在 Tool Gateway 後；nanobot 不持有；pack 是宣告式資料，不另開執行路徑。

---

## Failure Modes（前 6）

| # | Failure | 偵測 | 復原 |
|:--|:---|:---|:---|
| 1 | LLM API 失敗/逾時 | 草稿生成 error / 延遲 | fallback_models 重試 → 仍失敗標 needs-human |
| 2 | 合規 sidecar 誤判（false positive） | 直銷商關閉率 / 申訴 | 可關單次 + 記原因回收調規則；false negative 由紅隊+人審第二道擋 |
| 3 | **跨租戶資料外洩（RLS 失效）** | 紅隊測試 / audit | RLS + app 層雙重防護；違規=P0 即停（blast radius 致命） |
| 4 | nanobot 自我擴展未凍結 → 行為漂移 | 配置快照 diff / drift 偵測 | Frozen 包覆強制關閉自改（ADR-0001） |
| 5 | 知識檢索缺漏 → 幻覺 | citation 缺 / judge reject | grounding + needs-human guard + 強制 citation |
| 6 | AI 成本爆量 | 成本/直銷商/日 監控 | Quota + circuit breaker 降階模型 |

---

## Observability 前置需求（交 devteam-ops 在 P5 實作）

- **Metrics（SLI）**：草稿延遲 p95 / 成功率、採用率(approve·edit·reject)、合規觸發率·誤判率、成本/直銷商/日、**跨租戶違規數(=0)**、外送踩線數(=0)
- **Logs**：structured，`conversation_id` 串接；每草稿記 `used_chunks + model + decision + decided_by`
- **Traces**：`draft → policy → audit` spans across containers
- **Alerts**：跨租戶違規 > 0（P0）、外送踩線 > 0（P0）、成本超 quota、採用率崩、killswitch 觸發

---

> Gate 4 evidence：NFR matrix（`nfr-care-copilot.md`）✓ · C4 L1+L2 ✓ · ADR ≥1（ADR-0001/0002/0003）✓ · Failure modes ≥5 ✓ · Observability 列出 ✓。

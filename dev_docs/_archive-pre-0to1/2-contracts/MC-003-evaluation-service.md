---
id: MC-003
title: "Module Contract -- Evaluation Service"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 90eaacb470567a3bf631af423e5dbf1ad8053a47
sync-source: doc
source-paths:
  - src/governance/evaluation/
related: [SAD-v0.1, ADR-0005, ADR-0009, MC-001, MC-002, domain-model]
---

# Evaluation Service -- One-Page Module Contract

> **Plane**: Governance | **Priority**: #3 (閉環回饋的引擎) | **Phase 1 scope: basic metrics only**

## Purpose

監控 production AI 員工的品質表現，從對話記錄與 audit log 計算關鍵指標，偵測品質漂移，並將失敗案例分類回饋給 Training Room 觸發重訓。這是 COMPILER 3（Conversation --> Iteration）的技術實作 -- 沒有 Evaluation Service，AI 員工只會「上線後祈禱」。

## Responsibilities

| 做 | 不做 |
|---|---|
| 從 audit_log + conversation 計算品質指標（FCR, CSAT） | 直接修改 AI 員工行為（--> Training Room 重訓） |
| 偵測 Skill 品質漂移（drift detection） | 即時攔截有問題的對話（--> Policy Engine） |
| 將失敗案例分類（Failure Taxonomy）並產生重訓建議 | 執行重訓流程（--> Training Room） |
| 提供指標查詢 API 供 Admin Console dashboard 使用 | 前端 dashboard UI 本身（--> Admin Console） |
| 產生每日品質報告 | 帳務 / 成本分析（--> Cost Tracker, Phase 2） |
| 讀取 Audit Service 資料（唯讀） | 寫入 Audit Service（只在自身操作時寫） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | 指標計算為 batch job（每日 cron），非即時串流 | :green_circle: | Phase 1 對話量低（日均 < 1000），daily batch 足夠；避免串流基礎設施 | 需要 < 5 分鐘延遲的即時告警 --> :yellow_circle: Redis Streams + 即時 pipeline |
| D2 | 所有指標存入 PG `evaluation_metric` table（不用 time-series DB） | :green_circle: | PG 足以存儲百萬筆 metric；避免引入 InfluxDB/TimescaleDB 的運維成本 | 指標量 > 1000 萬筆且查詢 > 3s --> :yellow_circle: TimescaleDB 或 PG partitioning |
| D3 | Hallucination 偵測 Phase 1 用 rule-based（回應 vs KnowledgeCard 關鍵字比對），非 LLM-as-judge | :green_circle: | 省 LLM 成本；Phase 1 先建管線，精準度 Phase 2 升級 | 偽陽/偽陰率 > 20% --> :yellow_circle: LLM-as-judge（Haiku 4.5 逐筆評估） |
| D4 | Drift detection Phase 1 為簡單統計（7 天滑動視窗 pass rate 下降 > 10%） | :green_circle: | 無需 ML 模型，一條 SQL 就能算 | 需偵測語意漂移（語氣變化、回應風格偏移） --> :yellow_circle: embedding 距離 + 異常偵測 |
| D5 | Failure Taxonomy 為預定義 enum（7 類），非動態分類 | :green_circle: | Phase 1 先固定分類；動態分類需 LLM 成本 + 穩定性保證 | 固定分類不夠用 --> :yellow_circle: LLM 輔助分類 + 人工校驗 |
| D6 | 重訓觸發為手動（產生建議 --> 專家決定是否重訓），非自動 | :green_circle: | 安全第一；自動重訓 loop 失控風險高 | 專家信任系統建議後 --> :yellow_circle: 半自動（系統產生 test case + 自動 enqueue training session） |

## Data Model

```sql
-- Evaluation Metric: 每日聚合的品質指標（Phase 1: daily batch only）
CREATE TABLE evaluation_metric (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL,
    employee_id     UUID         NOT NULL,
    skill_id        UUID,                              -- NULL = employee-level metric
    skill_version   TEXT,
    metric_name     TEXT         NOT NULL,              -- Phase 1: 'fcr' | 'csat'
                                                       -- Phase 2: 'aht_seconds' | 'hallucination_rate' |
                                                       -- 'sop_compliance' | 'drift_score' | 'escalation_rate'
    metric_value    NUMERIC(10,4) NOT NULL,
    sample_size     INT          NOT NULL,              -- 計算此指標的對話數
    period_start    TIMESTAMPTZ  NOT NULL,
    period_end      TIMESTAMPTZ  NOT NULL,
    granularity     TEXT         NOT NULL,              -- Phase 1: 'daily' only; Phase 2: 'hourly' | 'weekly'
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_metric_tenant_time ON evaluation_metric (tenant_id, metric_name, period_start DESC);
CREATE INDEX idx_eval_metric_employee    ON evaluation_metric (employee_id, metric_name, period_start DESC);
CREATE INDEX idx_eval_metric_skill       ON evaluation_metric (skill_id, metric_name, period_start DESC);

-- Failure Record: 單一失敗案例
CREATE TABLE failure_record (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID         NOT NULL,
    conversation_id   UUID         NOT NULL,            -- FK conversation
    message_id        UUID,                             -- FK message (optional, 指向具體問題回應)
    employee_id       UUID         NOT NULL,
    skill_id          UUID,
    skill_version     TEXT,
    failure_category  TEXT         NOT NULL,             -- enum, see below
    severity          TEXT         NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    description       TEXT         NOT NULL,
    evidence          JSONB,                             -- 佐證 (e.g. expected vs actual, matched rule)
    retraining_status TEXT         NOT NULL DEFAULT 'pending'
                      CHECK (retraining_status IN ('pending', 'acknowledged', 'retraining', 'resolved', 'wont_fix')),
    acknowledged_by   TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_failure_tenant_time ON failure_record (tenant_id, created_at DESC);
CREATE INDEX idx_failure_category    ON failure_record (failure_category, severity);
CREATE INDEX idx_failure_retraining  ON failure_record (retraining_status) WHERE retraining_status IN ('pending', 'retraining');

-- Phase 2 (deferred): drift_alert, retraining_suggestion tables
-- Phase 1 uses simple 7-day sliding window SQL query for drift detection
-- Phase 1 retraining suggestions are manual (expert decides based on failure_record data)
```

## Interface

### Internal Python API

```python
class EvaluationService:
    """Evaluation Service -- Governance Plane 的品質監控引擎。"""

    # --- Metric Computation (cron job 呼叫) ---
    async def compute_metrics(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
        granularity: Literal["daily"] = "daily",       # Phase 1: daily only
    ) -> list[EvaluationMetric]: ...

    # --- Metric Query ---
    async def get_metrics(
        self,
        tenant_id: str,
        employee_id: str | None = None,
        skill_id: str | None = None,
        metric_name: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        granularity: str = "daily",
    ) -> list[EvaluationMetric]: ...

    async def get_metric_summary(
        self,
        tenant_id: str,
        employee_id: str,
        period_days: int = 7,
    ) -> MetricSummary: ...

    # --- Failure Analysis ---
    async def analyze_failures(
        self,
        tenant_id: str,
        since: datetime,
    ) -> list[FailureRecord]: ...

    async def classify_failure(
        self,
        conversation_id: str,
        message_id: str | None = None,
    ) -> FailureRecord: ...

    async def acknowledge_failure(
        self,
        failure_id: str,
        acknowledged_by: str,
    ) -> FailureRecord: ...

    # --- Drift Detection (Phase 1: simple SQL query, no dedicated table) ---
    async def check_drift(
        self,
        tenant_id: str,
        window_days: int = 7,
        threshold_pct: float = 10.0,
    ) -> list[dict]: ...  # Phase 1: returns dicts; Phase 2: DriftAlert objects

    # --- Dashboard ---
    async def get_dashboard(
        self,
        tenant_id: str,
    ) -> DashboardSummary: ...
```

### REST Endpoints

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/evaluation/metrics` | GET | 查詢指標（filter: tenant, employee, skill, metric_name, period） |
| `/api/v1/evaluation/metrics/summary` | GET | 取得員工品質摘要（7 天） |
| `/api/v1/evaluation/metrics/compute` | POST | 手動觸發指標計算（通常由 cron 呼叫） |
| `/api/v1/evaluation/failures` | GET | 列出失敗案例（filter: tenant, category, severity, status） |
| `/api/v1/evaluation/failures/{id}` | GET | 單筆失敗案例詳情 |
| `/api/v1/evaluation/failures/{id}/acknowledge` | POST | 標記已處理 |
| `/api/v1/evaluation/dashboard/{tenant_id}` | GET | 租戶品質 dashboard（KPI cards + 趨勢） |
| `/api/v1/evaluation/report/daily` | GET | 每日品質報告 |

### Failure Taxonomy (7 Categories)

| Code | 名稱 | 描述 | 嚴重度預設 |
|---|---|---|---|
| F1 | **Hallucination** | AI 回應包含不在 KnowledgeCard 中的事實宣稱 | critical |
| F2 | **SOP Violation** | 回應未遵循既定流程（跳步驟、漏確認） | high |
| F3 | **Scope Escape** | 回應超出 AI 員工被授權的領域範圍 | high |
| F4 | **PII Leak** | 回應洩漏了 PII（自己的或其他用戶的） | critical |
| F5 | **Tone Mismatch** | 語氣、風格與品牌設定不符 | medium |
| F6 | **Escalation Failure** | 該轉人工時未轉，或不該轉時轉了 | high |
| F7 | **Tool Misuse** | 錯誤呼叫工具、參數錯誤、或不必要的工具呼叫 | medium |

### Metric Definitions

| Metric | 計算方式 | 資料來源 | Phase |
|---|---|---|---|
| **FCR** (First Contact Resolution) | 單次對話解決 / 總對話 | `conversation.outcome = 'resolved'` | Phase 1 |
| **CSAT** | 客戶滿意度（若有回饋機制） | Phase 1: 從 outcome 推估 | Phase 1 |
| **AHT** (Avg Handle Time) | 平均對話時長（秒） | `conversation.ended_at - started_at` | Phase 2 |
| **Hallucination Rate** | 幻覺對話 / 總對話 | `failure_record.failure_category = 'hallucination'` | Phase 2 |
| **SOP Compliance** | SOP 合規對話 / 總對話 | 規則比對 + 抽樣 | Phase 2 |
| **Escalation Rate** | 轉人工對話 / 總對話 | `conversation.outcome = 'handoff_human'` | Phase 2 |
| **Drift Score** | 7 天滑動視窗 FCR 變化百分比 | 計算欄位 | Phase 2 (alert if > 10% drop) |

### Event Type 命名規範（寫入 Audit Service）

```
evaluation.metrics_computed     -- 指標計算完成（batch job）
evaluation.failure_detected     -- 偵測到失敗案例
evaluation.failure_acknowledged -- 失敗案例已確認處理
evaluation.drift_alert_created  -- 品質漂移告警產生
evaluation.drift_alert_resolved -- 漂移告警解除
evaluation.retraining_suggested -- 產生重訓建議
evaluation.retraining_accepted  -- 接受重訓建議
evaluation.retraining_rejected  -- 拒絕重訓建議
evaluation.report_generated     -- 品質報告產生
```

## Dependencies

```
 讀取來源（唯讀）                        觸發目標
 ┌────────────────┐                    ┌────────────────┐
 │ Audit Service  │──audit_log──→      │                │
 │ (audit_log)    │                    │  Evaluation    │──retraining──→ Training Room
 │                │                    │  Service       │   suggestion    (MC-002)
 │ Conversation   │──conversation──→   │                │
 │ (conversation  │  + message         │                │──drift alert──→ Admin Console
 │  + message)    │                    │                │   + report       (通知)
 │                │                    │                │
 │ Knowledge (RAG)│──KC for──→         │                │──audit events──→ Audit Service
 │                │  halluc check      │                │                  (MC-001)
 │ Skill Registry │──skill version──→  │                │
 └────────────────┘  metadata          └────────────────┘
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| **Phase 1 tables**: `evaluation_metric`, `failure_record` only | **Phase 2 (deferred)**: `drift_alert`, `retraining_suggestion` tables |
| **Phase 1 metrics**: FCR + CSAT only | AHT, hallucination_rate, SOP compliance (Phase 2) |
| **Phase 1 computation**: daily cron batch only | Hourly batch / real-time streaming (Phase 2) |
| Rule-based hallucination 偵測（關鍵字比對） | LLM-as-judge 精準幻覺偵測 |
| 簡單 drift detection（7 天滑動視窗 + 閾值，SQL query） | Embedding-based 語意漂移偵測 / dedicated drift_alert table |
| `failure_record` table + 7 類 taxonomy | 動態 failure 分類（LLM 輔助） |
| REST API 供 Admin Console | 專用 Evaluation dashboard |
| 每日 cron 產生 email 報告 | Grafana / 即時 dashboard |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1-3 tenants              5-15 tenants                 50+ tenants
--------------------------------------------------------------------
daily batch cron         --> hourly batch              --> Redis Streams / Kafka real-time
PG metric table          --> PG partitioning           --> TimescaleDB / ClickHouse
FCR + CSAT only          --> all 7 metrics             --> custom metric definitions
rule-based halluc        --> LLM-as-judge (Haiku)      --> fine-tuned evaluator model
7-day window drift SQL   --> dedicated drift_alert tbl --> anomaly detection ML model
7 fixed failure types    --> LLM-assisted classify     --> adaptive taxonomy + clustering
manual retraining        --> semi-auto (suggest+queue)  --> auto retraining loop + canary
email daily report       --> Admin Console dashboard   --> Grafana + alerting (PagerDuty)
per-employee metrics     --> per-skill metrics          --> cross-tenant benchmarking
```

---
id: MC-002
title: "Module Contract -- Training Room"
status: draft
tier: 2-contracts
owner: HYBRID (AI-drafts, human-approves)
last-reviewed: 2026-05-15
last-synced-with: 868bfcc407b223db3767f62e3f431e17fb20f55e
sync-source: doc
source-paths:
  - src/governance/training/
related: [SAD-v0.1, ADR-0005, ADR-0009, MC-001, domain-model]
---

# Training Room -- One-Page Module Contract

> **Plane**: Governance | **Priority**: #2 (Frozen Runtime 的入口) | **Phase 1 scope: minimal viable**

## Purpose

提供嚴格隔離的沙盒環境，讓領域專家與 AI 員工共同訓練、測試、審核 Skill，確保只有通過 Quality Gate 的 Skill 版本才能進入 Production。這是 Frozen Runtime 原則的執行機制 -- 沒有 Training Room，「不可變生產」就是空話。

## Responsibilities

| 做 | 不做 |
|---|---|
| 管理 Skill 從 draft 到 approved 的完整生命週期 | 管理 production 運行時行為（--> Employee Runtime） |
| 提供隔離沙盒讓專家與 AI 員工對練 | 直接服務 end-user 流量 |
| 自動產生 test set（50-100 題） | 管理 Knowledge Card 本身（--> Knowledge 模組） |
| 執行 Red Team 對抗測試（7 種攻擊模式） | 即時監控 production 品質（--> Evaluation Service） |
| 實施 7 層 Quality Gate 檢核 | 管理 channel 連接（--> Channel Gateway） |
| 記錄每次 test run 與審核決策到 Audit Service | Skill 的 git 儲存與同步（--> Skill Registry + CI） |
| 將 approved Skill 版本交付 Skill Registry 部署 | Canary release / traffic splitting（--> Deployment Pipeline） |

## Key Decisions

| # | 決策 | 燈號 | 理由 | 升級觸發條件 |
|---|---|---|---|---|
| D1 | Training Room 與 Production 共用同一 PG instance，但用 `environment` 欄位隔離（不另起 DB） | :green_circle: | Phase 1 tenant 數少，邏輯隔離足夠；省維運成本 | 需要不同 LLM 配額或資源隔離 --> :yellow_circle: 獨立 schema / DB |
| D2 | Test set 自動產生用 LLM（Haiku 4.5），專家可增刪改 | :green_circle: | 人工寫 50 題太慢；LLM 產生 + 專家校準 = 速度與品質兼顧 | Test set 品質不穩定 --> :yellow_circle: 加入 test set 品質評分機制 |
| D3 | Red Team 測試為同步執行（test run job 內跑完 7 種攻擊） | :green_circle: | Phase 1 每次 test run < 100 題，同步 3-5 分鐘可接受 | 題數 > 500 或 test run > 10 分鐘 --> :yellow_circle: 拆為 async job + progress tracking |
| D4 | Quality Gate 為 7 層 hard gate，全部 pass 才能 approve | :yellow_circle: | 嚴格但 Phase 1 部分 gate 人工判斷（如 brand voice），增加流程摩擦 | 人工 gate 成為瓶頸 --> :yellow_circle: 部分 gate 自動化（LLM-as-judge） |
| D5 | Skill promotion 為 copy-on-write：Training Room 產出 approved SkillVersion，Skill Registry 讀取後標記為 production | :green_circle: | 符合 Frozen Runtime -- production 讀到的永遠是不可變快照 | 需要 multi-stage promotion（staging --> canary --> full） --> :yellow_circle: 加入 Deployment Pipeline 模組 |
| D6 | 每次 test run + 每次 approval 強制寫 audit log | :green_circle: | Governance-first 原則；合規必需 | 無 -- 這是硬需求，不會降級 |

## Data Model

```sql
-- Training Session: 一次專家-AI 共練的 session
CREATE TABLE training_session (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL,
    skill_version_id UUID        NOT NULL REFERENCES skill_version(id),
    started_by      TEXT         NOT NULL,              -- domain expert user ID
    status          TEXT         NOT NULL DEFAULT 'active'
                                 CHECK (status IN ('active', 'completed', 'abandoned')),
    notes           TEXT,                                -- 專家備註
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_training_session_tenant ON training_session (tenant_id, created_at DESC);
CREATE INDEX idx_training_session_skill  ON training_session (skill_version_id);

-- Test Case: 單一測試題（Phase 1; renamed from test_question）
CREATE TABLE test_case (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL,              -- 租戶隔離
    training_session_id UUID     NOT NULL REFERENCES training_session(id),
    seq             INT          NOT NULL,
    category        TEXT         NOT NULL,              -- 'happy_path' | 'edge_case' | 'red_team' | 'adversarial'
    attack_pattern  TEXT,                                -- red team: 'prompt_injection' | 'pii_extraction' |
                                                        -- 'jailbreak' | 'hallucination_bait' | 'scope_escape' |
                                                        -- 'policy_bypass' | 'emotional_manipulation'
    input_message   TEXT         NOT NULL,
    expected_behavior TEXT       NOT NULL,               -- 預期行為描述（非精確 match）
    tags            TEXT[],
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(training_session_id, seq)
);

-- Test Run: 一次測試執行（含 Red Team）
CREATE TABLE test_run (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL,
    skill_version_id UUID         NOT NULL REFERENCES skill_version(id),
    training_session_id UUID      NOT NULL REFERENCES training_session(id),
    run_type         TEXT         NOT NULL CHECK (run_type IN ('standard', 'red_team', 'full')),
    status           TEXT         NOT NULL DEFAULT 'pending'
                                  CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_questions  INT          NOT NULL,
    passed           INT          NOT NULL DEFAULT 0,
    failed           INT          NOT NULL DEFAULT 0,
    pass_rate        NUMERIC(5,4),                      -- 0.0000 ~ 1.0000
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,
    run_by           TEXT         NOT NULL,
    llm_model        TEXT         NOT NULL,              -- 記錄用了哪個 model
    total_tokens     INT          DEFAULT 0,
    total_cost_usd   NUMERIC(10,4) DEFAULT 0,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_test_run_skill ON test_run (skill_version_id, created_at DESC);

-- Test Result: 單題結果
CREATE TABLE test_result (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL,             -- 租戶隔離
    test_run_id      UUID         NOT NULL REFERENCES test_run(id),
    test_case_id     UUID         NOT NULL REFERENCES test_case(id),
    actual_response  TEXT         NOT NULL,
    verdict          TEXT         NOT NULL CHECK (verdict IN ('pass', 'fail', 'error')),
    failure_reason   TEXT,                               -- 失敗原因分類
    latency_ms       INT,
    tokens_used      INT,
    evaluator        TEXT         NOT NULL,              -- 'llm_judge' | 'rule_based' | 'human'
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Quality Gate Result: 品質關卡紀錄
-- Phase 2 (deferred): derive from test_run data in Phase 1
CREATE TABLE quality_gate_result (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL,
    skill_version_id UUID         NOT NULL REFERENCES skill_version(id),
    gate_number      INT          NOT NULL,             -- 1~7
    gate_name        TEXT         NOT NULL,
    status           TEXT         NOT NULL CHECK (status IN ('pass', 'fail', 'skip', 'pending')),
    evaluated_by     TEXT         NOT NULL,              -- 'system' | user ID
    evidence         JSONB,                              -- 佐證資料（test run ID, pass rate, etc.）
    notes            TEXT,
    evaluated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(skill_version_id, gate_number)
);

-- Approval Record: 專家最終審核
CREATE TABLE skill_approval (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL,
    skill_version_id UUID         NOT NULL UNIQUE,      -- 一個版本只有一筆 approval
    decision         TEXT         NOT NULL CHECK (decision IN ('approved', 'rejected', 'revoked')),
    approved_by      TEXT         NOT NULL,
    rejection_reason TEXT,
    gate_results     JSONB        NOT NULL,              -- snapshot of all gate results at approval time
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

## Interface

### Internal Python API

```python
class TrainingRoomService:
    """Training Room -- Governance Plane 的 Skill 訓練入口。"""

    # --- Test Case Management ---
    async def generate_test_cases(
        self,
        skill_version_id: str,
        target_count: int = 50,       # 50-100 questions
        include_red_team: bool = True, # 含 7 種攻擊模式
    ) -> list[TestCase]: ...

    async def update_test_case(
        self,
        test_case_id: str,
        input_message: str | None = None,
        expected_behavior: str | None = None,
    ) -> TestCase: ...

    # --- Test Execution ---
    async def run_test(
        self,
        skill_version_id: str,
        training_session_id: str,
        run_type: Literal["standard", "red_team", "full"] = "full",
    ) -> TestRun: ...

    async def get_test_run_results(
        self,
        test_run_id: str,
    ) -> TestRunWithResults: ...

    # --- Training Session ---
    async def start_training_session(
        self,
        skill_version_id: str,
        expert_user_id: str,
    ) -> TrainingSession: ...

    async def end_training_session(
        self,
        session_id: str,
        notes: str | None = None,
    ) -> TrainingSession: ...

    # --- Quality Gate ---
    async def evaluate_quality_gates(
        self,
        skill_version_id: str,
    ) -> list[QualityGateResult]: ...

    # --- Approval ---
    async def submit_for_approval(
        self,
        skill_version_id: str,
    ) -> SkillApproval: ...

    async def approve_skill_version(
        self,
        skill_version_id: str,
        approved_by: str,
    ) -> SkillApproval: ...

    async def reject_skill_version(
        self,
        skill_version_id: str,
        rejected_by: str,
        reason: str,
    ) -> SkillApproval: ...

    # --- Promotion ---
    async def promote_to_production(
        self,
        skill_version_id: str,
    ) -> SkillVersion: ...
```

### REST Endpoints

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/v1/training/test-cases` | POST | 自動產生 test cases |
| `/api/v1/training/test-cases/{id}` | GET | 取得 test case 詳情 |
| `/api/v1/training/test-cases/{id}` | PATCH | 專家修改單題 |
| `/api/v1/training/test-runs` | POST | 執行測試 |
| `/api/v1/training/test-runs/{id}` | GET | 取得 test run 結果 |
| `/api/v1/training/test-runs/{id}/results` | GET | 取得逐題結果 |
| `/api/v1/training/sessions` | POST | 開始訓練 session |
| `/api/v1/training/sessions/{id}` | PATCH | 結束訓練 session |
| `/api/v1/training/skills/{skill_version_id}/gates` | GET | 查看 Quality Gate 狀態 |
| `/api/v1/training/skills/{skill_version_id}/gates` | POST | 觸發 Quality Gate 評估 |
| `/api/v1/training/skills/{skill_version_id}/approve` | POST | 專家審核通過 |
| `/api/v1/training/skills/{skill_version_id}/reject` | POST | 專家審核拒絕 |
| `/api/v1/training/skills/{skill_version_id}/promote` | POST | 推送到 production |

### 7-Layer Quality Gates

| Gate | 名稱 | 檢核方式 | 通過條件 | Phase |
|---|---|---|---|---|
| G1 | **Knowledge Coverage** | 自動：比對 test case 題目 vs KnowledgeCard 覆蓋率 | 覆蓋率 >= 80% | Phase 1 (automated) |
| G2 | **Standard Test Pass** | 自動：standard test run pass rate | >= 80%（ADR-0009 門檻） | Phase 1 (automated) |
| G3 | **Hallucination Check** | 自動：LLM-as-judge 檢查幻覺率 | 幻覺率 < 5% | Phase 1 (automated) |
| G4 | **Red Team Resilience** | 自動：7 種攻擊模式全部 pass | 100% 不被攻破 | Phase 2 (deferred) |
| G5 | **SOP Compliance** | 自動：抽檢 10 題回應是否符合 SOP 流程 | 100% 合規 | Phase 2 (deferred) |
| G6 | **Expert Final Review** | 人工：專家綜合審核 + 簽名 | 專家明確 approve | Phase 1 (manual) |
| G7 | **Brand Voice** | 人工：專家審閱 AI 回應語氣與品牌一致性 | 專家標記 pass | Phase 2 (deferred) |

> **Phase 1 QG scope**: Only G1-G3 automated + G6 expert approval. G4 red team, G5 SOP compliance, and G7 brand voice are deferred to Phase 2.

### Event Type 命名規範（寫入 Audit Service）

```
training.test_set_generated    -- 自動產生 test cases
training.test_set_edited       -- 專家修改 test case
training.test_run_started      -- 測試執行開始
training.test_run_completed    -- 測試執行完成
training.red_team_completed    -- Red Team 測試完成
training.session_started       -- 訓練 session 開始
training.session_ended         -- 訓練 session 結束
training.gate_evaluated        -- 單一 Quality Gate 評估
training.approval_submitted    -- 提交審核
training.approved              -- 專家審核通過
training.rejected              -- 專家審核拒絕
training.promoted              -- 推送到 production
```

## Dependencies

```
 輸入方                           輸出方
 ┌────────────────┐              ┌────────────────┐
 │ Knowledge (RAG)│──KC 內容──→  │                │
 │ Skill Registry │──draft ver─→ │ Training Room  │──approved ver──→ Skill Registry
 │ LLM Client     │──生成/評估─→ │                │──audit events──→ Audit Service
 │ Evaluation Svc │──失敗案例──→ │                │
 └────────────────┘  (retraining)└────────────────┘
                                        ↑
                                  Domain Expert
                                  (Web UI 操作)
```

## Phase 1 Scope

| 做 | 不做（標記為升級路徑） |
|---|---|
| **Phase 1 tables**: `training_session`, `test_case`, `test_run`, `test_result`, `skill_approval` | **Phase 2 (deferred)**: `quality_gate_result` (derive from test_run data), `test_set` (merged into training_session) |
| LLM 自動產生 50 題 test cases + 專家可編輯 | 自動 test case 品質評分 |
| Phase 1 QG: G1-G3 automated + G6 expert approval only | G4 red team, G5 SOP compliance, G7 brand voice (Phase 2) |
| `skill_approval` table + 專家簽核 | 多級審核流程（主管 + 法務） |
| REST API 供 Admin Console 前端呼叫 | 專用 Training Room Web UI（Phase 1 嵌入 Admin Console） |
| 每個事件寫 Audit log | Training Room 獨立 dashboard |
| 單一 promote 動作（approved --> production） | Canary release 整合 |

## Upgrade Path

```
:green_circle: Phase 1                :yellow_circle: Growth                     :red_circle: Scale
1-3 tenants              5-15 tenants                 50+ tenants
--------------------------------------------------------------------
同步 test run            --> async job queue          --> distributed test runner
LLM 產生 50 題           --> 100+ 題 + 品質評分       --> 自適應題庫（依失敗模式補題）
G1-G3+G6 only            --> all 7 gates              --> gate plugin system
人工 G6                  --> LLM-as-judge 輔助        --> 全自動 + 人工抽檢
單次 promote             --> canary + rollback         --> blue-green + feature flag
嵌入 Admin Console       --> 專用 Training Room UI     --> 多角色工作流（trainer/reviewer/approver）
per skill test           --> cross-skill regression    --> continuous evaluation pipeline
```

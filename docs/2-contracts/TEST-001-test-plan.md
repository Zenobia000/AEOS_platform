---
id: TEST-001
title: Test Plan + Traceability Matrix
status: active
type: test-plan
created: 2026-05-15
last-synced-with: abbd2b83fd1ec10383cb68850fff218c1ad57923
owner: CTO
tier: 2
related: [BF-001, UF-001-to-005, SF-001-to-005, API-001-internal, API-002-line-webhook, AC-001-to-005, NFR-001, OBS-001]
---

# TEST-001 — 測試計畫與追溯矩陣

> 「**CI 綠燈 ≠ 功能正確**」— 除非每個 BF/UF/SF/API 都映射到具體 TC。本文件強制要求每個 contract 都有 testable evidence。

## 1. 測試金字塔

依 NFR-001 §6（80% coverage 基線）：

```
              ▲
             ╱E╲           E2E（10%）— 真實 LINE / 真實 LLM provider sandbox
            ╱2E ╲          15-20 個 critical scenario
           ╱_____╲
          ╱       ╲
         ╱   Int   ╲       Integration（30%）— API + DB + worker
        ╱___________╲       60-80 個 module-boundary case
       ╱             ╲
      ╱     Unit      ╲    Unit（60%）— 純函式 / 純邏輯
     ╱_________________╲    300+ 個 fast test
```

### 1.1 各層責任

| 層 | 範圍 | 速度 | 在 CI 跑 | 工具 |
|---|---|---|---|---|
| Unit | 純函式、guardrail rule、prompt template build | < 5s 全跑完 | 每次 push | pytest（Python）/ vitest（TS） |
| Integration | API endpoint + 真實 DB + mocked LLM | < 2min 全跑完 | 每次 push | pytest + testcontainers |
| E2E | 真實 LINE sandbox + LLM provider sandbox | < 5min 全跑完 | nightly + pre-release | playwright + LINE bot test mode |
| Manual / Exploratory | 新 feature smoke + 客戶驗收 | n/a | 部署 staging 後 | 人工 |

### 1.2 Test Set Pass Rate（客戶共寫 50 題）

對應 AC-002，這是**業務正確性指標**，獨立於 CI test suite：

- 每 tenant 維護自己的 50 題（共寫，定義對話 + 期望結果）
- 每日跑一次，pass rate metric 進 OBS-001 D1 dashboard
- 目標 ≥ 85%（PILOT-001 §2.1）

## 2. Traceability Matrix（追溯矩陣）

**規則**：每個 BF/UF/SF/API/AC 必須對應 ≥ 1 個 TC；TC 必須對應 ≥ 1 個 spec。

### 2.1 BF → UF → SF → API → TC 完整鏈

| BF | UF | SF | API | TC（unit / int / e2e） | Owner |
|---|---|---|---|---|---|
| BF-001 | UF-001 客戶開帳 | SF-001 onboarding | API-001 /tenants POST | TC-001 (int), TC-E01 (e2e) | LLM eng |
| BF-001 | UF-002 知識上傳 | SF-002 KB ingest | API-001 /kb/upload | TC-010, TC-011, TC-012, TC-E02 | LLM eng |
| BF-001 | UF-003 共寫 test set | SF-003 test mgmt | API-001 /tests/* | TC-020 ~ TC-025 | CTO |
| BF-001 | UF-004 LINE 接線 | SF-004 webhook + reply | API-002 webhook | TC-030 ~ TC-035, TC-E03 ~ TC-E05 | CTO |
| BF-001 | UF-005 後台監控 | SF-005 dashboard | API-001 /metrics | TC-040 ~ TC-043 | LLM eng |

### 2.2 AC → TC 映射

| AC | 期望行為 | TC |
|---|---|---|
| AC-001 | Auto-reply rate ≥ 70%（基於 50 題 test set） | TC-PASS-001（每日跑） |
| AC-002 | Test set 通過率 ≥ 85% | TC-PASS-002 |
| AC-003 | 不確定時正確 escalate ≥ 95% | TC-ESC-001 ~ TC-ESC-010 |
| AC-004 | P95 latency ≤ 8s | TC-PERF-001（持續監控） |
| AC-005 | 7 天內完成 onboarding | 整合性 staging drill |

### 2.3 NFR → TC 映射

| NFR | TC |
|---|---|
| NFR-001 §1 latency | TC-PERF-001 ~ 005（locust + production p95 monitor） |
| NFR-001 §2 availability | OBS-001 uptime check（持續） |
| NFR-001 §3 security | TC-SEC-001 ~ 010（見 SEC-001 threat model） |
| NFR-001 §4 PII | TC-PII-001 ~ 005（audit log 抽檢） |
| NFR-001 §6 coverage | CI gate（< 80% block merge） |

## 3. 命名與檔案組織

```
tests/
├── unit/
│   ├── test_guardrail.py
│   ├── test_prompt_builder.py
│   └── ...
├── integration/
│   ├── test_kb_ingest.py
│   ├── test_webhook_flow.py
│   └── ...
├── e2e/
│   ├── test_onboarding_journey.py
│   ├── test_line_conversation.py
│   └── ...
├── test_set/           # 客戶 50 題（不在 CI 跑；獨立 runner）
│   ├── tenant_<id>/
│   │   ├── cases.yaml
│   │   └── expected.yaml
└── conftest.py
```

### 3.1 TC ID 規則

- `TC-NNN` — 一般 integration / e2e（從 001 連續）
- `TC-PERF-NNN` — 性能測試
- `TC-SEC-NNN` — 安全測試
- `TC-PII-NNN` — 隱私測試
- `TC-ESC-NNN` — escalation 測試
- `TC-E0N` — E2E 主要 journey
- `TC-PASS-NNN` — pass rate metric（不在 CI，定時跑）

每個 TC 在註解中明示對應 spec：

```python
def test_kb_ingest_pdf_basic():
    """TC-010 — KB ingest happy path.
    Covers: SF-002, API-001 /kb/upload, AC-002
    """
    ...
```

## 4. CI Quality Gates

每 PR 必過：

| Gate | 工具 | 失敗動作 |
|---|---|---|
| Lint | ruff / eslint | block |
| Type check | mypy / tsc | block |
| Unit + Integration | pytest | block |
| Coverage ≥ 80% | pytest-cov | block |
| Migration reverse 存在 | 自訂 check | block |
| Frontmatter `last-synced-with` 更新（tier 2 changed） | sunnydata-doc-freshness | warn → block 若 stale > 5 commits |
| E2E（nightly） | playwright | not blocking PR；blocking release |

## 5. Test Data 管理

### 5.1 Fixture 規則

- 固定 fixture（不變的 reference data） → `tests/fixtures/`
- 隨機 fixture → `factory_boy` / `faker`，固定 seed
- DB fixture → `pytest-postgresql` 每 test isolated transaction

### 5.2 PII 在測試的處理

- ❌ **絕不**在 fixture 用真實 PII（姓名、電話、地址）
- ❌ **絕不**在 fixture 用客戶真實對話
- ✅ 用 `faker` 產生合成資料
- ✅ 客戶 50 題 test set 在獨立 tenant_id，不混入 CI

### 5.3 LLM 在測試的處理

- Unit / Integration：**完全 mock LLM**（用 record-replay fixture）
- E2E nightly：用 LLM provider sandbox（如 OpenAI org with $50/month cap）
- 50 題 test set：用 production model（但走獨立 test tenant）

## 6. 測試環境

| 環境 | 用途 | DB | LLM | LINE |
|---|---|---|---|---|
| local | 開發 + unit | local Postgres | mocked | mocked |
| ci | PR check | testcontainer Postgres | mocked | mocked |
| staging | int + e2e drill | staging Postgres | sandbox | LINE bot test mode |
| prod | 監控（不跑測試）| prod Postgres | prod | prod |
| test-tenant | 50 題 test set runner | prod Postgres（隔離 tenant） | prod | LINE bot test mode |

## 7. 缺陷管理

| 缺陷類型 | 處理 |
|---|---|
| Test failure on main | 立即 revert PR；任何例外需 CTO approve |
| Flaky test | 標 `@pytest.mark.flaky` + 開 issue + 1 週內修；連續兩次失敗則 disable + P1 issue |
| Coverage drop | 提示 reviewer；< 78% 則 block |
| Missing TC（review 發現） | 補 TC 或補 spec；不可僅刪 spec |

## 8. 報表

每週五自動產出，公布在 Slack #engineering：

- Coverage 趨勢（per service）
- Top 10 慢測試
- Flaky test 清單
- Test set pass rate 趨勢
- 新增 TC 數 / 對應的新 spec 數

## 9. PR Review Checklist（測試相關）

- [ ] 新 feature 是否有 unit + integration TC？
- [ ] 修 bug 是否加 regression test？
- [ ] 新 contract（API/UF/SF）是否更新本矩陣 §2？
- [ ] Coverage 沒下降？
- [ ] 測試是否符合 §5 PII / LLM 規則？

## 10. 實作優先序（Pilot 13 週）

| Week | 交付 |
|---|---|
| W1 | 測試骨架 + CI gates；TC-001, 010, 030（happy path each module） |
| W2 | TC-020 ~ 025（test set management）；coverage 達 60% |
| W3 | TC-040 ~ 043 + TC-E01 ~ E03；coverage 70% |
| W4 | TC-ESC-001~010 escalation 測試；coverage 80% baseline |
| W5 | Per-tenant test set runner 上線；TC-PASS-001 自動跑 |
| W8 | TC-SEC-001 ~ 010（對應 SEC-001 threat model） |

---

**See also**:
- `AC-001-to-005-acceptance-criteria.md` — 驗收條件原文
- `BF-001-customer-onboarding.md`, `UF-001-to-005-user-flows.md`, `SF-001-to-005-system-flows.md` — 上游 spec
- `API-001-internal.md`, `API-002-line-webhook.md` — API contracts
- `NFR-001-non-functional-requirements.md` §6 — coverage 基線
- `OBS-001-observability-spec.md` §3 — test set pass rate metric
- `SEC-001-threat-model.md` — security TC 對應

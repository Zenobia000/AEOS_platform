# Traceability Matrix — care-copilot（最薄切片）

> **📋 Status**: generated（半自動：`scripts/check-doc-consistency.sh` 驗，內容手維護）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: facilitator（跨文件單一真相）
> **🔖 Version**: v1
> **🎯 目的**: 把散在 PRD/system-spec/test-plan/openapi/ADR 的對映收成**單一真相表**。任一文件改了 FR/UC/test/endpoint，跟此表對不上 = linter 報錯。補上一輪診斷出的盲區「跨文件同物漂移」。
> **🔗 Verified by**: `scripts/check-doc-consistency.sh`

---

## §1 Coverage Dashboard

| 指標 | 數量 | 健康 |
|:---|:---:|:---|
| FR（PRD） | 7 | — |
| UC（system-spec） | 5 | — |
| BR（system-spec） | 8 | — |
| ADR | 4（全 Proposed） | — |
| API endpoint（openapi） | 5 | — |
| 鐵律（NFR） | 3 | — |
| 測試 case | 13 | — |
| **Orphan FR**（無 UC 也無 test 也無 endpoint） | 0 | 🟢 |
| **Orphan BR**（未被任何 test/governance 覆蓋） | 0 | 🟢 |
| **Lonely ADR**（無下游引用） | 0 | 🟢 |
| **ID 命名分裂**（同物異名） | 0 | 🟢（修於 6036b15） |
| **斷連結** | 0 | 🟢 |

---

## §2 FR ↔ UC ↔ BR ↔ Endpoint ↔ Test ↔ ADR（主表）

> 5 UC ↔ 7 FR **非 1:1**（FR-003/005/006 無專屬 UC，分別為入口/橫切/ops）。

| FR | 標題 | UC | BR | Endpoint | Test | ADR | 鐵律 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| FR-001 | 知識 ingest | UC-1 | BR-1 | `POST /contacts`、`/contacts/{id}/ingest` | T-B1-1 | ADR-0003, ADR-0004 | — |
| FR-002 | 草稿生成 | UC-2 | BR-1, BR-2 | `POST /drafts` | T-B1-1/2, T-GND-1, T-CMP-1~4 | ADR-0001/0002/0003 | 外送踩線=0 |
| FR-003 | 訊息入口（W1 手動貼 / W2 LINE） | —（入口） | — | （W2 LINE webhook） | — | — | — |
| FR-004 | Draft Mode 審核 | UC-3 | BR-4 | `POST /drafts/{id}/decision` | TC-SEC-03 | ADR-0001 | 未審自動發=0 |
| FR-005 | 全鏈路稽核 | —（橫切） | BR-5 | （所有，經 audit_event） | T-AUD-1 | ADR-0001 | — |
| FR-006 | Kill switch | —（ops） | — | （flag，無 endpoint） | T-KILL-1 | ADR-0001 | — |
| FR-007 | 離線 eval | UC-5 | — | `POST /eval` | T-B1-1/2 | — | — |

> **UC-4（合規攔截）** 不對單一 FR：它是 FR-002 草稿流的 gate（BR-2/BR-8），test = T-CMP-1~4。

---

## §3 BR 覆蓋（每條 BR → 誰驗）

| BR | 規則 | 覆蓋方式 | source |
|:---|:---|:---|:---|
| BR-1 | grounded、無幻覺 | T-GND-1 / T-B1-1 | ADR-0003 |
| BR-2 | 合規紅燈 = gate | T-CMP-1~3 | PRD §3.12 |
| BR-3 | 跨 tenant deny | T-ISO-1 / TC-SEC-01 | legacy ADR-0007 → ADR-0003 |
| BR-4 | 人審每則、不自動發 | TC-SEC-03 | PRD §3.6 |
| BR-5 | 全稽核 | T-AUD-1 | 原則3 |
| BR-6 | 生產配置凍結 | T-FRZ-1 | ADR-0001 |
| BR-7 | 同意/資料請求 | governance-gated（`consent-and-dpa.md` SLA 驗收） | governance |
| BR-8 | 合規法源 authority | governance-gated（法務 sign-off）+ T-CMP-4 | governance |

---

## §4 鐵律 → 控制 → 對抗測試（3 條，blast radius 致命）

| 鐵律 | NFR | 控制（C4/threat-model） | 對抗測試 | runbook alert |
|:---|:---|:---|:---|:---|
| **跨 tenant = 0** | NFR Security | RLS ENABLE+FORCE + `tenant_isolation` policy（migration） | **TC-SEC-01** / T-ISO-1 | 跨租戶違規數>0 → P0 killswitch |
| **外送踩線 = 0** | NFR（鐵律） | Policy Engine 獨立於 LLM；red 強制擋；詞庫法源（lexicon-authority） | **TC-SEC-02** / T-CMP-4 | 詞庫攔截計數>0 → P0 |
| **未審自動發 = 0** | NFR（鐵律） | Draft Mode；Tool Gateway 不暴露發送工具；`sent_at⊥decision` | **TC-SEC-03** | `sent_at IS NOT NULL AND decided_by IS NULL` 掃描 |

---

## §5 ADR Status / 下游引用鏈

| ADR | 標題 | Status | 下游引用 | freeze 時點 |
|:---|:---|:---|:---|:---|
| ADR-0001 | nanobot Frozen Runtime | Proposed | C4, NFR, runbook, threat-model, openapi | 可 pre-pilot Accept |
| ADR-0002 | Vertical Pack 抽象 | Proposed | C4, knowledge-pipeline, lexicon-authority, threat-model | **刻意延至 B1 後**（高槓桿介面） |
| ADR-0003 | 結構化 contact | Proposed | ERD, openapi, system-spec | 可 pre-pilot Accept |
| ADR-0004 | 知識 ingestion 治理 | Proposed | knowledge-pipeline, consent-and-dpa, threat-model | **刻意延至 B1 後** |

> Lonely ADR = 0（4 個皆有下游）。supersede chain：無 superseded（全初版）。

---

## §6 Health Issues（linter 自動 flag）

> 由 `scripts/check-doc-consistency.sh` 每次重跑刷新。當前：**全綠**。

- 🔴 Critical：orphan FR / 斷連結 / ID 命名分裂 / 鐵律無對抗測試 → **0**
- 🟡 Warning：orphan BR / lonely ADR / 待補標記異常 → **0**（pilot_run/G4-G5 的待補為刻意 defer，linter 白名單排除）

---

## §7 維護規則

1. 改 FR/UC/BR/test/endpoint → **同步改本表** → 跑 `scripts/check-doc-consistency.sh`。
2. linter 報錯 = 本表與文件漂移，必修才 commit（建議掛 pre-commit / CI）。
3. 每個 freeze gate 前跑一次（Gate evidence 強制項）。

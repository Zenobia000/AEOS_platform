---
id: PROJ-001
title: 90-Day Sprint Plan + RACI + Definition of Done
status: active
type: project-plan
created: 2026-05-14
owner: CTO + CEO
tier: 3
related: [PRD-001, BF-001, UF-001..005, AC-001..005]
---

# PROJ-001 — 90-Day Sprint Plan

> Phase 1 完整時程、RACI、定義完成（DoD）、風險登記。對應 PRD-001 與 BF-001。

## 1. 整體節奏

- **每週**：週一 90 分鐘 planning + retro；週五 60 分鐘 demo + 客戶 sync
- **無 daily standup**（3 人團隊太小，async 即可）
- **Async 工具**：GitHub Issues + Projects（Kanban）；Slack workspace
- **客戶溝通**：weekly status email + ad-hoc LINE

## 2. Sprint 結構（13 週）

| Sprint | 週次 | 主題 | Goal |
|---|---|---|---|
| S0 | Week 1 | Specs ✅ | ADR / Domain / DB / PRD（已完成） |
| S0.5 | Week 1.5 | SA Layer ✅ | BF / UF / NFR（已完成） |
| S0.5 | Week 2 | SD Layer ✅ | SAD / API / UX（已完成） |
| S1 | Week 2.5 | PM Layer + 開工準備 | AC / 此文件 / 開工 checklist |
| S2 | Week 3–4 | KB & KC | UF-001 完整可用 |
| S3 | Week 5–6 | TestSet & Skill 初版 | UF-002 完整可用、第一個 Skill v1.0 |
| S4 | Week 7–8 | LINE 整合 + Draft Mode | UF-003 完整可用 |
| S5 | Week 9–10 | Canary + Kill Switch + Audit UI | UF-004, UF-005 完整可用 |
| S6 | Week 11 | Pilot Hardening | 跑 pilot 客戶整套 onboarding，補洞 |
| S7 | Week 12 | Pilot Live + Canary | Day 7 上線 |
| S8 | Week 13 | Template Extraction + Retro | 抽出 Vertical-X v1，準備第二客戶 |

## 3. 詳細 Sprint Backlog

### S2 — Week 3–4：KB & KC（UF-001）
**Goal**：Expert 可上傳 PDF / URL → 系統產 KC draft → review → approve。AC-001 全 scenario 過。

| Task | Owner | Estimate | Status |
|---|---|---|---|
| Project scaffold（FastAPI + SQLAlchemy + Alembic + RQ） | CTO | 2d | 待 |
| Docker Compose（api / worker / pg / redis） | CTO | 1d | 待 |
| DB migration v0（依 db-schema.md） | CTO | 1d | 待 |
| API: ingest, KC list/edit/approve/archive | CTO | 3d | 待 |
| Worker: ingest job（PDF parse → chunk → LLM title/summary → embed → INSERT） | CTO | 4d | 待 |
| Web SPA scaffold（Vite + React + Tailwind + shadcn）+ login | 隊員 A | 3d | 待 |
| Web: KC list + edit page + upload modal | 隊員 A | 4d | 待 |
| Audit logger module + AuditEvent trigger | CTO | 1d | 待 |
| AC-001 scenarios 跑通（pytest-bdd） | CTO | 1d | 待 |

### S3 — Week 5–6：TestSet & Skill v1.0
| Task | Owner | Estimate |
|---|---|---|
| API: test-sets / cases / runs | CTO | 2d |
| Worker: test_run handler（對 Employee 跑題 → 判 pass/fail） | CTO | 3d |
| Skill loader（讀 git `skills/customer-service/faq-respond/`） | CTO | 2d |
| 第一個 Skill v1.0.0：FAQ respond prompt + io_contract + 50 題 reference test set | CTO | 3d |
| Quality Gate CI（test pass ≥ 0.80 才能 approve） | CTO | 1d |
| Web: Test Set 編輯頁、Run 結果頁 | 隊員 A | 4d |
| AC-002 全 scenario 跑通 | CTO | 1d |

### S4 — Week 7–8：LINE + Draft Mode（UF-003）
| Task | Owner | Estimate |
|---|---|---|
| LINE 帳號申請陪跑客戶 / 文檔化 | CEO + 隊員 A | 1d |
| API: LINE webhook（驗簽 + idempotency + enqueue） | CTO | 2d |
| Worker: process_message handler（RAG + LLM + draft INSERT） | CTO | 4d |
| PII boundary filter（pseudonymize at ingest） | CTO | 3d |
| API: /messages、/messages/{id}/approve、/messages/{id}/reject | CTO | 2d |
| Worker: LINE Push client + retry / DLQ | CTO | 2d |
| Web: Draft Inbox 頁 + LINE Notify 推送 setup | 隊員 A | 4d |
| AC-003 全 scenario | CTO | 1d |

### S5 — Week 9–10：Canary + Kill Switch + Audit UI（UF-004, UF-005）
| Task | Owner | Estimate |
|---|---|---|
| API: auto_reply_pct toggle、emergency-disable、re-enable | CTO | 2d |
| Worker: bucket logic + confidence threshold + anomaly flag | CTO | 3d |
| Alert integration（Slack webhook + email） | CTO | 1d |
| Web: /admin 頁 + /audit 頁 + Dashboard | 隊員 A | 5d |
| AC-004 + AC-005 全 scenario | CTO | 2d |
| Backup script + recovery drill | CTO | 1d |

### S6 — Week 11：Pilot Hardening
| Task | Owner | Estimate |
|---|---|---|
| 跑完整 BF-001 流程（內部 dogfood） | 全員 | 2d |
| 補洞、修 bug、加 alert | CTO | 3d |
| Incident Response v0 撰寫（prompt injection / 模型失控 / 資料外洩 3 個情境） | CTO | 1d |
| 客戶 KB 真實 ingest（Day 1 of pilot） | CTO + Expert | 1d |
| Expert review session（Day 3） | CEO + Expert | 1d |

### S7 — Week 12：Pilot Live
| Task | Owner | Estimate |
|---|---|---|
| Test set 共寫 + run（Day 4–5） | Expert + CTO | 2d |
| Draft Mode（Day 6） | Expert + CTO | 1d |
| Canary 10% / 50% / 100%（Day 7） | CTO | 1d |
| 收齊 setup fee + 啟動月費 | CEO | 0.5d |
| Case study draft | CEO | 1d |

### S8 — Week 13：Template Extraction + Retro
| Task | Owner | Estimate |
|---|---|---|
| 抽 Vertical-X Skill Template v1（從 pilot 的 KC + Skill） | CTO | 3d |
| 對第二客戶試裝（測 ≤ 2h 配置） | CTO + CEO | 1d |
| Phase 1 Retro + Phase 2 招募 JD | 全員 | 2d |
| 寫 ADR-0011（語言選擇正式落地）、補 Engineering Onboarding | CTO | 1d |

## 4. RACI Matrix

| 活動 | CEO | CTO | 隊員 A | Expert |
|---|---|---|---|---|
| 客戶簽約 / 收款 | **A,R** | C | — | I |
| 合約 / 法務 | **A,R** | C | — | — |
| 客戶溝通 / 期望管理 | **A,R** | C | — | I |
| 架構 / ADR | C | **A,R** | C | — |
| Backend 開發 | I | **A,R** | C | — |
| Frontend 開發 | I | A | **R** | — |
| LINE 整合 | I | A | **R** | I |
| 安全 / PII | I | **A,R** | C | I |
| KC review / 提供 | I | C | — | **A,R** |
| Test set 共寫 | I | C | — | **A,R** |
| Draft Mode approve | I | C | — | **A,R** |
| 緊急 disable / re-enable | I | **A,R** | I | C |
| 部署 / DevOps | I | **A,R** | I | — |
| Case study | **A,R** | C | — | C |

> R=Responsible（執行）、A=Accountable（最終負責人）、C=Consulted、I=Informed

## 5. Definition of Done

### Story / Task DoD
- [ ] Code review approved（≥ 1 CTO approve）
- [ ] Unit test 覆蓋 ≥ 80%
- [ ] AC scenario 全部跑通
- [ ] NFR 對應指標達標
- [ ] Audit event 全發 + 驗證寫入
- [ ] 文件無 drift（`sunnydata-doc-freshness` 通過）
- [ ] PR description 含 WHY / WHAT / IMPACT
- [ ] 合併到 main 後手動 smoke test 過

### Sprint DoD
- [ ] 本 sprint 所有 task DoD 達成
- [ ] Sprint demo 完成
- [ ] 客戶 demo（從 S6 開始）成功
- [ ] Retro 完成、改進項記錄

### Phase 1 DoD（Week 13）
- [ ] Pilot 客戶 production live
- [ ] 收齊 setup fee + 1+ 個月月費
- [ ] Skill Template v1 抽出，第二客戶 ≤ 2 小時可配置
- [ ] CTO 每週此 pilot 投入 ≤ 10 小時
- [ ] 所有 AC-001~005 全部 scenario CI 過
- [ ] Phase 2 招募 JD 完成

## 6. Risk Register

| ID | Risk | 機率 | 影響 | Owner | Mitigation |
|---|---|---|---|---|---|
| R-01 | KB 品質太差導致 accuracy 拉不到 70% | 中 | 高 | CTO | EX-1 流程；不下修品質標準 |
| R-02 | Expert 沒時間配合 3 小時 session | 中 | 高 | CEO | 簽約時寫入義務條款 |
| R-03 | LINE webhook 不穩 / 訊息丟失 | 低 | 中 | CTO | retry + DLQ + 監控 |
| R-04 | LLM 出怪話導致 PR 危機 | 低 | 極高 | CTO | Draft Mode 第一週強制；Canary 漸進；Kill switch |
| R-05 | Anthropic API outage | 低 | 高 | CTO | Phase 1 接受人工降級；不重複工程投入 |
| R-06 | Setup fee 收不到 | 低 | 高 | CEO | 50% 預付 + Live 後 7 天內收齊 |
| R-07 | 隊員 A 離職 / 不可用 | 低 | 高 | CEO | 寫好文件 + commit message；CTO 可暫接全棧 |
| R-08 | 預算 burn 超預期 | 中 | 中 | CEO + CTO | 每週對帳；> 預算 110% 立即 trim scope |
| R-09 | Scope creep（客戶要更多功能） | 高 | 中 | CEO | CIA 流程強制；新需求進 Phase 2 backlog |
| R-10 | 第二客戶配置 > 2 小時 | 中 | 高 | CTO | S8 是專門的 template extraction sprint，提早識別 |

**Review cadence**：每週五 retro 時 review；新增 risk 即時加入。

## 7. 預算追蹤（給 bootstrapped）

| 項目 | 月成本估計 | 13 週累計 |
|---|---|---|
| VM hosting（pilot VM + dev VM） | NT$ 3000 | NT$ 9000 |
| Anthropic API（dev + pilot） | NT$ 3000 | NT$ 9000 |
| Tools（GitHub, Sentry free, S3, Cloudflare） | NT$ 500 | NT$ 1500 |
| 其他（域名、SSL、SaaS 雜項） | NT$ 1000 | NT$ 3000 |
| **小計（不含人力）** | **NT$ 7500** | **NT$ 22500** |
| Pilot setup fee（收入） | NT$ 50000 一次 | NT$ 50000 |
| Pilot 月費（收入，Week 12 起） | NT$ 5000–10000 | NT$ 5000 |
| **淨現金流（13 週）** | — | **≈ +NT$ 32500** |

> CTO 與隊員 A 的薪酬不在這裡計（bootstrapped = 創辦人薪酬延期 / equity）

## 8. 不在 Phase 1 的 Scope（明文 backlog）

- 多 channel（Web Chat, WhatsApp）
- 多語言
- Eval Dashboard 進階
- Skill Marketplace
- 主動 outreach
- 第二垂直（餐飲、零售外的）
- Voice / 圖片支援
- 多租戶共享 stack
- SOC 2 / ISO 27001 認證

## 9. 連結
- 業務流程：`BF-001`
- 需求：`PRD-001`
- 驗收：`AC-001` ~ `AC-005`
- 架構：`SAD-v0.1`
- NFR：`NFR-001`
- 工程文化：`engineering-charter.md`

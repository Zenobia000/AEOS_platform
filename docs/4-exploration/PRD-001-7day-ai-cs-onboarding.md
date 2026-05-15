---
id: PRD-001
title: 7-Day AI 客服 Onboarding（Phase 1 唯一 PRD）
status: draft
date: 2026-05-14
owner: CTO
tier: 4
related_adrs: [ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005]
---

# PRD-001 — 7-Day AI 客服 Onboarding

> **這份 PRD 是 Phase 1 的整個產品範圍**。任何不在這份 PRD 內的功能，Phase 1 都不做。

## 1. Background

### 1.1 痛點
我們的 pilot 客戶（小型服務業，3–30 人規模）面臨：
- 客服人手不足 / 流動率 > 50%
- 訓練新人 1–3 個月
- 夜間 / 假日 SLA 不穩
- 重複問題占客服 70% 時間（FAQ、訂單查詢、營業時間）

### 1.2 為什麼是現在
- LLM 已可 production grade 處理 FAQ + 簡單 reasoning
- 對話介面（LINE）在台灣 SMB 滲透率 > 80%
- 客戶願付費（已驗證 setup fee + 月費 model）

### 1.3 為什麼不是別的解
- 自己寫 chatbot → 沒治理、客戶不信、上線後失控
- 買 Salesforce / Zendesk AI → 太貴、太重、不會配置
- 找接案公司 → 一次性、無 reuse、客戶被綁

AEOS 的差異點：**7 天上線、可審計、可回滾、3 小時專家投入**。

## 2. Goals & Non-Goals

### Goals
- ✅ Pilot 客戶可在**自然日 7 天內**完成「上線一位 AI 客服」
- ✅ 客戶領域專家總投入時間 **≤ 3 小時**
- ✅ AI 回答 accuracy（vs. 客戶提供的 50 題 test set）≥ 70%
- ✅ 所有對話 100% 進 audit log；客戶可隨時 review
- ✅ 客戶可一鍵 disable AI（fallback to 人工）

### Non-Goals（Phase 1 明文不做）
- ❌ 多 channel 同時上線（先 LINE **或** Web Chat 一個就好）
- ❌ 多語言（先繁中）
- ❌ 主動外撥 / 主動推送
- ❌ 訂單修改 / 退款執行（只查不寫，risk_tier=restricted 操作 Phase 2）
- ❌ 多 AI 員工協作
- ❌ 自定義 persona UI（Phase 1 一個 default + 文字編輯）
- ❌ 自動 KB 抓取（手動上傳 + 半自動）

## 3. Target Users & Personas

### 3.1 客戶端：店家 / 經營者（Buyer）
- 角色：老闆、店長、營運主管
- 痛點：人手不夠、客服品質不穩
- 決策動機：節省人力成本 + 不漏單

### 3.2 客戶端：領域專家（Expert，可能是同一人）
- 角色：資深員工、客服主管
- 任務：提供 FAQ、確認 AI 回答正確性、簽核 production 上線
- 投入：≤ 3 小時

### 3.3 終端使用者：客戶的消費者
- 角色：透過 LINE 與店家對話的一般人
- 期望：問問題有人秒回；不在乎是不是 AI

### 3.4 內部：AEOS Onboarding Engineer（也可能是 CTO 自己）
- 角色：協助客戶設定、轉換知識文件、驗收
- 投入：Phase 1 ≈ 1 人天 / 客戶

## 4. 7-Day Onboarding Flow

```
Day 0  ┃ 客戶簽約、付 50% setup fee、提供 KB 來源（網站 / FAQ / 既有客服紀錄）
Day 1  ┃ AEOS 內部：建 tenant、初始化 VM stack、跑 KB ingest pipeline
Day 2  ┃ AEOS 內部：產生 Knowledge Card draft，挑出可能的 FAQ
Day 3  ┃ 客戶 expert review（90 分鐘 session）：核對 KC、補漏、確認 persona
Day 4  ┃ AEOS 內部：configure Employee、bind Skill、setup LINE webhook
Day 4  ┃ 客戶 expert 共寫 50 題 test set（60 分鐘 session）
Day 5  ┃ AEOS 內部：對 test set 跑 dry run；accuracy < 70% → 補 KC 再跑
Day 6  ┃ Draft Mode 上線：AI 在 LINE 收訊但**回覆需 expert 1-click approve**（30 分鐘 session）
Day 7  ┃ Canary：10% 流量自動回覆；observe 24h；無重大 error → 100% live
       ┃ 客戶付清 setup fee + 啟動月費
```

## 5. Functional Requirements

### 5.1 KB Ingest（Day 1–2）

| ID | Requirement |
|---|---|
| F-KB-01 | 支援上傳：PDF, DOCX, Markdown, plain text；單檔 ≤ 20 MB |
| F-KB-02 | 支援 URL 抓取（單頁，HTML）；不做整站爬蟲 |
| F-KB-03 | 文件切片：固定 chunk size + overlap；每 chunk 自動產 title + summary |
| F-KB-04 | 切片結果產 `KnowledgeCard draft`，status=`draft` |
| F-KB-05 | 內部頁面可看所有 draft KC、edit、approve、archive |

### 5.2 Employee Configuration（Day 3–4）

| ID | Requirement |
|---|---|
| F-EMP-01 | 建立 Employee：選 role=`customer_service`、name、persona（tone, language） |
| F-EMP-02 | bind 至少 1 個 Skill（Phase 1 預設 `customer-service/faq-respond` v1.0） |
| F-EMP-03 | bind 1 個 channel（LINE OR web chat） |
| F-EMP-04 | LINE：客戶提供 channel access token + webhook URL setup |
| F-EMP-05 | Web chat：產出一段 `<script>` snippet 給客戶嵌網站 |

### 5.3 Test Set Co-Authoring（Day 4）

| ID | Requirement |
|---|---|
| F-TST-01 | Expert 可在介面輸入 50 題 + expected outcome（accept / decline / handoff） |
| F-TST-02 | 一鍵 "Run test"：對當前 Employee 配置跑全部 50 題 |
| F-TST-03 | 顯示 pass rate；逐題顯示 AI 回答 + expected outcome 比對 |
| F-TST-04 | 失敗題：一鍵「我要補一張 KC 來解這題」 |

### 5.4 Draft Mode（Day 6）

| ID | Requirement |
|---|---|
| F-DFT-01 | LINE 收訊時，AI 產出 draft 回覆但**不發出**；推送通知給 expert（LINE Notify / web） |
| F-DFT-02 | Expert 可：1-click approve（送出）、edit-and-send、reject（人工接手） |
| F-DFT-03 | 所有 approve/edit/reject 進 audit log，作為下次 SkillVersion 訓練素材 |

### 5.5 Canary & Live（Day 7+）

| ID | Requirement |
|---|---|
| F-CAN-01 | Toggle：10% / 50% / 100% 流量自動回覆 |
| F-CAN-02 | Confidence threshold：若 LLM 自信度 < 閾值，自動 fallback 到 expert review |
| F-CAN-03 | 一鍵「全 disable AI」（緊急開關，30 秒內生效） |

### 5.6 Audit & Monitoring（全程）

| ID | Requirement |
|---|---|
| F-AUD-01 | 客戶可看自家所有 conversation list + 全文 review |
| F-AUD-02 | 每則 message 顯示：用了哪個 Skill version、引用了哪些 KC、tool calls |
| F-AUD-03 | 每日 email digest：對話數、handoff 率、AI accuracy（依 expert override 推算） |

## 6. Success Metrics

| Metric | Target | Measure |
|---|---|---|
| **Time to live** | ≤ 7 自然日 | Day 0 → Live 時間戳 |
| **Expert hours** | ≤ 3 小時 / 客戶 | 4 個 session 加總 |
| **Test set pass rate** | ≥ 70% Day 5；≥ 80% Day 7 | F-TST-02 結果 |
| **Customer satisfaction**（pilot 訪談） | ≥ 4 / 5 | Day 14 訪談 |
| **Setup fee collected** | 100% | 帳上現金 |
| **AI accuracy（live 第一週）** | ≥ 80%（expert override < 20%） | F-DFT-02 / F-CAN-02 統計 |

## 7. Constraints

- **Tech stack**：依 ADR-0001~0005 已決定（Claude + nanobot + Git Skill + 單租戶 + PII 政策）
- **Budget**：Phase 1 工程投入 ≤ 3 人月（你 + 隊員 A 部分時間）
- **Timeline**：90 天內完成 = MVP + 跑通 pilot
- **不依賴**：第三方 AI orchestration platform（LangChain, LangSmith, OpenAI Assistants）

## 8. Open Questions

| # | Question | Owner | Deadline |
|---|---|---|---|
| Q-01 | Pilot 客戶名稱、產業、聯絡人？ | CEO | Week 1 |
| Q-02 | LINE channel 申請流程細節（誰名下、誰維護 token）？ | CEO | Week 1 |
| Q-03 | KB 來源預估文件數量與格式分布？ | Onboarding | Week 1 |
| Q-04 | Expert 是否願意每週 1 次 30 分鐘 retro（連續 4 週）？ | CEO | Week 2 |
| Q-05 | 「handoff to human」的人是誰、回應 SLA？ | CEO | Week 2 |

## 9. Risks

| Risk | 機率 | 影響 | 緩解 |
|---|---|---|---|
| KB 品質太差導致 accuracy 永遠拉不到 70% | 中 | 高 | Day 5 設 gate；不達標延 Live 時間，不下修品質標準 |
| Expert 沒時間配合 3 小時 session | 中 | 高 | 簽約時把 expert hours 寫進義務條款 |
| LINE webhook 不穩 / 訊息丟失 | 低 | 中 | 加 retry + dead-letter queue |
| LLM 出怪話導致客戶 PR 危機 | 低 | 極高 | Draft Mode 強制過第一週；Canary 階段保留 expert review |
| Setup fee 收不到 | 低 | 高 | 先收 50%，剩下 50% Live 後 7 天內 |

## 10. Out of Scope / Phase 2 backlog

- 多 channel 同時 active
- Eval Dashboard（accuracy trend, drift detection）
- Skill Marketplace / cross-customer template UI
- 主動 outreach（推送營銷訊息）
- 多語言支援
- Voice channel（電話、語音）
- 訂單寫入操作（退款、改單）

## 11. Linked Documents

- 商業情境：`docs/01-vision-positioning.md` §22.8、`docs/03-execution-onboarding.md`
- 架構決策：`ADR-0001` ~ `ADR-0005`
- 領域契約：`docs/2-contracts/domain-model.md`、`docs/2-contracts/db-schema.md`
- Onboarding UX：`docs/appendices/H-onboarding-wizard-ux.md`
- 7-day package：`docs/appendices/I-7-day-package.md`

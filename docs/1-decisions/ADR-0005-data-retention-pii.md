---
id: ADR-0005
title: Data Retention and PII Handling Policy
status: accepted
date: 2026-05-14
deciders: CTO
tier: 1
---

# ADR-0005 — 資料保存與 PII 政策

## Context

AEOS 處理：
- **對話資料**：客戶的終端使用者（消費者）與 AI 員工的對話 — 含姓名、電話、地址、訂單號
- **知識卡片**：客戶的內部知識、產品資訊、SOP — 可能含商業機密
- **Audit Log**：每次 LLM call、tool call、policy decision — 含 PII shadow
- **Test cases**：客戶共寫的 50 題 — 可能含真實案例

法律與合規要求：
- 台灣《個人資料保護法》— 蒐集需告知目的、保留期限可問
- 客戶可能要求 GDPR-like 行為（被遺忘權、可攜權）
- pilot 客戶簽約時極可能要求「資料不外流、不訓練模型」

設計目標：在 Phase 1 就建立**對的習慣**，不要等到 Phase 3 補課（資料補救極貴）。

## Decision

### 1. 最小化收集
- AI 員工**只在必要時**問 PII；可不問就不問
- 系統提示模板強制：「請以最少資訊完成任務」

### 2. PII Pseudonymization at Ingest
- 對話 message 入庫前過 **PII detector**（Phase 1 = 正則 + 名單；Phase 2 升級 NER）
- 偵測到電話、身分證、信用卡號 → 入庫時取代為 token（`<<PHONE_001>>`），原值存獨立加密表
- LLM context 預設只看 pseudonymized 版本；只有審計或客戶授權才解 mask

### 3. 不訓練模型
- **絕對不**將客戶資料送回 Anthropic 用於 model training
- 啟用 Anthropic `disable_training` flag（API 預設）
- 不存 prompt cache 到第三方平台

### 4. 保留期限
| 資料類型 | 預設保留 | 之後處理 |
|---|---|---|
| 對話訊息（含 raw 內文） | 90 天 | 匿名化（PII 取代為 `<<REDACTED>>`），保留統計與 audit |
| 對話訊息（匿名化版） | 2 年 | 用於 case study、failure taxonomy |
| Audit Log | **永久** | 不可刪除；客戶要求刪除需走 ADR 例外流程 |
| Knowledge Cards | 與客戶合約共存 | 解約後 30 天硬刪 |
| Test cases | 與客戶合約共存 | 解約後 30 天硬刪 |

### 5. 客戶權利
- 終端使用者要求查詢 / 刪除自己的資料：48 小時內處理
- 客戶（企業）解約：30 天內硬刪所有與該租戶綁定的資料；提供刪除證明

### 6. 跨境
- Phase 1 資料**全部留在台灣**（AWS ap-northeast-1 / Google asia-east1 / 國內機房）
- 不主動將 PII 傳到台灣外的 LLM endpoint；Anthropic API 走 us-east 是已知例外 — pseudonymized 後可接受，客戶簽約時揭露

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| Phase 1 不做 PII masking，Phase 3 再補 | 客戶資料補做匿名化極貴；早期建習慣便宜 |
| 全本地模型避免跨境 | 推理品質不足（見 ADR-0001） |
| 客戶資料留 7 年（符合會計法） | 我們不是會計 SaaS；對話資料 7 年無業務必要 |
| 客戶要求即刪除（全自助） | Phase 1 沒這人力 / 自動化；先用 48 小時人工 SLA |

## Consequences

**Positive**:
- pilot 客戶合約談判容易（可直接 show 政策）
- 早期建好 pseudonymization 管線，未來 SOC 2 / ISO 27001 cost 大降
- Audit Log 永久保留 = 法律自衛 + case study 資產

**Negative**:
- PII detector 初期偽陽 / 偽陰會發生；需 ops 持續 tune
- 永久保留 audit log 的存儲成本要計入定價（Phase 1 一年 < 1000 NTD，可忽略）

**Tracking**:
- Monthly: PII detector precision/recall（用合成資料測）；目標 > 95%
- Monthly: 客戶刪除請求數量與處理時間
- 每 6 個月 review 政策

## Status

Accepted. 必須在 pilot 客戶合約簽訂前 finalize（最遲 Week 2）。

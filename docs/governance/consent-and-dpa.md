# Governance — 同意 / 隱私 / DPA（care-copilot pilot）

> **📋 Status**: draft（**須一次外部法務 sign-off 才生效** — 見 `stakeholders.md` 法務 owner）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: 法務 owner（pre-seed = CEO + 一次性外部法務 review）
> **🔖 Version**: v1
> **🎯 Scope**: pilot 蒐集/處理終端客戶個資的同意、合法依據、權利、DPA 分工。
> **🔗 Related**: ADR-0004(知識治理管線) · `security/threat-model.md` · ERD §Privacy · `compliance-lexicon-authority.md`

---

## 📋 Executive Summary

> [!IMPORTANT]
> **TL;DR (30s)**: ba critique:同意書/隱私政策/DPA「承諾散在 pilot_run,無規格、無 owner」。本文把它收斂成可簽核的 baseline:**蒐集什麼 PII、合法依據（台個資法 §8/§19 或 GDPR Art.6）、當事人權利（30 天匯出 / 7 天刪除 / 撤回）、三方 DPA 分工（AEOS=processor）**。pilot 碰真資料前必須有一次外部法務 sign-off。

| 維度 | 摘要 |
|:---|:---|
| **🎯 處理者角色** | AEOS = **資料處理者（processor）**;直銷商 = 控制者;Synergy = 品牌方（責任待 DPA 釐清） |
| **📊 PII 範圍** | contact 7 欄位 + interaction + message 原文（見 ERD PII map） |
| **🚀 狀態** | ⚠️ draft;**外部 sign-off = pilot 入場券** |
| **🎯 下一步** | DPA 範本定稿 → 外部法務 review → W0 簽署 |

---

## 🎯 角色與合法依據

| 角色 | 法律身份 | 責任 |
|:---|:---|:---|
| **終端客戶** | data subject / 當事人 | 個資權利主體（升 medium,見 stakeholders） |
| **直銷商（expert）** | **資料控制者** | 決定蒐集目的、取得同意、回應權利請求 |
| **AEOS** | **資料處理者（processor）** | 依控制者指示處理;不挪用、不二次利用、可刪除 |
| **Synergy 品牌方** | 品牌/可能的共同控制者 | 品牌詞、療效/收入宣稱責任 → DPA 釐清 |

**合法依據**:
- 台灣個資法:§19（蒐集/處理特定目的必要範圍）+ §8（告知義務）;§3 當事人權利不得預先拋棄。
- GDPR（若涉歐盟）:Art.6(1)(a) 同意 或 (b) 履約必要;健康相關資料涉 Art.9 特種個資 → 明示同意。

---

## 📝 同意與告知（§8 告知五項）

直銷商向終端客戶蒐集前須告知（範本要點,法務定稿）:
1. **蒐集者**:直銷商（控制者）+ AEOS（受託處理）
2. **目的**:提供關懷/客服回覆草稿的個人化與品質
3. **類別**:聯絡資訊、對話內容、健康關注/家庭/興趣（活檔案 7 欄位）
4. **利用期間/對象/地區**:pilot 期間;限本租戶;不跨境（除 LLM API,見下）
5. **權利**:可查詢/更正/刪除/撤回,及不提供之影響

> [!WARNING]
> **健康關注欄位**涉特種個資 → 同意須**明示**且可單獨撤回;不得作療效推論（接 `compliance-lexicon-authority.md`）。

---

## 🔐 當事人權利 → 系統執行（接 BR-7）

| 權利 | SLA | 系統執行 | Owner |
|:---|:---|:---|:---|
| **匯出** | 30 天內 | 撈本 contact 全資料導出 | 客服/ops |
| **刪除** | 7 天內 | 刪 contact/interaction/message + knowledge_chunk 殘留;audit_event 去識別化保留 | ops + 刪除 job |
| **撤回同意** | 即時 | 停止後續處理;既有資料依刪除流程 | expert |
| **更正** | 即時 | expert 改活檔案 | expert |

- **PITR 衝突**:刪 PII 後備份仍留 ≤7 天（ERD §82）→ 告知當事人「完全清除含備份週期」;PITR 視窗 = 刪除緩衝（不超過必要）。
- **LLM 跨境**:草稿生成傳 Anthropic（美國）→ 屬跨境傳輸,須在告知列明 + zero-retention 條款（threat-model §邊界 4）。

---

## 🎙 語音 / TTS 隱私（pilot_run §3.8 對應）

- 客戶聲音樣本（若 W2+ 接語音）**不進訓練**;僅即時合成,不留存原聲 → 同意書單列。

---

## 🤝 DPA 分工（三方）

| 條款 | 內容 |
|:---|:---|
| **處理範圍** | AEOS 僅依直銷商指示處理 contact/message,不二次利用 |
| **再委託** | LLM provider（Anthropic）為次處理者,zero-retention + 不訓練條款 |
| **安全控制** | RLS 租戶隔離、傳輸加密、audit、刪除能力（接 `security/threat-model.md`） |
| **資料外洩通報** | 跨租戶/外洩事件 72 小時內通報控制者（接 runbook P0） |
| **終止** | pilot 結束 → 依指示刪除/返還;audit_event 去識別化保留 |
| **Synergy 釐清** | 品牌詞使用、療效/收入宣稱的責任歸屬（共同控制 or 純品牌方） |

---

## ✅ Pre-pilot 法務 Go/No-Go

- [ ] 同意書範本（含特種個資明示、跨境傳輸告知）外部法務 review
- [ ] DPA 範本三方分工定稿 + W0 簽署
- [ ] 刪除/匯出 SLA 對應系統能力驗證（BR-7 + ERD 刪除 job）
- [ ] 健康欄位特種個資處理合法性確認

---

## 🔗 Cross References
- PII map / retention:[`docs/data/erd-care-copilot.md`](../data/erd-care-copilot.md) §Privacy
- 知識去識別化管線:ADR-0004
- 安全控制（DPA 承諾的技術面）:[`security/threat-model.md`](../security/threat-model.md)
- 合規詞庫（療效/收入宣稱）:[`compliance-lexicon-authority.md`](./compliance-lexicon-authority.md)
- business rule:`analysis/system-spec-care-copilot.md` BR-7

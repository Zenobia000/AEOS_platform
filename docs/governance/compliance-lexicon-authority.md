# Governance — 合規詞庫權威與法源（care-copilot pack）

> **📋 Status**: draft（詞庫法源須法務 sign-off）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: 法務 owner + AI-Architect（詞庫維護）
> **🔖 Version**: v1
> **🎯 Scope**: Care Copilot pack 的 FTC/FDA/個資 合規詞庫的法源、權威、簽核、申訴。
> **🔗 Related**: ADR-0002(pack) · `security/threat-model.md` §pack 投毒 · system-spec BR-2/BR-8 · `consent-and-dpa.md`

---

## 📋 Executive Summary

> [!IMPORTANT]
> **TL;DR (30s)**: ba/qa critique:合規 50 詞庫「無法源、無權威、誰簽核/誰維護/誤判申訴皆待答」,而 test-plan 的「踩線=0」要拿它當真值。本文定義**詞庫=有 ID + 法源 + 分級的規則集**,綁定權威（法務 sign-off）、維護者（AI-Architect）、變更流程（PR review）、誤擋申訴路徑。沒有法源的詞 = 不可上線。

| 維度 | 摘要 |
|:---|:---|
| **🎯 命題** | 每個合規詞要有法源 ID,否則「踩線=0」無法驗收 |
| **📊 分類** | 療效宣稱(FDA) · 收入宣稱(FTC) · 絕對化用語 · 特種個資 |
| **🚀 狀態** | ⚠️ 結構就緒;50 詞真值集 + 法源映射為 pre-pilot 前置 |
| **🎯 下一步** | 接 `qa/test-data-strategy.md`（待補）的真值/誤擋集 |

---

## 🎯 詞庫條目結構（每詞必備欄位）

> [!NOTE]
> 補 system-spec BR-8:合規 gate 的判定必須可溯源到法源,不是「感覺危險」。

| 欄位 | 說明 | 範例 |
|:---|:---|:---|
| `id` | 詞庫條目 ID | LEX-FDA-001 |
| `category` | 分類 | health_claim / income_claim / absolute_term / sensitive_pii |
| `pattern` | regex / 關鍵詞 | "治療\|根治\|療效\|cure" |
| `gate` | green/yellow/red | red |
| `authority` | **法源**（缺則不可上線） | FTC Act §5 / FDA FD&C Act §201(g) / 健康食品管理法 §14 |
| `rationale` | 為何違規 | 未經核可的療效宣稱 |
| `owner_signoff` | 法務簽核日期 | (待 sign-off) |

---

## 📜 分類與法源（直銷垂直）

| 分類 | 風險 | 法源 | gate |
|:---|:---|:---|:--:|
| **療效宣稱** | 宣稱產品治療/預防疾病 | FDA FD&C Act §201(g);台健康食品管理法 §14 不得宣稱療效 | 🔴 red |
| **收入宣稱** | 誇大招募收入/保證獲利 | FTC Act §5 + FTC Business Opportunity Rule;公平交易法 | 🔴 red |
| **絕對化用語** | 「最」「100%」「保證」 | 公平交易法 §21 不實廣告 | 🟡 yellow |
| **特種個資推論** | 用健康關注推銷療效 | 個資法特種個資 + 上述療效 | 🔴 red |

> 這些是 **🟨 pack 詞庫**（垂直特定,餵 core Policy Engine）;不同垂直（保險）換一套法源（保險法/招攬規範）= ADR-0002 的複用點。

---

## 🏛 權威與流程

| 問題（ba 待答） | 裁決 |
|:---|:---|
| **誰定義詞庫** | AI-Architect 起草 + **法務 owner sign-off**;無 sign-off 的 red 詞不上線 |
| **誰維護/更新** | AI-Architect;法規變更（新 FTC 指引）觸發 review |
| **變更流程** | git-backed + PR review + 法務 sign-off（接 threat-model §pack 投毒） |
| **誤擋申訴** | expert 可單次關閉 + 記原因（system-spec edge case）;誤擋集每週回收 → AI-Architect 調 pattern;誤擋率 ≤5%（test-plan） |
| **判定權威** | Policy Engine（regex,**獨立於 LLM**）= 唯一裁決者（system-spec C4） |

---

## ✅ Pre-pilot Go/No-Go
- [ ] 50 詞每條有 `authority` 法源 + 法務 sign-off
- [ ] 真值集 + 誤擋集就緒（接 `qa/test-data-strategy.md`）
- [ ] 高風險詞召回 100% / 誤擋 ≤5%（test-plan TC）
- [ ] 詞庫變更 PR 流程 + 惡意 pack 對抗測試（threat-model）

---

## 🔗 Cross References
- pack 抽象與後門防禦:ADR-0002 · [`security/threat-model.md`](../security/threat-model.md) §pack 投毒
- business rule:`analysis/system-spec-care-copilot.md` BR-2 / BR-8
- 詞庫真值維護:`docs/qa/test-data-strategy.md`（待補,AI-Architect own）
- 特種個資:[`consent-and-dpa.md`](./consent-and-dpa.md)

# Stakeholder Map — care-copilot（AEOS 核心切片代號 ai-cs-mvg）

> **Status**: draft · **Updated**: 2026-05-28 · **Owner**: PM
> 收 `strategy/docs-gap-audit.md` 根因：5 個盲點 = 未指派的 owner。種子前 = founder 戴帽 / AI persona 代理，標明**觸發換真人**的條件。

## 外部 / 核心 stakeholder

| Stakeholder | Influence | Decision Area | 備註 |
|:---|:---:|:---|:---|
| **CEO / 創辦人** | 🔴 high | 賭注是否成立、Go/Kill 裁決、簽 pilot、預算/跑道 | 唯一 oncall；簽署 `foundation/03` 殺死條件承諾 |
| **Pilot 客戶（客服專家／主管）** | 🟠 high | 提供真實知識、定義「好用」、實際決定 K1 採用率 | 北極星數字的判定者；缺此角色則整個實驗無法跑 |
| **終端客戶（data subject）** | 🟠 **medium** | 個資當事人：同意 / 撤回 / 30 天匯出 / 7 天刪除請求 | **升 medium**（原 low 誤判）：個資法/GDPR 下是權利主體，非旁觀者。見 `governance/consent-and-dpa.md` |
| **Synergy 品牌方** | 🟢 low | 品牌詞使用、療效/收入宣稱責任歸屬 | pilot 期被動；責任分工須 DPA 釐清 |
| **Coding agent / 工程** | 🟠 medium | 依 `foundation/02-mvg-build-sheet` + `data/migrations/` 實作切片 | handoff 對象；不做架構決策（已凍結） |

## 5 個內部 owner（原缺席 → 指派；種子前 founder 戴帽）

> [!IMPORTANT]
> audit 收斂：盲點精準落在「沒人 own」的角色之間。pre-seed 一人戴多帽，但**帽子必須有名字**，否則文件補了也腐爛。

| Owner（帽子） | 負責文件 / Decision Area | 種子前由誰戴 | 觸發換真人 |
|:---|:---|:---|:---|
| **安全 owner** | `security/threat-model.md`；跨租戶/注入/secret 對抗驗證；鐵律「跨tenant=0」 | CEO + arch persona 代理 | pilot 接真資料 / tenant > 5 / 外部 pentest |
| **法務 owner** | `governance/consent-and-dpa.md`、`compliance-lexicon-authority.md`；DPA 簽核、詞庫法源 | CEO + 一次性外部法務 review | 碰真客戶 PII 前（W0）必須有一次外部 sign-off |
| **AI-Architect / 資料 owner** | `qa/test-data-strategy.md`（待補）；50 題測試集 / 200 標註 / 50 詞庫 真值維護 | CEO + qa persona 代理 | B1 打不動 / 真值集需領域標註者 |
| **GTM owner** | `strategy/gtm-execution.md`（待補）；Top Leader 抽成、招募 SOP、CAC/churn | CEO | 垂直#2 啟動 / 付費轉換驗證階段 |
| **SRE-ops owner** | `ops/dr-backup.md`（待補）、runbook；RPO/RTO/secret 輪替/還原演練 | CEO（唯一 oncall） | tenant > 5 / 出現第一次 P0 incident |

> 設計意圖（foundation 延後原則）：不是「現在招 5 個人」，而是**讓每個盲點有明確署名的責任人**。致命路徑（安全/法務）pre-pilot 必須有對抗驗證與一次外部 sign-off；其餘（GTM/SRE/真值集）defer 到對應觸發事件。

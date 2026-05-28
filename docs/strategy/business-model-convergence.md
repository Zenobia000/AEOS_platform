# Strategy — 商業模式收斂藍圖（Socratic + Elon + Premortem Forum）

> **📋 Status**: reviewed（6 問收斂；數字為合理估算，標 ASSUMPTION）
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: founder + facilitator（蘇格拉底/Elon/premortem）
> **🔖 Version**: v2（升 KB-12 格式標準 + R4–R6 收斂）
> **🔗 Related**: `foundation/00-the-bet` · `architecture/feasibility-AEOS-x-care-copilot` · KB-06 · KB-11

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: AEOS = **垂直先行、平台後萃取**的生意。用**直銷(Care Copilot)當垂直#1 兼 B1/治理試煉場**(溫暖 pilot + 最硬合規)，**$39 prosumer 毛利 ~77–87% 成立**——但生死不在 LLM 成本，在 **CAC/churn**(靠 Top Leader 抽成病毒壓低 + 活檔案 lock-in 降 churn)。**平台品牌(AEOS)與垂直產品(Care Copilot)脫鉤**；等**垂直#2(保險，佔位)**證明核心 ≥70% 可複用，才「成為平台」收乘數、才募資。每個 premortem 殺手都對應一個 pilot 可證偽的假設 → 收斂。

| 維度 | 摘要 |
|:---|:---|
| **🎯 商業模式** | 垂直先行 + 平台後萃取（vertical SaaS 養平台 thesis） |
| **📊 單位經濟** | $39/mo · 毛利 ~77–87%（LLM ~$3–9/mo）· LTV ≈ $390 · CAC 上限 ≈ $130 |
| **🚀 狀態** | ⚠️ 6 問已收斂（假資料）；待 pilot 真實數字驗證 |
| **🎯 下一步** | 簽 Synergy pilot 打真 B1 + 量 留存/病毒；確認垂直#2 真實入口 |

---

## 🎯 收斂的商業模式（藍圖）

| 層 | 內容 |
|:---|:---|
| **賣什麼** | Care Copilot（AI 直銷關懷 copilot）— 把混亂客戶知識量產成可審核、合規、有溫度的草稿 |
| **賣給誰** | 直銷商 prosumer 自付（主 persona Amy）；Top Leader 免費+抽成（GTM 引擎） |
| **怎麼收費** | $39/mo Pro（毛利 ~77–87%）· Freemium 引流 · $129 Leader Team（Phase II） |
| **怎麼獲客** | Top Leader 抽成病毒（CAC 低）— **不靠付費廣告**（$39 撐不起 CPA） |
| **為何離不開** | 活檔案 lock-in（用越久切換成本越高）+ 跨租戶匿名資料飛輪（草稿越用越準） |
| **擋大廠** | 垂直治理深度（FTC/FDA 合規詞庫 + 直銷領域模型）= 大廠盲區（非「我們 agent 較強」） |
| **平台路徑** | 直銷=垂直#1/試煉場 → 萃取垂直無關核心 → 垂直#2(保險)證 ≥70% 複用 → 收平台乘數 |
| **募資** | Bootstrap 打 B1+單位經濟+垂直#2（pilot 約 $1–4k）→ 垂直#2 證複用後才募 seed（證據非希望） |

---

## ⚠️ Premortem → 可證偽假設映射（收斂的判準）

> [!IMPORTANT]
> 一條收斂的商業模式 = 每個殺手都有一個**同一個 pilot 可檢驗**的假設。下表全綠 = 收斂。

| # | 殺死情境 | 狀態 | 對應可證偽假設（pilot 量） |
|:--|:--|:--:|:--|
| K1 | CAC/churn 吃光（高流動） | ⚠️ 待驗 | 月 churn ≤ 8%（留存代理:每週開 App ≥4 天）+ Top Leader 病毒簽入 ≥ N |
| K2 | LLM 成本 > 月費 | ✅ 解 | 毛利 ~77–87%（caching；LLM ~$3–9/mo ≪ $39） |
| K3 | MLM 汙名 + FTC/FDA | ⚠️ 緩解 | pilot=design-partner 規模 + 品牌脫鉤 + 外送 0 踩線（合規詞庫） |
| K4 | 永遠沒有垂直#2 → 卡單一 SaaS | ⚠️ 待驗 | 垂直#2(保險)swap vertical pack 後核心複用 ≥ 70% |
| K5 | 大廠 SMB Copilot 下沉 | ⚠️ 緩解 | 垂直治理深度（FTC 合規）= 大廠盲區；pilot 證合規攔截 100% |
| K6 | 採用 ≠ 付費 ≠ 留存 | ⚠️ 待驗 | pilot 末 ≥ 4/5 教練「願付 $39 簽約」（非僅採用率高） |

---

## 📊 6 問收斂表（Forum R1–R6）

| Q | 議題 | 收斂裁決 | 輪次 |
|:--|:--|:--|:--:|
| **Q1** | 做什麼生意 | 垂直先行 + 平台後萃取（閘:單位經濟/≥70%複用/垂直#2） | ✅ R1 |
| **Q2** | 直銷對嗎 | 是，當 B1/治理試煉場；平台品牌與 MLM 脫鉤 | ✅ R2 |
| **Q3** | $39 成立嗎 | 毛利 ~77–87% 清關；真殺手 = CAC/churn 非 LLM | ✅ R3 |
| **Q4** | 護城河/降churn/擋大廠 | 活檔案 lock-in + 資料飛輪 + 垂直治理深度（大廠盲區） | ✅ R4 |
| **Q5** | 垂直#2 | 保險業務員（佔位）；證 ≥70% 複用 = 平台 thesis 成立 | ✅ R5 |
| **Q6** | 募資/跑道 | Bootstrap 至垂直#2（~$1–4k pilot）；證複用後才募 seed | ✅ R6 |

---

## 🎯 業主待確認的假設（我已估算續推，你修正即更新）

| # | 假設（合理估算） | 推導依據 | 你來修正 |
|:--|:--|:--|:--|
| **A1** | 月 churn 8% → LTV ≈ $390 → CAC 上限 ≈ $130 | LTV=$39×(1/0.08)×0.80margin；CAC=LTV/3 | 真實直銷留存/獲客數字 |
| **A2** | 垂直#2 = 保險業務員 | 關係 CRM + 合規(保險法規) + 跟進痛點 ≈ 直銷 → 複用 est ~80% | 你 Synergy 之外的溫暖入口 |
| **A3** | LLM ~$3–9/直銷商/月 | 150 草稿/月 × ~$0.015(opus+caching) ≈ $2.25 + judge/語音/緩衝；上限 $9（$0.30/日） | pilot 量實際 token |
| **A4** | pilot 12 週 burn ~$1–4k | 1 VM ~$50/mo + LLM ~$55/mo(11 人) + 法務 review 一次性 ~$1–3k | 真實報價 |

---

## 🔍 Drill-down: Forum 逐輪 critique（R1–R6）

<details>
<summary>展開 6 輪 Socratic / Elon / premortem 辯論全文</summary>

### R1 — Q1 商業身份（✅）
- Positions:A 垂直 SaaS / B 平台先行 / C 垂直先行-平台後萃取。
- Critique:A→premortem K3/K4 致命(困汙名垂直、無溢價);B→平台陷阱(建沒人付錢的基礎設施,違反驗證前不建設);C→營收養平台 thesis。
- 裁決 **C**,閘在 g1 單位經濟 / g2 ≥70%複用 / g3 垂直#2。

### R2 — Q2 直銷對嗎（✅）
- 蘇格拉底:為何直銷?真因=Synergy 溫暖 pilot(Elon:別為拿不到的 pilot 放棄手上資產)。
- 裁決:直銷=垂直#1/B1 試煉場(合規最硬=治理證明最強);**平台品牌 AEOS ≠ 垂直產品 Care Copilot**(K3 脫鉤)。

### R3 — Q3 單位經濟（✅）
- 成本堆疊:LLM ~$2.25/mo(150 草稿×$0.015,caching)、上限 $9 → 毛利 ~77–87%。
- 蘇格拉底揭穿:「毛利夠」答錯問題 → K2 降級,**K1(CAC/churn)升為頭號殺手**;付費廣告必死,只有 Top Leader 病毒撐得起。

### R4 — Q4 護城河（✅）
- 第一性原理「什麼擋 churn + 大廠」:
  - **活檔案 lock-in**:用越久、累積客戶關係資料越多 → 切換成本升 → churn 隨時間降。**早期 churn(活檔案未累積前)是風險窗** → onboarding 須前置價值。
  - **跨租戶匿名資料飛輪**:草稿採用/異議樣式聚合 → skill 更準(opt-in 匿名)。
  - **vs 大廠(K5)**:大廠 SMB Copilot 是水平通用;AEOS 護城河=**垂直治理深度**(FTC/FDA 合規 + 直銷領域)= 大廠盲區(對映 feasibility 22.8)。**不是「我們 agent 較強」**(那會被模型供應商吃)。
- 裁決:護城河三層(per-tenant lock-in / 資料飛輪 / 垂直治理深度);churn 防線=前置 onboarding 價值跨過早期窗。

### R5 — Q5 垂直#2（✅）
- 好的垂直#2 判準:≥70% 核心複用 / 體面(脫汙名) / 有溫暖入口 / 關係+合規+一線 痛點類似。
- 候選:**保險業務員**(~80% 複用,合規治理可重用,體面) > 房仲(~75%) > 診所前台(~75% 但客戶端複雜)。
- 裁決:**保險(佔位,待業主真實入口)**;**平台 thesis 的證明=直銷→保險 只換 vertical pack(領域模型+詞庫+skill+persona)即複用 ≥70%**。這就是 R1 的 g2/g3 閘門。

### R6 — Q6 募資（✅）
- bootstrap vs raise:
  - bootstrap:infra ~$50/mo + LLM ~$55/mo(11 人 pilot) + 法務一次性 ~$1–3k → 12 週 ~$1–4k,可自力。
  - raise:平台是 VC story,但**垂直#2 未證前募=賣希望**(premortem K4)。
- 裁決:**bootstrap 至 B1+單位經濟+垂直#2 證複用 → 才募 seed**(證據非希望);對齊 foundation「驗證前不建設/不過早募資」。

</details>

---

## 🔗 Cross References

- 賭注與殺死條件:[`docs/foundation/00-the-bet.md`](../foundation/00-the-bet.md) · [`03-validation-and-kill.md`](../foundation/03-validation-and-kill.md)
- 可行性與 vertical pack:[`docs/architecture/feasibility-AEOS-x-care-copilot.md`](../architecture/feasibility-AEOS-x-care-copilot.md) §6
- 護城河四層 / 藍領 wedge:`_legacy-dev_docs/01-vision-positioning.md` §22
- 格式標準:KB-12 · 品質維度:KB-06 · 資料/合規:KB-11

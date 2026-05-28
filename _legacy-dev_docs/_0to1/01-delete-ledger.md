---
id: 0TO1-01-DELETE-LEDGER
title: Delete Ledger — 對 81 份既有文件的 Elon 裁決
status: canonical
type: decision
created: 2026-05-28
rule: "若刪完沒有『這份其實要加回來』的衝動，代表刪得不夠。預測加回 < 10%。"
---

# Delete Ledger — 81 份文件的 Elon 裁決

> 這份文件就是「**幫我做決策**」本身。每一份既有文件都被判定：
> - **KEEP** — 服務核心賭注 B1–B4 或成本極低且有用，留在關鍵路徑。
> - **ARCHIVE** — 解決「想像中的未來」的問題，不刪除、退為 reference，**被觸發時再加回**。
> - **KILL** — 主動有害 / 純維護負擔 / 永遠不需要。
>
> **我沒有物理移動任何檔案。** 下方是建議。要不要把 ARCHIVE 類移到 `dev_docs/_archive-pre-0to1/`，你一句話我就做。

---

## 裁決摘要

| 判定 | 份數 | 含義 |
|---|---:|---|
| **KEEP**（active path） | ~12 | + `_0to1/` 5 份 = 關鍵路徑共 ~17 份 |
| **ARCHIVE** | ~63 | 退為 reference，被觸發再加回 |
| **KILL** | ~2 | 純負擔 |

**文件白癡指數**：81 → ~17 active（含種子）。**砍掉 ~79%。** 預測「加回」清單 < 8 份（< 10%，見 §7）→ 符合 Elon「刪得夠」的訊號。

---

## 1. 根目錄敘事檔（12 份）

| 檔案 | 判定 | 一句話理由 |
|---|---|---|
| `00-executive-summary.md` | **ARCHIVE** | 決策功能被 `_0to1/00-the-bet` 取代；保留為 pitch 開場素材 |
| `01-vision-positioning.md` | **ARCHIVE→ref** | 願景/護城河論述，募資時讀；不擋開工 |
| `02-product-architecture.md` | **ARCHIVE→ref** | 894 行架構藍圖，描述還沒存在的系統；切片只需 build-sheet 那一頁 |
| `03-execution-onboarding.md` | **ARCHIVE→ref** | 847 行服務交付方法論；pilot 跑過一次才知道對不對，先別固化 |
| `04-strategy-business.md` | **ARCHIVE→ref** | 商業模式論述，募資用 |
| `05-investor-thesis.md` | **ARCHIVE→ref** | 投資論述/十年護城河；募資時用，**不擋開工** |
| `06-risk-boundaries.md` | **KEEP-lite** | 不採納清單（Non-goals）+ 紅線是真護欄，**便宜且防走偏**；濃縮版進 build-sheet |
| `07-north-star.md` | **KEEP** | 第一性原理願景算對了，`_0to1` 建立其上；留著當北極星，但**離開 build 關鍵路徑** |
| `99-conclusion.md` | **ARCHIVE** | 收束文，無決策功能 |
| `README.md` | **KEEP-lite** | 改指向 `_0to1/`；雙版維護 SOP 那段 KILL（whitepaper 不再維護雙版） |
| `STRATEGY-NORTHSTAR.md` | **ARCHIVE→ref** | 與 07 重疊 |
| `LAUNCH-DASHBOARD.md` | **KEEP** | 「現在在哪」單一入口有用；但 repoint 必讀清單到 `_0to1`，砍掉指向 ARCHIVE 檔的連結 |

---

## 2. ADR（10 份）— 只留真正綁住切片的決策

| 檔案 | 判定 | 一句話理由 |
|---|---|---|
| `ADR-0002-agent-runtime.md`（Frozen Runtime） | **KEEP** | 學習/生產分離是身份，切片就要這條鐵律 |
| `ADR-0010-memory-architecture.md`（五層記憶） | **KEEP-lite** | B3 核心；但切片只需 L1/L2/L3，L4/L2.5 標 Phase 2 |
| `ADR-0005-data-retention-pii.md` | **KEEP-lite** | 碰真實客戶資料前必須有；濃縮成「pilot 期 PII 規則」 |
| `ADR-0001-llm-provider-strategy.md` | **ARCHIVE** | 「用哪個模型」折成 build-sheet 一行；多模型抽象層是 Phase 2 |
| `ADR-0007-tenant-isolation.md` | **ARCHIVE** | 單一 pilot 租戶，**現在沒有「跨租戶」問題**；多租戶量產時加回 |
| `ADR-0003-skill-registry.md` | **ARCHIVE** | 切片只有 1 個 skill，不需要 registry |
| `ADR-0004-deployment-model.md` | **ARCHIVE** | 0 LOC，沒東西可部署 |
| `ADR-0006-auth-identity.md` | **ARCHIVE** | 切片用最簡單的 token，正式 auth 延後 |
| `ADR-0008-observability-stack.md` | **ARCHIVE** | 先 log to stdout / 一張 Grafana；完整 stack 過早 |
| `ADR-0009-prompt-versioning.md` | **ARCHIVE** | 切片用 git 管 prompt 就夠 |

> 反模式提醒：10 份 ADR 裡有 7 份在「決定還沒存在系統的架構」。ADR 應該記錄**被迫做的取捨**，不是預先規劃所有可能的取捨。

---

## 3. Contracts（19 份）— 想像中未來規範的重災區

| 檔案 | 判定 | 一句話理由 |
|---|---|---|
| `API-002-line-webhook.md` | **KEEP-lite** | LINE webhook 是切片真實入口，要實作 |
| `db-schema.md` | **KEEP-lite** | 切片需要存對話/知識/audit；但只留切片用到的 3–4 張表，其餘 ARCHIVE |
| `QUOTA-001-llm-budget.md` | **KEEP-lite** | B4 成本護欄，真實；濃縮成「pilot LLM 上限 $300/月」 |
| `BF-001-customer-onboarding.md` | **KEEP-lite** | pilot onboarding 端到端流程，要走一次；簡化版 |
| `SEC-001-threat-model.md` | **ARCHIVE（抽 4 項）** | 完整威脅模型過早；只抽 §6.1 的 HMAC 驗證 / RLS / secret scanning / TLS 進 build-sheet checklist |
| `MC-001 ~ MC-011`（11 份微服務契約） | **ARCHIVE** | **沒有微服務。** 切片是單體。11 份 bounded-context 契約全部過早 |
| `SAD-v0.1.md` | **ARCHIVE→ref** | 系統架構描述還沒存在的系統 |
| `domain-model.md` | **ARCHIVE→ref** | DDD 模型過早；切片用最樸素的資料結構 |
| `API-001-internal.md` | **ARCHIVE** | 沒有內部服務要互調 |
| `API-003-third-party-integrations.md` | **ARCHIVE** | 第三方整合是 Phase 2 |
| `NFR-001-non-functional-requirements.md` | **ARCHIVE** | 性能/可用性指標，沒系統可量；pilot 期只追「草稿採用率」 |
| `OBS-001-observability-spec.md` | **ARCHIVE** | 完整可觀測規範過早；切片 log to stdout + 數採用率 |
| `UF-001-to-005-user-flows.md` | **ARCHIVE（抽 1 條）** | 只留 pilot 主流程那條，其餘 ARCHIVE |
| `SF-001-to-005-system-flows.md` | **ARCHIVE** | 系統流程圖描述未建系統 |
| `UX-001-wireframe.md` | **ARCHIVE→ref** | 切片是 LINE + 草稿審核台，wireframe 可後補 |
| `AC-001-to-005-acceptance-criteria.md` | **ARCHIVE** | 驗收標準折進 `_0to1/03-validation` |
| `TEST-001-test-plan.md` | **ARCHIVE** | 測試計畫折進 `_0to1/03-validation`；切片邊寫邊測 |
| `traceability-matrix.md` | **KILL** | 追溯 81 份正在離開路徑的文件——純維護負擔，砍 |
| `flow-index.md` | **KILL** | 索引 ARCHIVE 的流程檔，自動生成的負擔 |
| `LEGAL-001-DPA-template.md` | **KEEP-lite** | 簽 pilot 拿真實資料前要 DPA，真實需求 |
| `LEGAL-002-SOW-template.md` | **ARCHIVE** | SOW 等真的要簽約時再說 |

---

## 4. Process（7 份）— 0 LOC 不需要運維

| 檔案 | 判定 | 一句話理由 |
|---|---|---|
| `PILOT-001-success-criteria.md` | **KEEP（folds in）** | 成功/失敗標準是 B1–B4 核心，內容併入 `_0to1/03-validation` |
| `RUNBOOK-001-incident-response.md` | **ARCHIVE** | 沒系統可出事 |
| `RUNBOOK-002-deploy-rollback.md` | **ARCHIVE** | 沒東西可部署/回滾 |
| `RUNBOOK-003-backup-dr.md` | **ARCHIVE** | 沒資料可備份 |
| `PROJ-001-90day-sprint-plan.md` | **ARCHIVE** | 13 週計畫被 build-sheet 壓縮版取代 |
| `PLAYBOOK-001-cs-escalation.md` | **ARCHIVE** | 升級流程等真有客服量再寫 |
| `HIRING-001-role-jds.md` | **KILL** | 驗證前不招人；招募 JD 是純未來想像 |

---

## 5. Exploration（4 份）— 唯一接近「該做的事」的叢集

| 檔案 | 判定 | 一句話理由 |
|---|---|---|
| `PRD-001-7day-ai-cs-onboarding.md` | **KEEP** | 最接近 MVG 的真實產品範圍；build-sheet 精煉它，**CEO 本週要把它從 draft 轉 active** |
| `COST-MODEL-2026-05.md` | **KEEP** | B4 單位經濟，真實；pilot 跑道計算靠它 |
| `PILOT-ICP-2026-05.md` | **KEEP** | 「找誰當第一個客戶」，本週最重要的文件之一 |
| `CTO-team-build-plan-2026-05-14.md` | **ARCHIVE** | 組隊計畫，驗證後才有意義 |

---

## 6. Appendices（10）+ Visual Prompts（5）+ 其他

| 叢集 | 判定 | 一句話理由 |
|---|---|---|
| `appendices/A-glossary.md` | **KEEP-lite** | 共用詞彙便宜有用 |
| `appendices/E-three-mantras.md` | **KEEP-lite** | 記憶錨點便宜 |
| `appendices/I-7-day-package.md`、`H-onboarding-wizard-ux.md`、`F-onboarding-checklist.md` | **ARCHIVE→ref** | 與 PRD-001 重疊的交付細節，pilot 時參考 |
| `appendices/C-pre-launch-checklist.md` | **ARCHIVE（抽真項）** | 抽 §C.1–C.5 真正擋上線的紅項進 build-sheet，其餘 ARCHIVE |
| `appendices/B、D、G、J` | **ARCHIVE** | 決策矩陣/參考實作/容器化/履歷模板，全部過早 |
| `visual-prompts/*`（5 份） | **ARCHIVE** | 投影片生圖 prompt，純對外敘事支援 |
| `superpowers/specs/...northstar-design.md` | **KEEP→ref** | 07 北極星的設計源稿，留著 |
| `whitepaper.md`（根，4519 行） | **ARCHIVE-snapshot** | 凍結為快照，**停止雙版維護**（這是最大的隱形負擔來源） |
| `agent_x.md`（根，109K） | **❓ OUT-OF-SCOPE** | 不在 dev_docs，內容未知；請你確認這是什麼，再決定去留 |

---

## 7. 「加回 10%」預測清單（Elon 第 2 步的誠實檢查）

刪完後，我**預測**以下幾份會在賭注被驗證、進入 scale 階段時**需要加回**（按觸發條件）：

| 加回的檔案 | 觸發條件 |
|---|---|
| ADR-0007 租戶隔離、MC 系列契約 | 簽到第 2 個租戶、要拆服務時 |
| OBS-001、RUNBOOK 系列、NFR-001 | 切片上 production、有真實流量時 |
| ADR-0008 觀測 stack、ADR-0006 auth | 同上 |
| 05-investor-thesis、04-strategy | 開始正式募資輪時 |
| HIRING-001、CTO-team-build-plan | 拿到資金、要擴編時 |

**共 ~7 份 < 81 的 10%。** → 刪得夠（若這清單超過 8 份，代表我刪過頭，該把其中幾份從 ARCHIVE 拉回 KEEP）。

> 注意：「加回」永遠是**被真實事件觸發**才加，不是「為了完整性」預先加。這是整個 ledger 的靈魂。

---

## 8. 建議的物理動作（等你授權）

```bash
# 我不會擅自執行。授權後我做：
mkdir -p dev_docs/_archive-pre-0to1
# 將上表所有 ARCHIVE / KILL 類別 git mv 進去（git 可追、可還原）
# KEEP / KEEP-lite 留原地
# 更新 LAUNCH-DASHBOARD 與 root README 的連結指向 _0to1
```

要執行的話跟我說「執行歸檔」。要先看看完整移動清單也可以。要推翻任何一份判定，直接講——Elon 第 2 步允許刪錯了再加回。

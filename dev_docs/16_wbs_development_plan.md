# WBS 開發計劃 - care-copilot（最薄切片 / B1）

> **版本:** v1.0 | **更新:** 2026-05-29 | **狀態:** 草稿
> **負責人:** PM（CEO 戴帽） | **審核:** TL | **追蹤:** E-0001~E-0005 / US-0001~0011
> **來源:** `docs/foundation/02-mvg-build-sheet.md`（handoff，開工順序）+ `docs/foundation/03-validation-and-kill.md`（閘門/殺死條件）

---

## 1. 專案總覽

| 項目 | 內容 |
| :--- | :--- |
| **專案名稱** | care-copilot（AEOS 核心切片 ai-cs-mvg / B1） |
| **專案經理** | CEO（戴 PM 帽） |
| **技術主導** | coding agent（依 foundation/02 handoff） |
| **總工期** | 約 6 週（W0 簽 pilot → W6 Go/Kill） |
| **目前進度** | PRD frozen，待開工（W1 ingest+draft+eval） |

### 角色與職責（5 內部 owner，種子前 founder 戴帽，但帽子必須有名字）

| 角色（帽子） | 種子前由誰戴 | 職責 | 觸發換真人 |
| :--- | :--- | :--- | :--- |
| PM / CEO | CEO | 賭注是否成立、Go/Kill 裁決、簽 pilot、預算/跑道 | — |
| 安全 owner | CEO + arch persona | threat-model、跨租戶/注入/secret 對抗驗證 | pilot 接真資料 / tenant > 5 / 外部 pentest |
| 法務 owner | CEO + 一次性外部法務 | DPA 簽核、詞庫法源 sign-off | 碰真客戶 PII 前（W0）必須一次外部 sign-off |
| AI-Architect / 資料 owner | CEO + qa persona | 50 題測試集 / 200 標註 / 50 詞庫真值維護 | B1 打不動 / 需領域標註者 |
| SRE-ops owner | CEO（唯一 oncall） | runbook、RPO/RTO、secret 輪替、還原演練 | tenant > 5 / 第一次 P0 incident |

---

## 2. WBS 結構

> **開工順序按「最快看到一則真實草稿」排，不按架構分層**（foundation/02 §5）。W1 結束就能用 eval.py 打 B1——最致命賭注最早驗，LINE 串接晚於「知道知識可不可用」。

```text
0.0 市場與法務前置（W0，硬閘門）
├── 0.1 簽 pilot（≥1 位 Synergy 教練，OQ-002）
├── 0.2 簽 DPA + 一次外部法務 sign-off
└── 0.3 FTC/FDA 詞庫法源 + 50 詞 sign-off

1.0 W1 — 離線打 B1（最致命賭注最早驗）
├── 1.1 ingest.py：貼 markdown → pgvector，手驗檢索
├── 1.2 draft.py（離線版）：問題字串 → 檢索 → Claude 產草稿 → print
└── 1.3 eval.py：吃 testset.csv，跑 50 題，印 pass rate ← 打 B1 硬閘門

2.0 W2 — 全鏈路 + 治理鐵律
├── 2.1 webhook.py：LINE 收訊（HMAC 驗簽）→ message(role=user)
├── 2.2 串接：收訊自動產草稿存 DB + 通知 expert
├── 2.3 review.py：approve/edit/reject；approve→LINE 回發；edit 重跑 gate
├── 2.4 killswitch.py：一個 flag 全停（30s）
└── 2.5 policy / audit 橫切：合規 gate + append-only 稽核

3.0 W3 — 真知識上線 Draft Mode
└── 3.1 接真 pilot 教練的真知識 + 真 LINE，開始量採用率

4.0 W4–W6 — 量採用率 + Go/Kill
├── 4.1 連續量採用率 ≥ 2 週穩定讀數
└── 4.2 W6 Go/Kill 決策點
```

### 工作包統計（pilot 估算，h = 理想人時）

| WBS 模組 | 對應 Epic/US | 估工時 | 狀態 |
| :--- | :--- | :--- | :--- |
| 0.0 市場/法務前置 | Q-0001 / RISK-002 | — (CEO+法務) | 待辦 |
| 1.0 W1 離線打 B1 | E-0001/E-0002/E-0005 | ~40h | 待辦 |
| 2.0 W2 全鏈路+鐵律 | E-0003/E-0004 | ~60h | 待辦 |
| 3.0 W3 真知識上線 | E-0001 | ~20h | 待辦 |
| 4.0 W4–W6 量採用率 | E-0005 | — (運維) | 待辦 |
| **合計** | | **~120h + 運維** | — |

---

## 3. 詳細任務分解

> 📎 每個任務對應 02 PRD 的 `US-NNNN`，工時以該 US 範圍為基準。

### 模組: 1.0 W1 離線打 B1

| 編號 | 任務 | 對應 US | 負責人 | 工時 | 狀態 | 依賴 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1.1.1 | `ingest.py`：markdown chunk → embed → pgvector | US-0001 | DEV | 12h | 待辦 | 0.0 |
| 1.1.2 | KnowledgeRouter structured contact 7 欄位抽取 | US-0002 | DEV | 8h | 待辦 | 1.1.1 |
| 1.2.1 | `draft.py`：檢索 + Claude 產草稿（grounded） | US-0003 | DEV | 10h | 待辦 | 1.1.1 |
| 1.2.2 | needs-human guard（缺依據標記，不幻覺） | US-0005 | DEV | 4h | 待辦 | 1.2.1 |
| 1.3.1 | `eval.py`：testset 50 題 → pass rate | US-0011 | DEV | 6h | 待辦 | 1.2.1 |

**模組小計**: ~40h ｜ **硬閘門**：W1 pass rate < 50% 且補救無效 → 立即停，**不准進 W2**。

### 模組: 2.0 W2 全鏈路 + 治理鐵律

| 編號 | 任務 | 對應 US | 負責人 | 工時 | 狀態 | 依賴 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2.1.1 | `webhook.py`：LINE 收訊 + HMAC 驗簽 | US-0012 | DEV | 8h | 待辦 | 1.0 |
| 2.2.1 | 串接：收訊自動產草稿 + 通知 expert | US-0003 | DEV | 6h | 待辦 | 2.1.1 |
| 2.3.1 | `review.py`：approve/edit/reject + 回發 | US-0006 | DEV | 12h | 待辦 | 2.2.1 |
| 2.3.2 | edit 必重跑合規 gate（C2，不可繞紅燈） | US-0006 | DEV | 4h | 待辦 | 2.3.1 |
| 2.4.1 | `killswitch.py`：flag 全停（30s）+ 心跳 | US-0008 | DEV | 4h | 待辦 | 1.0 |
| 2.5.1 | `policy`：regex 詞庫 gate（green/yellow/red） | US-0004 | DEV | 10h | 待辦 | 0.3 |
| 2.5.2 | `audit`：append-only 稽核 + 寫敗回滾 | US-0007 | DEV | 8h | 待辦 | 2.2.1 |
| 2.5.3 | Frozen 包覆（不自改/不自裝/不自由載 MCP） | US-0009 | DEV | 6h | 待辦 | 1.0 |
| 2.5.4 | RLS migration + 跨租戶紅隊（TC-SEC-01） | US-0010 | DEV+SEC | 8h | 待辦 | — |

**模組小計**: ~60h ｜ **鐵律 gate**：跨租戶/踩線/未審自動發 任一破 = 不上線。

---

## 4. 進度摘要

| 項目 | 當前值 | 目標值 |
| :--- | :--- | :--- |
| 整體進度 | 0%（PRD frozen） | 100% |
| B1 測試集 pass rate | — | ≥ 70%（W1）/ ≥ 80%（pilot 末） |
| 草稿原樣 approve 率（北極星 K1） | — | ≥ 50% |
| 鐵律違規（跨租戶/踩線/未審發） | — | = 0（1 次都不行） |

---

## 5. 風險管理

| 風險 | 可能性 | 影響 | 緩解策略 | 負責人 |
| :--- | :--- | :--- | :--- | :--- |
| RISK-001 B1 死（採用率 < 40%） | 中 | 致命 | W1 eval 早驗；採用率崩即 Kill 不續寫 | CEO |
| RISK-002 8 週簽不到 pilot | 中 | 致命 | W0 先簽 + 簽 DPA | GTM/CEO |
| RISK-003 知識品質差致幻覺 | 中 | 高 | ingest 品質檢查 + needs_human + expert 回流 | AI-Architect |
| RISK-004 客戶個資外洩 | 低 | 致命 | RLS + 驗簽 + secrets 不進 git + DPA | 安全 owner |

---

## 6. 里程碑

| 里程碑 | 預計（相對 W0） | 交付物 | 狀態 |
| :--- | :--- | :--- | :--- |
| M0: 市場/法務前置 | W0 | 簽 pilot + DPA + 詞庫 sign-off | 待辦 |
| M1: W1 打 B1 | W1 | `eval.py` 對真 50 題出 pass rate | 待辦 |
| M2: 全鏈路 + 鐵律 | W3 | 收訊→草稿→審核→稽核 跑通；killswitch/RLS/Frozen | 待辦 |
| M3: 量採用率 | W4–W6 | ≥ 2 週穩定採用率讀數 | 待辦 |
| **M4: W6 Go/Kill** | W6 | Go（approve≥50% + 採用≥70% + 毛利≥50% + 1 pilot 跑通 2 週）或 Kill/Pivot | 待辦 |

### Go/Kill 預先承諾（foundation/03，現在簽、W6 不准賴）

```text
KILL：總採用 < 40% / reject > 30% / 毛利長期為負無轉正 / 8 週簽不到 pilot
PIVOT：採用率 40–50% 限再調 2 輪 / B3 零件互換做不到（降 Phase 2）
GO：approve≥50% 且採用≥70% 且每則省時≥50% 且毛利≥50% 且 ≥1 pilot 跑通 2 週
```

> **承諾**：任一 KILL 訊號觸發即停手、retro、pivot 或收掉，**不准用「再寫一版文件 / 再補一輪願景」逃避**。

---

## 變更紀錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v1.0 | 2026-05-29 | 依模板 16 從 mvg-build-sheet（開工順序）+ validation-and-kill（閘門）實例化 |

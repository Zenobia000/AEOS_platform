# AEOS — AI 員工製造工廠（專案文件）

> **北極星**：把「製造一位能上班的 AI 員工」從數月的人工工程，變成數天、近乎零邊際成本的工廠量產——且這條產線越用越快、越用越便宜。
>
> **唯一賭注**：一條半自動產線，能把「一個客服職位 + 一坨真實混亂知識」，在 7 天內、人類只簽核一次，量產出一位能在 LINE 上對真實客戶訊息產生「可被人類採用的草稿回覆」的 AI 員工。
>
> **唯一要盯的數字**：草稿原樣 approve 率。

---

## 這份 docs/ 的定位

從第一性原理重置而來的**乾淨關鍵路徑**。先前的 81 份企業級規範 corpus 已退役（保存於 git history，pre-0to1 `_legacy-dev_docs/`），其理念提煉於下方 `foundation/`，其餘細節在被真實事件觸發時才從 git history 叫回——不是被焦慮叫回。

## 結構

```
docs/
├── README.md              ← 你在這裡
├── foundation/            ← 專案憲法（提煉自第一性原理，做決策的唯一依據）
│   ├── 00-the-bet.md          唯一賭注 + 白癡指數 + B1~B5 子賭注 + 殺死條件
│   ├── 01-north-star.md       10 年工廠願景 + 五支柱 + Elon 五步工作法 + 紅線/Non-goals
│   ├── 02-mvg-build-sheet.md  最薄垂直切片 + 開工順序 + 鐵律（coding agent handoff）
│   └── 03-validation-and-kill.md  可證偽實驗 + 北極星數字 + 殺死訊號 + 簽名承諾
│
└── （以下由 devteam 工作流逐 phase 產出）
    0-discovery/   PRD …
    1-analysis/    System Spec / User Flow …
    2-architecture/ ADR / C4 / NFR …
    3-design/      OpenAPI / ERD …
    4-delivery/    Test Plan …
    5-release/     Runbook / Release Readiness …
```

## 怎麼用

| 角色 | 路徑 |
|---|---|
| **CEO / 創辦人** | 讀 `foundation/00` → `03`。本週只做兩件事：簽 1 個 pilot、把 `03` 的殺死條件變成對自己的書面承諾。 |
| **要開工的 coding agent** | `foundation/02-mvg-build-sheet.md` 就是 handoff，讀完能直接開工。 |
| **要做架構/契約決策** | 走 devteam 工作流（`/devteam`），產出落在對應 phase 目錄。 |

## 鐵律（任何切片都不准省）

1. 學習/生產分離（Frozen Runtime：上線配置凍結，回饋資料離線改版）
2. 草稿模式強制（碰真客戶階段 AI 永不自動發訊，人類審每一則）
3. Kill switch（30 秒內全停，第一週就要有）
4. Audit 全覆蓋（每則訊息記：用了哪些知識 + 哪個 model + 人類決定）
5. PII 紅線（HMAC 驗簽 / secrets 不進 git / TLS / tenant_id 強制 scope；簽 pilot 前先簽 DPA）

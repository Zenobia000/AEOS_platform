# CIA-NNNN: [變更影響分析標題]

> **檔名:** `CIA-NNNN-<short-kebab-slug>.md`（例：`CIA-0005-upgrade-stripe-v2-to-v3.md`）
> **版本:** v1.0 | **更新:** YYYY-MM-DD | **狀態:** 草稿/審核中/已批准/已歸檔
> **負責人:** ARCH | **審核:** TL + 受影響模組 owner | **追蹤:** CR-NNNN（觸發來源）

---

## 0. 用途與適用時機

CIA 是觸碰以下任一面向**前**的硬 gate（不可繞過，未完成 §8 Human Decisions 不可動 code）：

- User flow / Business flow（新增/修改 BF/UF/SF；改變主流程或例外流程）
- API contract（新增/刪除 endpoint；schema / error code / 版本變動）
- Domain model（新增 entity；改變 invariant、關聯、生命週期）
- DB schema（新增/刪除 table / column / index；需 migration）
- External integration（新接 vendor；改 callback / retry / auth）
- Architecture boundary（新增 module / service；移動 bounded context）

**豁免**：純 typo、格式調整、單 function 內 bug fix（無 contract 影響）、tier-3 process 文件編輯。

## 1. 變更摘要

- **觸發來源:** CR-NNNN
- **變更類別:** flow / contract / data / architecture / external（多選）
- **一句話描述:** [做什麼，為什麼]

## 2. 受影響資產（Affected Artifacts）

| 類別             | ID / 路徑                | 變動類型                         | 風險等級  |
| -------------- | ---------------------- | ---------------------------- | ----- |
| User Flow      | UF-NNNN                | 新增 / 修改 / 刪除                 | 高/中/低 |
| Business Flow  | BF-NNNN                |                              |       |
| Subsystem Flow | SF-NNNN                |                              |       |
| API            | `POST /v1/orders`      | breaking / non-breaking      |       |
| ADR            | ADR-NNNN               | 需 superseded / amended       |       |
| Module         | MOD-NNNN               |                              |       |
| Data           | `orders.status` column | add / drop / rename / retype |       |
| External       | Stripe API v2 → v3     |                              |       |

## 3. 風險評估

| 風險              | 可能性   | 衝擊    | 緩解策略                      |
| --------------- | ----- | ----- | ------------------------- |
| 既有客戶 API 客戶端崩潰  | 高/中/低 | 高/中/低 | 雙寫期 / version negotiation |
| 資料 migration 失敗 |       |       | 預先 dry-run / canary       |
| 第三方 SLA 變動      |       |       | 備援 vendor                 |

## 4. 兼容性策略

- **向後相容路徑:** [雙寫？version header？feature flag？]
- **棄用時程:** [既有 API 何時退役，提前通知客戶幾天]
- **資料 migration:** [線上 migration 還是 offline？分批還是一次？]

## 5. 測試影響

| 測試類別 | 受影響範圍             | 需新增 | 需修改 |
| ---- | ----------------- | --- | --- |
| 單元測試 | TC-NNNN ~ TC-NNNN | X 個 | Y 個 |
| 整合測試 |                   |     |     |
| E2E  |                   |     |     |
| 契約測試 |                   |     |     |
| 負載測試 | 是否需要重跑基準？         |     |     |

## 6. Rollback 策略

- **回滾觸發條件:** [錯誤率 > X%、SLO 跌破 Y、客戶投訴 > Z]
- **回滾方式:** [code rollback / DB rollback / feature flag off]
- **回滾後資料狀態:** [是否仍然一致？需 compensating action？]
- **無法回滾的部分:** [明確列出 point-of-no-return]

## 7. 對外通訊

| 對象        | 內容       | 時機      | 渠道                  |
| --------- | -------- | ------- | ------------------- |
| 既有 API 客戶 | API 變動公告 | 上線前 X 天 | email + status page |
| 內部團隊      | 部署通知     | 上線當天    | Slack               |
| 客服        | FAQ 更新   | 上線前 1 天 | knowledge base      |

## 8. 🛑 Human Decisions Required（**必填**）

未填完此段 → **不可動 code**。

| #   | 待決問題                 | 選項                | 決策者  | 結論  | 日期         |
| --- | -------------------- | ----------------- | ---- | --- | ---------- |
| 1   | [例：是否雙寫期？]           | A: 雙寫 2 週 / B: 直切 | ARCH |     | YYYY-MM-DD |
| 2   | [例：誰負責資料 migration？] | A: SRE / B: DBA   | TL   |     |            |
| 3   | [例：是否需 ADR？]         | A: 升級 / B: 不升級    | ARCH |     |            |

## 9. Suggested Implementation Order

按順序執行，每步驟完成才能進下一步：

1. [ ] §8 所有 Human Decisions 已裁決
2. [ ] 對應 ADR 草案（若升級）
3. [ ] 受影響 ADR 標記 amended / superseded
4. [ ] Migration script 撰寫 + dry-run
5. [ ] Code 變更（含雙寫邏輯，若有）
6. [ ] 測試補齊（§5 列出的所有項）
7. [ ] Staging 部署 + 驗證
8. [ ] 對外通訊（§7）
9. [ ] Production 部署
10. [ ] 監控 ≥ 1 週確認穩定
11. [ ] 移除雙寫 / 棄用舊 API（若適用）
12. [ ] 更新 INDEX.md / ADR 索引 / Traceability
13. [ ] CR-NNNN 標記 closed

## 10. 歸檔

實作完成後，CIA 不刪除，狀態改為「已歸檔」並補充：

- **實際工時:** [vs 預估]
- **與預期的偏差:** [若有，記錄學到的教訓]
- **後續監控結論:** [上線後 N 週的觀察]

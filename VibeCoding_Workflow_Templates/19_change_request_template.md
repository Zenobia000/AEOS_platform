# CR-NNNN: [簡短變更標題]

> **檔名:** `CR-NNNN-<short-kebab-slug>.md`（例：`CR-0023-deprecate-v1-api.md`）
> **版本:** v1.0 | **更新:** YYYY-MM-DD | **狀態:** 提議/審核中/已批准/已駁回/已實作/已關閉
> **負責人:** [提出者] | **審核:** TL + ARCH | **追蹤:** US-NNNN, ADR-NNNN（觸發來源）
> **是否需 CIA:** 是/否（觸碰 flow/contract/data/architecture → 必填 CIA-NNNN）

---

## 1. 變更類別

勾選一項：

- [ ] 新需求（產品端新增功能）
- [ ] Spec 衝突（既有文件互相矛盾或與實作不符）
- [ ] Bug 修復（規格層級的修正，非單純程式碼 bug）
- [ ] 技術債清償
- [ ] 合規 / 安全要求
- [ ] 其他：______________

## 2. 觸發背景

- **發現者:** [人員 / 角色]
- **發現時機:** [開發中 / 上線後 / 審查時 / 客戶反饋]
- **原始問題:** [一句話描述，附 issue / Slack link]
- **若不變更會怎樣:** [量化影響：用戶數、營收、合規風險]

## 3. 影響範圍

| 維度 | 受影響項目 |
| :--- | :--- |
| 文件 | 列出受影響的模板實例（如 `02_prd.md §3`、`06_api.md /v1/orders`） |
| 模組 | 列出受影響的 `MOD-NNNN` |
| API | 列出受影響的端點（method + path） |
| 資料 | 是否需要 migration？schema 變動？ |
| 流程 | 是否變動使用者流程 / 業務流程？ |
| 第三方 | 是否變動 vendor / SDK 版本 / 依賴？ |

### 是否需要 CIA？

若上表任一項勾選「flow / contract / data / architecture」→ **必須先跑 CIA**（見 `20_change_impact_analysis.md`），CIA-NNNN 填回本檔頭部。

## 4. 提議方案

### 4.1 方案 A（推薦）

- 描述：
- 工時估算：
- 風險：

### 4.2 方案 B（替代）

- 描述：
- 工時估算：
- 與 A 的取捨：

### 4.3 不做（Do Nothing）

- 後果：

## 5. 裁決紀錄

| 日期 | 裁決者 | 結論 | 理由 |
| :--- | :--- | :--- | :--- |
| YYYY-MM-DD | [TL / ARCH / PM] | 批准方案 A / 駁回 / 要求補資料 | [一句話] |

**最終決定:** ☐ 批准 ☐ 駁回 ☐ 延期 ☐ 升級為 ADR-NNNN

## 6. 實作追蹤

| 項目 | 連結 / ID |
| :--- | :--- |
| 對應 ADR（若升級） | ADR-NNNN |
| 對應 CIA | CIA-NNNN |
| 受影響 ADR（需更新） | ADR-NNNN（標 superseded 或 amended） |
| PR / Commit | [link] |
| 受影響 TC（需修改） | TC-NNNN |
| 部署 / 上線時間 | YYYY-MM-DD |

## 7. 關閉條件

- [ ] 所有受影響檔案已更新
- [ ] 對應 TC 已通過
- [ ] 受影響 ADR 已標記 superseded（若適用）
- [ ] 部署完成且監控正常 ≥ 1 週
- [ ] 通知所有 stakeholder

**關閉日期:** YYYY-MM-DD | **關閉人:** [TL / PM]

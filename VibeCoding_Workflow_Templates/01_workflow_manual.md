# 產品開發流程使用說明書

> **版本:** v2.1 | **更新:** YYYY-MM-DD | **狀態:** 活躍
> **負責人:** PM + TL | **適用範圍:** 全域（所有模式：完整流程 / MVP）

---

## 1. 使用原則

- **以文檔為契約**: 所有決策以文檔為單一事實來源 (SSOT)
- **小步快跑**: 優先小批量交付，保留 ADR 以利回溯
- **風險前置**: 用審查 Gate 降低重大偏差風險
- **模式可升降級**: MVP 可升級為完整流程；完整流程可在低風險子專案降級

**角色縮寫 (RACI):** PM / TL / ARCH / DEV / QA / SRE / SEC / OPS

---

## 2. 模式選擇

| 條件 | 完整流程 | MVP 快速迭代 |
| :--- | :--- | :--- |
| 金流/法遵/隱私資料 | V | |
| 高可用與規模化 | V | |
| 跨 3+ 團隊協作 | V | |
| 快速驗證價值假設 | | V |
| 時間/預算有限 | | V |

**升級觸發**: 觸及敏感資料、DAU > 10k / TPS > 100、引入新服務/多團隊、轉為核心營收

---

## 3. 模式 A: 完整流程

```mermaid
graph LR
  A0[Kickoff] --> A1[PRD] --> A2[架構設計] --> A3[模組/API] --> A4[開發驗證] --> A5[品質Gate] --> A6[上線]
```

| 階段 | 目標 | 產出 | Gate |
| :--- | :--- | :--- | :--- |
| A0 啟動 | 對齊目標、邊界、風險 | 啟動簡報、里程碑 | 利益相關者共識 |
| A1 PRD | 定義問題、受眾、範圍、KPI | `02_prd.md` | PRD 簽核、KPI 可量測 |
| A2 架構 | 系統邊界、技術選型、NFR | `05_architecture.md` + `04_adr.md` | ADR 齊備、NFR 可驗證 |
| A3 詳細設計 | 可實作規格與契約 | `07_module.md` + `06_api.md` + `08_structure.md` | 契約穩定、測試策略完整 |
| A4 開發 | 增量交付 | 程式碼、測試、建置產物 | 測試綠燈、覆蓋率達標 |
| A5 品質 | 消除高風險弱點 | `13_security.md` | 高/中風險已整改 |
| A6 上線 | 可靠性、可觀測性就緒 | Go/No-Go 簽核 | SLO/Alert 就緒、回滾演練通過 |

**跨階段**: 變更需更新 ADR 與相依文檔；重大變更需重過 Gate。

---

## 4. 模式 B: MVP 快速迭代

```mermaid
graph LR
  B0[Tech Spec] --> B1[Iter 1] --> B2[Iter 2] --> Bn[Iter n] --> BL[Light Launch]
```

### B0 Sprint 0: Tech Spec

一份輕量文件合併 PRD/SA/SDD/API 最小集合：

- 問題/目標用戶/成功指標 (最多 3 條)
- 高層設計 + 1 張元件圖
- 必要 API 契約 (僅核心端點)
- 1-2 張資料表 Schema
- 風險與手動替代方案

### B1-Bn 迭代循環

- 每次交付: 可運行版本 + 指標驗證 + 回顧
- 最低限度: 安全檢查 (Secrets/認證/輸入驗證) + 可觀測性 (日誌/健康檢查)

### MVP 上線 Gate

- [ ] 有最小可運營 Runbook
- [ ] 資料備份已啟用
- [ ] 風險與債務列入後續 Backlog

---

## 5. 文檔產出對照

| 階段 | 完整流程 | MVP |
| :--- | :--- | :--- |
| 規劃 | `02_prd.md` | Tech Spec PRD 區塊 |
| 架構 | `05_architecture.md` + `04_adr.md` | Tech Spec SA/ADR 區塊 |
| 規格 | `07_module.md` + `06_api.md` | Tech Spec SDD/API 區塊 |
| 品質 | `13_security.md` | 簡化安全檢查 |
| 結構 | `08_structure.md` | Tech Spec 結構區塊 |

---

## 6. Quality Gates (QG-G0 ~ QG-G4)

五個量化關卡，對應 §3 完整流程與 §4 MVP 模式。每個 Gate 都有**必備產出**、**量化判準**、**簽核 RACI**，避免「90% 完成度」這類無法稽核的軟判準。

### QG-G0: Ready to Design

**目標**: PRD 已穩定，可進入架構設計。

| 維度 | 判準（量化） |
| :--- | :--- |
| 必備產出 | `02_prd.md`（含 E-/US- 編號）、KPI 表、Q-001~ 待澄清清單 |
| 完成度 | Q-001~ 數量 ≤ 3 且全部標記 owner；非目標段已列 ≥ 3 項 |
| KPI 可量測 | 100% KPI 有量測管道（log/metric/survey 來源） |
| 共識 | PM + TL + PO 簽名（或 PR approve） |

**簽核 RACI**: PM=R, PO=A, TL=C, ARCH=I

### QG-G1: Ready to Code

**目標**: 架構與契約穩定，可開始實作。

| 維度 | 判準（量化） |
| :--- | :--- |
| 必備產出 | `04_adr.md`（至少涵蓋技術選型、NFR、資料）、`05_architecture.md`（C4 L1+L2）、`06_api.md`、`07_module.md` |
| 契約穩定度 | API endpoint 數量穩定 ≥ 2 個 sprint；無 `TBD` 標記在 request/response schema |
| ADR 覆蓋 | 每個被選擇的技術元件都有對應 ADR-NNNN（DB/快取/MQ/第三方）|
| NFR 可驗證 | 100% NFR 有對應測試策略（負載/壓力/安全） |

**簽核 RACI**: TL=R, ARCH=A, DEV=C, SEC=C

### QG-G2: Ready to Test

**目標**: 功能實作完成，可進整合/E2E 測試。

| 維度 | 判準（量化） |
| :--- | :--- |
| 單元測試 | 覆蓋率 ≥ 80%（核心模組 ≥ 90%），全部綠燈 |
| 程式碼審查 | 100% PR 經至少一位同儕 approve；TL 必審條件已標記 |
| 靜態檢查 | linter / type checker / SAST 零 error，warning 已 triage |
| 文件同步 | 所有新增 `MOD-/API-/ADR-` 已寫入對應檔案，frontmatter `traces:` 完整 |

**簽核 RACI**: DEV=R, TL=A, QA=C

### QG-G3: Ready to Deploy

**目標**: 系統可上線。對應 13 §F「整體評估」。

| 維度 | 判準（量化） |
| :--- | :--- |
| 整合測試 | 100% 關鍵 user journey E2E 通過 |
| 安全審查 | 13 §A-F 全部勾選；CVE: **critical = 0 且 high ≤ 2** |
| 效能 | 13 §G 負載測試完成，P95 達標、錯誤率 < 0.1% |
| 回滾準備 | `14 §6 回滾計畫`已撰寫並演練過至少 1 次 |
| 監控就緒 | SLI 已定義（≥ 4 個：延遲/流量/錯誤率/飽和度）、告警已配置 |

**簽核 RACI**: SEC=R, SRE=A, TL=C, PM=I

**通過規則**: 若 critical > 0 → ❌ 不可上線；若 high > 2 → 🟡 限制條件上線（需 ADR 記錄例外）；否則 ✅ 可上線。

### QG-G4: Ready to Operate

**目標**: 上線後進入穩定維運。

| 維度 | 判準（量化） |
| :--- | :--- |
| Runbook | `14 §7` 已撰寫，至少 3 個常見故障情境有 step-by-step 處理 |
| On-call | 值班排程已建立，alert routing 已測試 |
| 第一週監控 | SLO 達成率 ≥ 目標、MTTR 已基準化 |
| 文件同步 | README、CHANGELOG、ADR 索引已更新 |

**簽核 RACI**: SRE=R, OPS=A, TL=C

### 共同度量（across all gates）

- 需求穩定度：Sprint 內變更 < 10%
- 缺陷密度：每千行新增程式碼 bug ≤ 5
- Lead Time / Cycle Time：依專案基準化
- SLO 達成率：G4 之後持續追蹤
- MTTR：incident 發生後恢復時間

### MVP 模式對應

MVP（§4）只強制 QG-G0 + QG-G3 + QG-G4，G1/G2 合併為「Tech Spec 簽核 + 測試綠燈」單一閘。升級為完整流程時，G1/G2 需補填。

---

## 7. 附錄: 檢查清單

- **PRD**: 問題陳述、非目標、量化 KPI?
- **架構**: 權衡與 ADR? NFR 可測?
- **設計**: 資料模型/索引、API 契約、錯誤處理、可觀測性?
- **安全**: Secrets 管理、認證授權、輸入驗證、依賴風險?
- **上線**: 備份、監控、告警、回滾方案與演練?

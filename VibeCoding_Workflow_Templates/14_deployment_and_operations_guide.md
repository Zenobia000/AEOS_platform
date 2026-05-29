# 部署與運維指南 - [專案名稱]

> **版本:** v1.0 | **更新:** YYYY-MM-DD | **狀態:** 草稿/已批准
> **負責人:** SRE | **審核:** TL + OPS | **適用範圍:** 上線 + 運維階段（CI/CD 細節在 §2；對應 QG-G3/G4 詳見 01 §6）

---

## 1. 部署架構

```text
Development → Staging → Production
```

### 基礎設施元件

| 元件 | 用途 | 技術選型 |
| :--- | :--- | :--- |
| 負載均衡 | 流量分配與故障轉移 | [Nginx/ALB/...] |
| 應用伺服器 | 核心應用託管 | [K8s/ECS/Cloud Run/...] |
| 資料庫叢集 | 資料持久化與複製 | [PostgreSQL/MySQL/...] |
| 快取層 | 效能優化 | [Redis/Memcached] |
| CDN | 靜態資源交付 | [CloudFront/Cloudflare] |
| 監控 | 健康檢查與告警 | [Prometheus+Grafana/Datadog] |

---

## 2. CI/CD 流水線

| 階段 | 步驟 |
| :--- | :--- |
| **建置** | 拉取程式碼 → 安裝依賴 → 編譯 → 單元測試 → 產出 artifact |
| **測試** | 部署至 staging → 整合測試 → E2E 測試 → 效能測試 → 安全掃描 |
| **部署** | 準備新環境 → 部署應用 → 煙霧測試 → 切換流量 → 清理舊環境 |

---

## 3. 部署檢查清單

> 📎 **與 13 §G、QG-G3 的分工**:
> · `13 §G` = **pre-deploy 整體就緒檢查**（安全 / SLI 定義 / Runbook / 備份），對應 `01 §6 QG-G3` 量化判準
> · 本節（14 §3） = **deploy 動作 checklist**（執行部署當下的步驟）
> · §5 監控與告警 = **post-deploy 持續監控配置**

### 部署前

- [ ] QG-G3 已通過（critical=0 且 high≤2，詳見 `13 §F` + `01 §6`）
- [ ] Code review 通過（PR checklist 見 `11`）
- [ ] 所有測試通過 (單元/整合/E2E)
- [ ] 安全掃描完成
- [ ] 效能基準達標（P95 < SLO 定義值）
- [ ] DB migration 準備好 (如需要，含 dry-run 與 rollback script)
- [ ] 回滾計畫已記錄並演練 ≥ 1 次（詳見 §6）
- [ ] 監控告警已配置（詳見 §5）
- [ ] 團隊已通知（含對外公告，若 breaking change）

### 部署中

- [ ] 監控部署進度
- [ ] 驗證健康檢查
- [ ] 檢查應用日誌
- [ ] 驗證關鍵功能
- [ ] 監控系統指標

### 部署後

- [ ] 煙霧測試通過
- [ ] 效能指標正常
- [ ] 錯誤率正常
- [ ] 文檔已更新

---

## 4. 部署策略

| 策略 | 適用場景 | 回滾時間 |
| :--- | :--- | :--- |
| **Blue-Green** | 大版本更新、架構變更 | < 30s |
| **Rolling** | 日常更新、小幅變更 | 1-5 min |
| **Canary** | 風險控制、A/B 測試 | < 30s |

---

## 5. 監控與告警

### 關鍵指標

| 類別 | 指標 | 閾值 |
| :--- | :--- | :--- |
| 應用 | 回應時間 P95 | < 500ms |
| 應用 | 錯誤率 | < 0.1% |
| 基礎設施 | CPU 使用率 | < 80% |
| 基礎設施 | 記憶體使用率 | < 85% |
| 基礎設施 | 磁碟使用率 | < 90% |

### 告警規則

| 名稱 | 條件 | 嚴重程度 | 通知方式 |
| :--- | :--- | :--- | :--- |
| 高錯誤率 | error_rate > 1% | Critical | Page on-call |
| 高延遲 | P95 > 1000ms | Warning | Slack |
| 資源耗盡 | CPU/Mem > 90% | Warning | Slack |

---

## 6. 回滾流程

> 📎 **與 20 CIA §6 的關係**: 大型變更的回滾策略應在實作前於 `20_change_impact_analysis.md §6` 預先定義（含 point-of-no-return）。本節是上線後實際執行回滾的 SOP。

### 6.1 自動回滾觸發

| 條件 | 閾值 | 處置 |
| :--- | :--- | :--- |
| 錯誤率 | > 1% 持續 5 分鐘 | 自動回滾 + page on-call |
| P95 延遲 | > SLO × 2 持續 5 分鐘 | 自動回滾 + page on-call |
| 健康檢查 | 連續 3 次失敗 | 自動回滾 + page on-call |
| 5xx 比率 | > 5% 即時 | 自動回滾 + page on-call |

自動回滾觸發後立即通知：on-call、TL、SRE Slack 頻道、status page 自動更新「Investigating」。

### 6.2 手動回滾決策準則

| 場景 | 決策者 | 動作 |
| :--- | :--- | :--- |
| 監控顯示異常但未達自動回滾閾值 | on-call + SRE | 評估是否手動回滾 |
| 客戶通報嚴重問題 | on-call + PM | 評估影響範圍後決策 |
| 資料正確性問題 | TL + DBA | 通常需手動，避免新資料覆蓋舊資料 |
| 安全漏洞 | SEC + TL | 立即回滾 |

### 6.3 手動回滾步驟

**Code 層**:

1. [ ] 確認最後一個穩定版本（git tag / image digest）
2. [ ] 通知 Slack #incidents：「ROLLBACK STARTED: vX.Y.Z → vX.Y.Z-1」
3. [ ] 執行回滾 (e.g., `kubectl rollout undo deployment/app`)
4. [ ] 驗證 pod 全部換回舊版本
5. [ ] 煙霧測試關鍵 endpoint
6. [ ] 監控錯誤率、延遲恢復正常 ≥ 10 分鐘

**Data 層**（若涉及 DB migration）:

1. [ ] 評估資料相容性：
    - 新版寫入的資料舊版能否讀？（forward-compatible schema）
    - 新版新增的 column / table 是否會讓舊版報錯？
2. [ ] 執行反向 migration（若 §6.4 已準備好 reverse script）
3. [ ] 驗證資料完整性（row count、checksum）
4. [ ] 若無法反向 → 進入「資料修補模式」（見 §6.5）

### 6.4 反向 Migration 準備

部署前必須準備：

- [ ] `migration_NNN_up.sql` — 正向腳本
- [ ] `migration_NNN_down.sql` — 反向腳本（或明確標記「不可逆」）
- [ ] Dry-run on staging：上 → 下 → 上，驗證資料一致
- [ ] **不可逆變更**（drop column、drop table、data transformation）必須在 CIA §6 預先標記 point-of-no-return

### 6.5 資料修補模式（不可逆變更後出問題）

當 forward migration 已執行且不可逆，但發現新版有 bug：

1. **不要回滾 code 到舊版**（會讀不到新 schema）
2. 評估能否在新版 schema 上 hotfix
3. 若必須回 schema → 撰寫 forward-compensating migration（如把新欄位資料 backfill 回相容狀態）
4. 升級 incident 至 P0，TL + DBA + SEC 共同決策

### 6.6 對應文件更新

回滾完成後（無論自動/手動）：

- [ ] 對應 ADR-NNNN 標記 `superseded by <new-ADR>` 或 `reverted`
- [ ] 對應 CR-NNNN 狀態改為「已駁回」或「重新評估」
- [ ] 對應 CIA-NNNN 補 §10「實際 vs 預期」與經驗教訓
- [ ] 16 WBS 對應任務狀態調整
- [ ] 規劃 post-mortem 會議（72 小時內）

### 6.7 對外通訊模板

```text
[Status Page]
Title: [Service] degraded performance / outage
Status: Investigating → Identified → Monitoring → Resolved
Updates:
- HH:MM 發現問題，已啟動回滾
- HH:MM 回滾完成，服務恢復
- HH:MM 確認穩定，將於 X 日內公布 post-mortem

[客戶 Email]（影響付費客戶時）
主旨: [Service] 暫時性服務影響說明
內容:
- 發生時間 / 影響範圍 / 已處置
- 預計補償（若 SLA 內）
- post-mortem 預計發布日期
```

### 6.8 回滾後驗證 Checklist

- [ ] 錯誤率回到基線 ≤ 0.1%
- [ ] P95 延遲回到 SLO 內
- [ ] 關鍵 user journey E2E 通過
- [ ] 客戶投訴新增為 0
- [ ] 資料 sample check（10 筆關鍵紀錄與回滾前一致）
- [ ] On-call 確認可以解除 incident 狀態

---

## 7. Runbook 模板

```markdown
# 服務 Runbook: [服務名稱]

## 服務概覽
- 用途與功能
- 依賴服務
- 架構圖

## 部署流程
- 建置與部署步驟
- 配置需求
- 健康檢查端點

## 監控
- 關鍵指標與儀表板
- 告警條件與回應方式
- 日誌位置與格式

## 故障排除
- 常見問題與解決方案
- 緊急聯絡人
- 升級流程
```

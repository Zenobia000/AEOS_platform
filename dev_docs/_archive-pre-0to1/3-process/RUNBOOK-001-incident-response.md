---
id: RUNBOOK-001
title: Incident Response Runbook + Oncall
status: active
type: runbook
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 3
related: [PILOT-001, OBS-001, NFR-001, ADR-0005]
---

# RUNBOOK-001 — 事故回應與 Oncall

> 事故會發生，問題是「會不會被快速止血」。本 runbook 定義分級、響應時限、行動步驟。**所有 Pilot 期 oncall 必讀**。

## 1. Severity 分級

| Level | 定義 | 例子 | 響應 SLA | 通報範圍 |
|---|---|---|---|---|
| **P0 — Critical** | 服務全停 / 資料外洩 / PII 洩漏 / 永久資料遺失 | 全部客戶無法收訊息；DB corruption；S3 bucket 公開 | **5 分鐘**內 ack；**1 小時**內止血嘗試 | CTO + CEO + 受影響客戶 |
| **P1 — High** | 單一客戶嚴重故障 / 核心功能不可用 / 可用性 < 95% | 某客戶 webhook 全失敗；LLM provider 全掛無 fallback | **15 分鐘**內 ack；**4 小時**內止血 | CTO + 受影響客戶 |
| **P2 — Medium** | 部分功能降級 / 可繞過 / 影響 < 10% 使用者 | KB ingest 慢；某 skill 偶發失敗；test runner 卡住 | **2 小時**內 ack；**1 工作日**內修復 | CTO（內部） |
| **P3 — Low** | 體驗瑕疵 / 無功能影響 / cosmetic | 錯字；非關鍵 metric 缺失；非阻塞 warning | **下個工作日**處理 | 內部追蹤 |

## 2. Oncall 輪值

### Phase 1（Pilot 期，2 ~ 3 人）

```
Week 1-2: CTO (primary)        | LLM eng (secondary)
Week 3-4: LLM eng (primary)    | CTO (secondary)
Week 5+:  輪替 + 加入 DevOps（hire 後）
```

- **Primary**：第一通報接收人。攜帶 oncall 手機 24/7。
- **Secondary**：Primary 30 分鐘內無回應時自動 escalate。
- **Backup（CEO）**：兩人都失聯時兜底；只負責客戶溝通，不碰 system。

### Handover 規則

- 每週一 10:00 交接；新 primary 必須複習過去 7 天 incident
- 交接 checklist：未結 ticket、進行中 fix、預期維護視窗

## 3. P0 / P1 事故響應流程

```
┌─────────────────────────────────────────────────────────┐
│ 0. 告警觸發（OBS-001 alert 或客戶 report）              │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Acknowledge（Slack #incidents 回覆 "ack"）           │
│    └─ SLA 計時開始                                       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Triage（5 分鐘內）                                    │
│    ├─ 確認 severity                                      │
│    ├─ 開 incident channel #inc-YYYYMMDD-<short>          │
│    └─ 通知 CTO（P0 額外通知 CEO）                        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Stop the bleeding（止血優先於 RCA）                  │
│    ├─ 可回滾？ → RUNBOOK-002 §rollback                   │
│    ├─ 可降級？ → 切 fallback（如 LLM provider B）       │
│    ├─ 可隔離？ → 暫停受影響 tenant                       │
│    └─ 都不行？ → maintenance mode + 客戶通報             │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Communicate                                          │
│    ├─ P0：每 30 分鐘 status update（內+外）             │
│    ├─ P1：每 1 小時 status update                       │
│    └─ Status page（如有）同步更新                        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Resolve + 確認                                        │
│    ├─ 驗證指標回到綠線（OBS-001 dashboard）              │
│    ├─ 連續觀察 30 分鐘                                   │
│    └─ Close incident                                    │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Post-incident（24 小時內）                            │
│    ├─ RCA 寫入 docs/4-exploration/RCA-YYYYMMDD.md       │
│    ├─ 受影響客戶正式通報（email + 補償方案）             │
│    └─ Action items 進 GitHub Issues                     │
└─────────────────────────────────────────────────────────┘
```

## 4. 常見場景 Playbook

### 4.1 LLM Provider 故障（P1）

```bash
# 1. 確認故障範圍
curl -X POST $PROVIDER_A_HEALTH_ENDPOINT
# 2. 切換到 fallback provider（ADR-0001）
kubectl set env deployment/agent-worker LLM_PROVIDER=provider_b
# 3. 驗證新 provider 接管
tail -f logs | grep "provider=provider_b"
# 4. 通報客戶（如延遲增加）
```

### 4.2 LINE Webhook 大量失敗（P1）

```bash
# 1. 看 nginx 5xx 比例
# 2. 檢查 webhook 簽章驗證（API-002）
# 3. 若 LINE 側故障 → 通知客戶 + 等待 + 重放 queue
# 4. 若我方故障 → 看 worker log → rollback 或 hotfix
```

### 4.3 DB 連線飽和（P0/P1）

```bash
# 1. 看連線數
psql -c "SELECT count(*) FROM pg_stat_activity;"
# 2. 殺長時間 idle
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND state_change < now() - interval '10 min';"
# 3. 考慮加 pgbouncer / scale up
# 4. 找根因（n+1 query? leaking connection?）
```

### 4.4 PII 疑似洩漏（P0 — 法律最高優先級）

```
1. 立即凍結受影響資料源（DB user 改 read-only）
2. 通知 CEO + 法務（如有）
3. 範圍評估：誰看到、看到什麼、如何洩漏
4. 24 小時內依《個資法》§12 通知當事人
5. 客戶通報 + 監管通報（依適用法律）
6. RCA + 補救（rotate keys、patch、追蹤外流）
```

詳見 ADR-0005 §PII 處理。

### 4.5 LLM Cost Spike（P1）

```bash
# 1. 看 OBS-001 cost dashboard
# 2. 確認是否單一 tenant 暴衝
# 3. 啟動 QUOTA-001 緊急降級（降模型 / 限頻率）
# 4. 通報該 tenant
```

### 4.6 部署後立即故障（P0/P1）

→ **永遠先 rollback，再 debug**。詳見 RUNBOOK-002 §rollback。

## 5. 通報範本

### 5.1 內部 Slack 開單

```
🚨 [P0] AI-CS service unavailable for tenant ABC
ack: @cto
incident channel: #inc-20260615-abc-down
started: 14:32 UTC
impact: tenant ABC 全部對話無回應，~120 使用者受影響
status: investigating
```

### 5.2 客戶通報範本（P0/P1）

```
主旨：[AEOS] Service Incident Notification - <YYYY-MM-DD>

Dear [Client Name],

我們在 [time] 偵測到影響貴司服務的事故：
- 影響範圍：[具體描述]
- 開始時間：[time]
- 目前狀態：[investigating / mitigating / resolved]
- 預計恢復：[ETA 或 "持續更新"]

我們會每 [30/60] 分鐘更新進展。
如有緊急問題請回此 email 或 LINE @aeos_support。

致歉，
AEOS Team
```

## 6. 工具與聯絡

| 用途 | 工具 / 聯絡 |
|---|---|
| 告警接收 | PagerDuty / Better Uptime / Slack #alerts |
| Incident channel | Slack #inc-* |
| 客戶溝通 | Email + LINE @aeos_support |
| Status page | (Phase 1: README badge；Phase 2: statuspage.io) |
| Oncall 手機 | (待 hire 確認) |

## 7. RCA 模板

事故 24 小時內必須寫入 `docs/4-exploration/RCA-YYYYMMDD-<short>.md`：

```markdown
# RCA — <事故簡述>

- **日期**: YYYY-MM-DD
- **嚴重度**: P0 / P1 / P2
- **持續時間**: HH:MM:SS
- **影響範圍**: <tenant 數 / 使用者數 / 對話數>

## Timeline
- HH:MM — 告警觸發
- HH:MM — Ack
- HH:MM — 找到根因
- HH:MM — 止血
- HH:MM — 完全恢復

## Root Cause
（用 5 Why 推到根因）

## What Worked
（哪些設計/工具救了我們）

## What Didn't Work
（哪些 gap 導致 detect 慢 / fix 慢）

## Action Items
- [ ] [owner] [due] item

## Customer Communication
（已發給客戶的內容）
```

## 8. 演練（Game Day）

每月一次 30 分鐘 incident drill：
- 隨機挑一個 §4 場景
- Primary 必須走完 §3 流程
- Postmortem 改進 runbook

---

**See also**:
- `OBS-001-observability-spec.md` — 告警來源與 dashboard
- `RUNBOOK-002-deploy-rollback.md` — 部署與回滾
- `RUNBOOK-003-backup-dr.md` — 資料災害恢復
- `PILOT-001-success-criteria.md` §3 Kill Criteria — 事故升級觸發條件

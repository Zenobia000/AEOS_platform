---
id: RUNBOOK-002
title: Deployment & Rollback Runbook
status: active
type: runbook
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 3
related: [ADR-0004, RUNBOOK-001, OBS-001, NFR-001]
---

# RUNBOOK-002 — 部署與回滾

> 第一條原則：**任何部署都必須能在 5 分鐘內回滾**。沒回滾路徑的部署 = 賭博。

## 1. 部署策略總覽

依 ADR-0004 deployment model：

- **環境**：3 套 — `dev`（本地 docker-compose）→ `staging`（單機 Hetzner）→ `prod`（單機 Hetzner + DB replica）
- **部署方式**：Blue-Green at process level（同機跑 2 份 container，nginx 切流）
- **發版頻率**：Pilot 期目標每週 1~3 次
- **凍結窗口**：週五 16:00 ~ 週一 09:00（除 hotfix）

## 2. 部署前 Checklist

PR merge 到 main 前必須全部 ✅：

- [ ] 所有 CI 綠燈（unit + integration + e2e）
- [ ] Test coverage ≥ 80%（對應 NFR-001 §6）
- [ ] DB migration 已加入 `migrations/` 並 reviewed（含 reverse migration）
- [ ] 新 metric / alert 已加入 OBS-001 §3 §7
- [ ] CHANGELOG.md 已更新
- [ ] Breaking change → 已在 commit message 標 `BREAKING:`
- [ ] 受影響 contract 文件（API/BF/UF/SF）已同步 + 更新 `last-synced-with`
- [ ] 變更涉及 flow/contract/data/architecture → CIA 已完成（見 change-governance）
- [ ] Reviewer 已 approve

## 3. 部署流程

### 3.1 Staging 部署（每次必經）

```bash
# 1. Tag 候選版本
git tag -a v0.X.Y-rc.N -m "release candidate"
git push origin v0.X.Y-rc.N

# 2. CI 觸發 image build + push to registry
# (GitHub Actions: .github/workflows/build.yml)

# 3. SSH 到 staging
ssh deploy@staging.aeos.internal

# 4. 拉新 image + 啟 green
cd /srv/aeos
./deploy.sh staging v0.X.Y-rc.N

# 5. 跑 smoke test
./scripts/smoke-test.sh https://staging.aeos.internal

# 6. 觀察 5 分鐘 OBS-001 D2 dashboard
```

### 3.2 Prod 部署（Blue-Green 切換）

```bash
# Prerequisite: staging 已穩定運行 ≥ 24 小時

# 1. 通知 #incidents channel
# "Deploying v0.X.Y to prod at HH:MM, ETA 10min"

# 2. SSH to prod
ssh deploy@prod.aeos.internal

# 3. Pull image + start green container
cd /srv/aeos
./deploy.sh prod-prepare v0.X.Y
# 此步驟：啟動 green，但 nginx 仍指 blue

# 4. Green health check
curl -f http://localhost:8081/health
# 預期 200 OK + version=v0.X.Y

# 5. Run prod smoke test against green
./scripts/smoke-test.sh http://localhost:8081

# 6. 切流量到 green
./deploy.sh prod-switch
# 此步驟：nginx reload，blue → green

# 7. 監控 10 分鐘
# OBS-001 D2 + tail logs
# 任何 §4 觸發條件 → 立即 rollback

# 8. 若穩定 → 停 blue
./deploy.sh prod-cleanup

# 9. 標 release
gh release create v0.X.Y --notes-from-tag
```

### 3.3 DB Migration 特殊規則

- **永遠先加新欄位，再 deploy code，再 drop 舊欄位**（三階段 deploy）
- 禁止 `DROP TABLE` / `DROP COLUMN` 與 code change 同一個 deploy
- 大表（> 100 萬筆）變更必須用 `pg_repack` 或 online schema change，禁止鎖表
- 任何 migration 必須有 reverse migration（即使是空的，也要明示「不可逆」）

範例三階段：

```
Deploy 1: Migration adds `users.email_v2` column. Code reads old, writes both.
Deploy 2: Backfill script copies old → v2. Code reads v2, writes both.
Deploy 3: Migration drops `users.email`. Code reads v2 only.
```

## 4. 回滾觸發條件

**部署後 30 分鐘內**出現以下任一 → 立即 rollback：

| 條件 | 來源 |
|---|---|
| Error rate > 5%（基線通常 < 1%） | OBS-001 D2 |
| Latency p95 > 2x 基線 | OBS-001 D2 |
| 任何 P0 告警 | RUNBOOK-001 |
| 新增的 metric 缺失或亂跳 | OBS-001 |
| 客戶 report 新故障 | Slack / email |
| Smoke test 失敗 | CI / manual |

**部署後 30 分鐘 ~ 24 小時**內出現問題 → 評估是否 rollback 還是 hotfix forward；
參考原則：**疑慮即 rollback**。

## 5. Rollback 程序

### 5.1 快速 Rollback（5 分鐘內，無 DB migration）

```bash
ssh deploy@prod.aeos.internal
cd /srv/aeos
./deploy.sh prod-rollback
# 此腳本：切 nginx 回 blue（舊版本仍在跑），停 green
```

### 5.2 含 DB Migration 的 Rollback

**情境 A：三階段中第 1 階段失敗** → 直接跑 reverse migration + rollback code

```bash
./scripts/migrate.sh down 1
./deploy.sh prod-rollback
```

**情境 B：三階段中第 2/3 階段失敗** → 通常 code rollback 即可（schema 仍兼容）

**情境 C：unsafe migration（違反 §3.3）導致** → 走 RUNBOOK-003 §point-in-time recovery
- 此情境視為 P0 事故
- 必須 incident channel + RCA

### 5.3 Rollback 後動作

1. Slack #incidents 公告 rollback 完成
2. 開 GitHub Issue 記錄失敗原因
3. 在 staging 重現問題
4. 修復 + 加測試 + 重新部署
5. 如達 P1/P0 → 寫 RCA（RUNBOOK-001 §7）

## 6. Hotfix 流程（繞過凍結窗口的緊急修復）

**前提**：正在發生的 P0/P1 事故 + 無法用 rollback 解決。

```bash
# 1. 從生產版本拉 hotfix branch
git checkout v0.X.Y
git checkout -b hotfix/<short-desc>

# 2. 最小變更修復（一個 commit）
# 3. PR + 至少 1 個 reviewer（緊急情況可後補）
# 4. CI 綠燈
# 5. 走 §3.2 部署
# 6. Tag v0.X.Y+1
# 7. Cherry-pick 回 main
```

## 7. Maintenance Mode

需停機維護時（Phase 1 應極少發生）：

```bash
# 1. 提前 24 小時通知客戶
# 2. Status page 標 "scheduled maintenance"
# 3. 啟用 nginx maintenance page
./deploy.sh maintenance-on
# 4. 執行維護
# 5. 完成驗證
./deploy.sh maintenance-off
# 6. Status page 標 resolved
```

對應 NFR-001 §2 — 計畫性維護不計入 SLA downtime，但須提前通知。

## 8. 部署視窗

| 場景 | 視窗 |
|---|---|
| 一般 release | 週二/三 10:00 ~ 16:00 |
| Hotfix | 任何時間（含週末） |
| DB migration | 週二/三 10:00 ~ 14:00（後續 2 小時觀察） |
| Breaking change | 客戶通知後 + 凍結窗口外 |
| 禁止部署 | 週五 16:00 ~ 週一 09:00；國定假日；客戶重要活動期 |

## 9. 工具與檔案位置

| 用途 | 位置 |
|---|---|
| 部署腳本 | `/srv/aeos/deploy.sh`（infra repo） |
| Smoke test | `scripts/smoke-test.sh` |
| Migration 工具 | `scripts/migrate.sh` |
| Nginx config | `/etc/nginx/sites-enabled/aeos` |
| Docker compose | `/srv/aeos/docker-compose.prod.yml` |
| Image registry | `ghcr.io/zenobia000/aeos-*` |

## 10. 演練

每月一次 staging rollback drill：
- 故意在 staging 部署有 bug 的版本
- 跑完整 §5 rollback 流程
- 計時：目標 5 分鐘內完成

---

**See also**:
- `ADR-0004-deployment-model.md` — 部署模式決策
- `RUNBOOK-001-incident-response.md` — 部署後事故處理
- `RUNBOOK-003-backup-dr.md` — DB migration 失敗時的災害恢復
- `OBS-001-observability-spec.md` §6 D2 — 部署監控 dashboard

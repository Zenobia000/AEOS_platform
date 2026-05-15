---
id: RUNBOOK-003
title: Backup & Disaster Recovery Runbook
status: active
type: runbook
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 3
related: [ADR-0004, ADR-0005, RUNBOOK-001, RUNBOOK-002, LEGAL-001, NFR-001]
---

# RUNBOOK-003 — 備份與災害恢復

> 「**沒驗證過的備份等於沒備份。**」Pilot 期客戶資料一次永久丟失 = Pilot 結束 + 商譽歸零。本 runbook 是最低限度生存指南。

## 1. 恢復目標

| 指標 | 目標 | 對應 |
|---|---|---|
| **RTO**（Recovery Time Objective） | **≤ 4 hours** for P0 / ≤ 1 hour for typical | LEGAL-001 §4.5 |
| **RPO**（Recovery Point Objective） | **≤ 24 hours** of data loss | LEGAL-001 §4.5 |
| **MTBF 目標**（Mean Time Between Failures） | ≥ 30 days | Pilot 期 |
| **MTTR 目標**（Mean Time To Recovery） | ≤ 2 hours | Pilot 期 |

Phase 2/3 收緊：RPO → 1h，RTO → 30min。

## 2. 資產分類與備份策略

| 資產 | 備份頻率 | 保留期 | 儲存位置 | 加密 |
|---|---|---|---|---|
| **Postgres（主 DB）** | 每日 full + WAL 連續 | 30 天 | Hetzner Storage Box + S3 cross-region | AES-256 |
| **Object Storage（KB 檔案、附件）** | 即時同步（rclone） | 30 天版本控制 | S3 + B2 cross-provider | AES-256 |
| **Audit Log** | 每日 export | 13 個月（法遵） | S3 cold tier | AES-256 |
| **Configuration / Secrets** | 每次變更 | 90 天 | Encrypted git repo + KMS | KMS |
| **Application Image** | 每次 build | 90 天 | Container registry + S3 mirror | TLS |
| **Vector DB / Embeddings** | 每週 snapshot | 4 週 | Hetzner Storage Box | AES-256 |
| **Code Repo** | GitHub 自動 + 自有 mirror 每日 | 永久 | GitHub + self-host gitea mirror | TLS |

**3-2-1 原則**：每個 critical 資產 ≥ **3 份**、**2 種**媒介、**1 份**異地。

## 3. Postgres 備份細節

### 3.1 Full Backup

```bash
# Daily 03:00 UTC (cron)
pg_basebackup -h prod-db -D /backup/postgres/$(date +%F) \
  -Ft -z -P -X stream \
  -U backup_user

# 加密 + upload
age -e -r $BACKUP_PUBKEY /backup/postgres/$(date +%F).tar.gz | \
  aws s3 cp - s3://aeos-backups/postgres/$(date +%F).tar.gz.age

# 驗證
./scripts/verify-backup.sh $(date +%F)
```

### 3.2 Continuous WAL Archiving

```ini
# postgresql.conf
archive_mode = on
archive_command = '/usr/local/bin/wal-archive.sh %p %f'
wal_level = replica
max_wal_senders = 4
```

`wal-archive.sh` 把每個 WAL segment 加密上傳至 S3 - 達成 PITR（Point-in-Time Recovery）。

### 3.3 Read Replica

Pilot 期至少 1 個 read replica（即使是低規格），用途：
- 故障時可快速 promote
- 跑分析查詢，不影響 prod
- 備份來源（從 replica pg_basebackup，不打擾 primary）

## 4. 備份驗證（最重要！）

未驗證的備份 = 沒備份。**每週自動執行**：

```bash
# .github/workflows/backup-verify.yml weekly
# 或 cron on backup verifier host

# 1. 隨機選一份近 7 天備份
BACKUP_DATE=$(date -d "$((RANDOM % 7)) days ago" +%F)

# 2. 下載 + 解密
aws s3 cp s3://aeos-backups/postgres/${BACKUP_DATE}.tar.gz.age - | \
  age -d -i $BACKUP_PRIVKEY > /tmp/backup.tar.gz

# 3. Restore 到隔離環境
./scripts/restore-to-sandbox.sh /tmp/backup.tar.gz

# 4. Run consistency check
psql -h sandbox-db -c "SELECT count(*) FROM tenants;" # > 0
psql -h sandbox-db -c "SELECT count(*) FROM conversations;" # > 0
psql -h sandbox-db -c "ANALYZE;" # full table scan

# 5. Run sample query that exercises FK
./scripts/sanity-queries.sh

# 6. 結果 → Slack #engineering + 進 OBS-001 metric
echo "backup_verify_status{date=\"$BACKUP_DATE\"} 1" | curl -X POST $PUSHGATEWAY
```

驗證失敗 → P0 alert（對應 OBS-001 §7 `backup_failed`）。

## 5. Disaster Recovery 場景

### 5.1 場景 A：單 row / 單表誤刪（最常見）

**RTO**：30 分鐘
**程序**：

```bash
# 1. 確認誤刪時間
# 2. 在隔離環境 PITR 到誤刪前 1 分鐘
./scripts/pitr.sh --target-time "2026-05-15 14:32:00 UTC" --dest sandbox

# 3. Export 該表 / row
pg_dump -h sandbox-db -t users --data-only --where="id IN (...)" > /tmp/restore.sql

# 4. 在 prod review + apply
psql -h prod-db -f /tmp/restore.sql

# 5. 驗證
# 6. 寫 RCA（屬於 P1 事故）
```

### 5.2 場景 B：DB corruption / migration 失敗

**RTO**：2 小時
**程序**：

```bash
# 1. 啟動 RUNBOOK-001 P0 流程
# 2. 切 nginx 到 maintenance mode（RUNBOOK-002 §7）
# 3. 評估：可修還是要全 restore？
#    可修：fix forward
#    不可修：→ §5.4 全 restore

# 4. 如能 promote replica：
./scripts/promote-replica.sh
# 切 app DB endpoint
# 5. Postmortem
```

### 5.3 場景 C：完整資料中心失聯（最壞情況）

**RTO**：4 小時
**前提**：cross-region S3 備份 + DNS 可切

**程序**：

```bash
# 1. CEO 通告所有 Pilot 客戶（RUNBOOK-001 §5.2）
# 2. 啟動備援 region
terraform apply -var-file=dr-region.tfvars

# 3. 從 S3 cross-region restore 最近備份
./scripts/restore-from-s3.sh --region $DR_REGION --date latest

# 4. 應用 WAL replay 到 RPO 邊界

# 5. 啟動 app 在新 region
./deploy.sh dr-region v$(latest)

# 6. DNS 切流（Cloudflare）
./scripts/dns-failover.sh

# 7. Smoke test + 客戶逐一通報
```

### 5.4 場景 D：物件儲存（KB 檔案）誤刪

**RTO**：1 小時
**程序**：

S3 啟用 versioning + lifecycle 後，誤刪實際是 mark deleted：

```bash
# Restore 最近版本
aws s3api list-object-versions --bucket aeos-kb --prefix tenant_id/
aws s3api restore-object --bucket aeos-kb --key <key> --version-id <ver>
```

### 5.5 場景 E：客戶要求刪除其全部資料（DPA §6 / §7）

不是事故，但是 DR 流程的一部分：

```bash
# 1. 驗證請求合法性（CEO 簽核）
# 2. 凍結該 tenant 寫入（quota-guard suspend）
# 3. Soft delete：標記 deleted_at；30 天保留期
# 4. 30 天後 hard delete：
./scripts/tenant-purge.sh <tenant_id>
# 此腳本：刪 prod DB、刪 object storage、刪 vector DB、刪 cache、刪近 30 天備份中的 tenant row
# 5. 提供刪除證明（時間戳 + hash）給客戶
```

注意：**audit log 保留 13 個月**（法遵），但只保留 hash + metadata；原 PII 已 mask。對應 ADR-0005。

## 6. 演練（DR Drill）

| 演練 | 頻率 | 目標 |
|---|---|---|
| **Backup verify** | 每週（自動） | 備份可解壓 + 連通性 |
| **PITR drill** | 每月 | 隨機時間點還原到 sandbox |
| **Replica promote drill** | 每季 | 計時：< 30 min |
| **Full DR drill**（場景 C） | 每半年 | 計時：< 4 hours |
| **Tenant purge drill** | 每季 | 證明 §5.5 流程可走完 |

每次演練 → 進 `docs/4-exploration/DR-DRILL-YYYY-MM.md` 記錄。

## 7. Backup 監控（對應 OBS-001 §7）

| 指標 | 閾值 | 告警 |
|---|---|---|
| 最近一次 daily backup 時間 | > 26 小時 | P0 |
| 最近一次 backup verify | > 8 天 | P1 |
| WAL archive lag | > 5 分鐘 | P1 |
| S3 bucket size 異常下降 | > 20% drop | P1 |
| Backup 加密驗證失敗 | 任何 | P0 |

## 8. Restore Authorization

防止內部誤操作或惡意：

- Restore 到 prod → 需 **CEO + CTO 雙人 approval**（緊急情況可後補）
- Tenant purge → 需 **CEO + 客戶書面請求** 雙簽
- 任何 restore 動作 → 進 audit log，13 個月保留

## 9. 第三方備份服務評估

Phase 1 自建以省成本；Phase 2 評估：

| 候選 | 用途 | 月成本估 |
|---|---|---|
| AWS Backup（cross-region） | 自動化 + 合規報告 | $50~100 |
| Continuent Tungsten | Postgres HA + DR | $500+ |
| 自建（current）| WAL + pg_basebackup + S3 | $30~50 |

Pilot 期：自建。GA 期：評估升級。

## 10. 文件對應 LEGAL-001 §4.5

DPA 中宣告：
- ✅ Daily encrypted backups, retained 30 days → §3
- ✅ Backup restoration tested quarterly → §6（我們做更嚴格：每月）
- ✅ RTO ≤ 4 hours, RPO ≤ 24 hours → §1

**任何此處目標調低 = 必須同步 update LEGAL-001 + 客戶通告**。

## 11. 緊急聯絡

| 角色 | 聯絡 |
|---|---|
| Backup primary | CTO |
| Restore authorization | CEO + CTO |
| Customer comm（DR 期間） | CEO |
| Vendor escalation（Hetzner / AWS） | (待 hire 確認) |

## 12. 實作優先序

| Week | 交付 |
|---|---|
| W1 | Postgres daily backup + WAL archive 上線；§3 完整 |
| W2 | §4 backup verify 自動化 |
| W3 | Object storage versioning + sync；read replica 上線 |
| W4 | §7 monitoring + alerts |
| W6 | §6 第一次 PITR drill |
| W8 | §6 第一次 replica promote drill |
| W12 | §6 第一次 full DR drill |

---

**See also**:
- `ADR-0004-deployment-model.md` — 基礎架構決策
- `ADR-0005-data-retention-pii.md` — 保留期與刪除政策
- `LEGAL-001-DPA-template.md` §4.5 §6 — 對客戶承諾
- `RUNBOOK-001-incident-response.md` §4.4 — PII 洩漏與 DR 交互
- `RUNBOOK-002-deploy-rollback.md` §3.3 §5.2 — DB migration 失敗對接
- `OBS-001-observability-spec.md` §7 — backup 監控
- `NFR-001-non-functional-requirements.md` §2 — 可用性目標

---
id: SEC-001
title: Threat Model (STRIDE + LLM Top 10)
status: active
type: threat-model
created: 2026-05-15
last-synced-with: a5d7a75bd822b8cf7d2b6d8c3157060f50848e86
owner: CTO
tier: 2
related: [SAD-v0.1, NFR-001, ADR-0005, ADR-0006, ADR-0007, QUOTA-001, OBS-001, LEGAL-001]
---

# SEC-001 — 威脅模型 (STRIDE + LLM Top 10)

> 「**安全不是 feature，是 baseline。**」本文同時覆蓋傳統 OWASP STRIDE 與 LLM 特有威脅（OWASP LLM Top 10），定義每項威脅的緩解控制。

## 1. Scope

涵蓋 SAD-v0.1 中的所有 component：
- API Gateway / Webhook Handler
- Agent Worker / RAG Engine
- KB Ingest Worker
- Admin Console
- Quota Guard / Prompt Registry
- Postgres / Object Storage / Vector DB
- LLM Provider integration
- LINE channel integration

時間範圍：Phase 1 (Pilot)。Phase 2/3 重做。

## 2. Trust Boundaries

```
                  ┌─────────────────────────────┐
   公開網際網路    │                              │   私有 VPC
                  │                              │
  ┌──────┐        │   ┌──────────┐  ┌─────────┐ │
  │ LINE │───────▶│──▶│ Webhook  │─▶│ Agent   │ │
  │ User │ HMAC   │   │ Handler  │  │ Worker  │ │
  └──────┘        │   └──────────┘  └────┬────┘ │
                  │                       │      │
  ┌──────┐        │   ┌──────────┐       │      │
  │Tenant│───────▶│──▶│  Admin   │◀──────┤      │
  │Admin │ HTTPS  │   │  Console │       │      │
  │      │+OAuth  │   └──────────┘       ▼      │
  └──────┘        │                  ┌────────┐ │
                  │                  │Postgres│ │
                  │                  │ S3, VD │ │
                  │                  └────┬───┘ │
                  │                       │      │
                  │   ┌──────────┐       │      │
                  │   │ Quota    │◀──────┤      │
                  │   │ Guard    │       │      │
                  │   └────┬─────┘       │      │
                  │        │             │      │
                  └────────┼─────────────┼──────┘
                           ▼             ▼
                       ┌──────┐     ┌────────┐
                       │ LLM  │     │ Backup │
                       │Prov. │     │   S3   │
                       └──────┘     └────────┘
                     (external)    (external)
```

**Trust boundaries**：
1. Public internet ↔ Webhook handler（HMAC + IP allowlist）
2. Public internet ↔ Admin Console（HTTPS + OAuth/JWT）
3. App ↔ DB / S3（VPC internal + IAM/RLS）
4. App ↔ LLM Provider（HTTPS + API key + 不傳 raw PII per ADR-0001 mitigation）

## 3. STRIDE 分析

### 3.1 Spoofing（身份偽造）

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-S-01** 偽造 LINE webhook | Webhook handler 公網 | HMAC SHA-256 簽章驗證（API-002）+ LINE IP allowlist |
| **T-S-02** 偽造 tenant admin 身份 | Admin console | ADR-0006 §1: password+MFA+JWT；login throttle |
| **T-S-03** JWT 偽造 / 重放 | API | RS256 簽章；short-lived（15min）；refresh rotation；JTI blacklist |
| **T-S-04** 偽造 internal service 身份 | Service-to-service | mTLS（ADR-0006 §4） |
| **T-S-05** 偽造 LLM provider 回應（中間人）| LLM API call | HTTPS strict cert validation；no http_proxy override |

### 3.2 Tampering（資料竄改）

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-T-01** 竄改 webhook payload | Webhook handler | HMAC 簽章 + payload schema 驗證 |
| **T-T-02** SQL injection | API endpoints | Parameterized query 強制；ORM；input validation；CI 加 sqlmap scan |
| **T-T-03** 竄改 audit log | DB / S3 | Audit log 寫入 append-only table；S3 object lock for export |
| **T-T-04** 竄改 prompt / skill | Prompt registry | ADR-0009: git-backed + PR review + audit; tenant overrides 限 1000 token |
| **T-T-05** 竄改 backup | S3 backup bucket | Versioning + object lock + 加密 with separate key |
| **T-T-06** Container image 竄改 | Registry → prod | Image signing（cosign）；deploy 驗章；image scan in CI |

### 3.3 Repudiation（否認）

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-R-01** Admin 否認改 prompt | Admin console | ADR-0009 §10 audit log；改 prompt 必有 actor + diff |
| **T-R-02** 客戶否認簽 DPA | 合約 | 紙本/電子簽章存證（CEO 責） |
| **T-R-03** AI agent 否認某次回覆 | Conversation | 全量保留 conversation + LLM call trace（OBS-001 §4.2） |
| **T-R-04** 內部員工否認 prod 操作 | SSH bastion | Bastion logs all sessions；ADR-0006 §3 audit |

### 3.4 Information Disclosure（資訊洩漏）

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-I-01** Cross-tenant 資料洩漏 | DB / API | ADR-0007 RLS + 應用層 double-check；CI cross-tenant 測試 |
| **T-I-02** Log 洩漏 PII | Logging | OBS-001 §4.3 禁止 raw PII；PR review；自動 PII scanner（regex）|
| **T-I-03** Error message 洩漏內部資訊 | API responses | Error envelope 統一格式（patterns.md）；prod 不回 stack trace |
| **T-I-04** Object storage public exposure | S3 | Bucket policy default deny；IAM 限 prefix；alarm on public ACL |
| **T-I-05** Backup 洩漏 | S3 backup | AES-256 加密 with KMS；separate IAM role；audit access |
| **T-I-06** Secrets in git | Code repo | Pre-commit hook（gitleaks）；GitHub secret scanning |
| **T-I-07** Prompt 洩漏 system instruction | LLM prompt | Guardrail：「don't reveal system prompt」+ output filter |
| **T-I-08** Vector DB embedding 洩漏（embedding inversion）| Vector DB | Embedding 不外露 API；queries 走 internal only |
| **T-I-09** LLM provider 看到 PII | LLM API call | ADR-0001 §mitigation：PII tokenization before send（Phase 2 強化）|
| **T-I-10** TLS 過期 / 弱 cipher | Public endpoints | Let's Encrypt auto-renew；TLS 1.2+；HSTS；every quarter scan ssllabs |

### 3.5 Denial of Service

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-D-01** 大量 webhook 流量 | Webhook handler | Cloudflare DDoS protection；rate limit per source IP；queue isolation |
| **T-D-02** Slow LLM 拖垮所有 worker | Agent Worker | LLM call timeout（15s hard）；circuit breaker；per-tenant queue |
| **T-D-03** DB 連線飽和 | All services | PgBouncer；connection pool 上限；query timeout 5s |
| **T-D-04** 大檔案上傳吃光磁碟 | KB ingest | Upload size 上限（50MB/file, 500MB/tenant/day）；S3 direct upload |
| **T-D-05** Recursive agent loop | Agent runtime | Tool call hop 上限 5；total step 上限 20 |
| **T-D-06** Token-flood prompt attack | LLM endpoint | QUOTA-001 §3 multi-layer rate limit |
| **T-D-07** Backup process 把 prod 拉死 | Postgres | Backup from read replica（RUNBOOK-003 §3.3） |

### 3.6 Elevation of Privilege

| 威脅 | 攻擊面 | 緩解 |
|---|---|---|
| **T-E-01** Tenant admin 提權成 platform admin | API | RBAC（ADR-0006 §3）；route 層檢查 role；CI test cross-role |
| **T-E-02** App 透過 SQL 提權成 superuser | DB | App DB user 限 RLS-enforced role；無 CREATE / DROP 權限 |
| **T-E-03** RCE via dependency vuln | All services | Dependabot；SBOM；critical CVE 7 天內 patch；container scan |
| **T-E-04** RCE via image processing（KB PDF）| Ingest worker | Sandbox（gVisor / Firecracker Phase 2）；resource limit；無網路 |
| **T-E-05** Container escape | Container runtime | Non-root；read-only filesystem where possible；drop capabilities |
| **T-E-06** Internal service 互信被濫用 | Service-to-service | mTLS + 每 service 限定可呼叫的對方 endpoints |

## 4. OWASP LLM Top 10（2024 版）對應

| LLM 風險 | 緩解 |
|---|---|
| **LLM01: Prompt Injection** | Input pre-filter（regex for "ignore previous", "reveal system"）；output filter；guardrail policy layer 獨立於 prompt（ADR-0009 §8）；audit suspicious patterns |
| **LLM02: Insecure Output Handling** | Output 不直接 eval；不直接 SQL/shell；output 經 sanitization 再 store/display；Markdown render 限白名單 |
| **LLM03: Training Data Poisoning** | Pilot 期不微調；用 OpenAI/Anthropic base model；ADR-0001 「no training on our data」契約條款 |
| **LLM04: Model Denial of Service** | 對應 T-D-05, T-D-06；QUOTA-001 全套 |
| **LLM05: Supply Chain Vulnerabilities** | Pin LLM SDK version；SBOM；不引未 audit 的 plugin |
| **LLM06: Sensitive Information Disclosure** | 對應 T-I-07, T-I-09；guardrail 過濾 PII output；prompt 不含真實密鑰 |
| **LLM07: Insecure Plugin Design** | Tool / skill 設計時：input schema 嚴格；output schema 嚴格；single responsibility；無系統呼叫權限 |
| **LLM08: Excessive Agency** | 限制 agent 可呼叫的工具集（per-tenant whitelist）；高風險操作（如發送訊息）需 confirm；audit 每次 tool call |
| **LLM09: Overreliance** | Guardrail：不確定 → escalate（AC-003）；UI 標示「AI 回覆，可能有誤」；50 題 test set 持續監控品質 |
| **LLM10: Model Theft** | 不在 Phase 1 自己訓練模型，N/A；後續若 fine-tune → 加 watermark + 限制 export |

## 5. 攻擊面評分（高 → 低）

| 攻擊面 | 暴露程度 | 影響度 | 優先級 |
|---|---|---|---|
| LINE Webhook | 公網 | 全 tenant 對話流 | **P0** |
| Admin Console Auth | 公網 | 單 tenant 完全控制 | **P0** |
| LLM Prompt Injection | 公網（via end-user） | 單對話 → 可放大 | **P0** |
| RLS / Cross-tenant | DB | 跨 tenant 災難 | **P0** |
| Backup / DR | Storage | 永久資料遺失 / 洩漏 | **P0** |
| KB Ingest（檔案處理） | API | RCE 風險 | **P1** |
| Dependency vuln | Code | RCE / lateral | **P1** |
| Internal SSH / bastion | 公網（限 IP） | 全系統控制 | **P1** |
| Service-to-service | 內網 | lateral | **P2** |

## 6. 控制措施 Checklist（Pilot 上線前必過）

### 6.1 必須完成（Go/No-Go）

- [ ] HMAC webhook 驗證 + 拒絕無簽章請求測試
- [ ] JWT 簽章驗證 + expired token 拒絕測試
- [ ] MFA 強制 for tenant admin
- [ ] RLS 啟用 + cross-tenant query 測試（TC-SEC-001）
- [ ] Secret scanning（gitleaks）pre-commit + CI
- [ ] Dependency scan（Dependabot）+ critical CVE 修完
- [ ] Container image scan（Trivy）in CI
- [ ] TLS 1.2+ only + HSTS + 證書自動續期
- [ ] OBS-001 §4.3 PII log 過濾驗證（PII scanner）
- [ ] LLM provider 「不訓練我方資料」合約條款（ADR-0001）
- [ ] Guardrail policy layer 上線（ADR-0009 §8）
- [ ] Backup 加密 + 驗證（RUNBOOK-003 §4）
- [ ] DPA 範本就緒（LEGAL-001）

### 6.2 Pilot 期完成

- [ ] 外部 pentest 一次（Week 8 前）
- [ ] DR drill 一次（RUNBOOK-003 §6）
- [ ] Prompt injection 攻擊紅隊測試
- [ ] SOC 2 readiness self-assessment（Phase 2 才正式申請）

## 7. 監控與告警對應

對應 OBS-001 §7：

| 告警 | 對應 STRIDE |
|---|---|
| `pii_audit_anomaly` | T-I-02, T-I-09 |
| `error_rate_high` | 廣泛 |
| `auth_failure_spike` | T-S-02, T-S-03 |
| `cross_tenant_query_detected` | T-I-01 |
| `prompt_injection_pattern_detected` | LLM01 |
| `llm_cost_spike` | T-D-06, LLM04 |
| `backup_failed` | T-T-05, T-I-05 |

## 8. 事故對應流程

任何 §3 / §4 威脅實際發生 → RUNBOOK-001 P0/P1 流程：

- 資料洩漏 → §4.4 PII 洩漏 playbook
- DoS → §4.5 / §4.6
- Cross-tenant 洩漏 → P0 + LEGAL-001 §8 客戶通報 72 小時
- Pentest 發現 critical → 7 天內 patch + 重測

## 9. 文件化的「明知不修」

Pilot 期接受、Phase 2 必修的風險（必須在 risk register 登記）：

| 風險 | 為何接受 | 何時修 |
|---|---|---|
| LLM provider 看到部分 PII（T-I-09） | Phase 1 token 化會大幅增加複雜度，且 OpenAI/Anthropic 有 zero retention 合約條款 | Phase 2 Q1 |
| 無 WAF | Cloudflare free tier 已給基本防護；Pilot 流量不大 | tenant > 20 |
| 無外部 SOC 2 | Pilot 客戶不要求；建立成本高 | Tenant 要求或 enterprise sale |
| 無內部 secret rotation 自動化 | 手動 90 天 OK | Phase 2 |
| Image sandbox 限 KB ingest | gVisor 設定複雜 | tenant > 10 或處理高敏感檔案 |

每項風險在 PR 引入時必須先 reference 此清單，避免「無聲帶入」。

## 10. 更新流程

- 本文件每季 review 一次
- 新 component 加入 SAD → 必須補對應 STRIDE row
- 任何 §3-§4 緩解控制被刪除 → CR 流程 + 更新本文件
- 外部 pentest 後依發現更新

---

**See also**:
- `SAD-v0.1.md` — 系統元件清單（攻擊面盤點來源）
- `NFR-001-non-functional-requirements.md` §3 — 安全基線需求
- `ADR-0005-data-retention-pii.md` — PII 處理對接
- `ADR-0006-auth-identity.md` — Auth 攻擊面緩解
- `ADR-0007-tenant-isolation.md` — Cross-tenant 攻擊面緩解
- `ADR-0009-prompt-versioning.md` §8 — Guardrail policy layer
- `QUOTA-001-llm-budget.md` §7 — LLM DoS / 注入緩解
- `OBS-001-observability-spec.md` §7 — 安全告警
- `LEGAL-001-DPA-template.md` §4 — 對客戶承諾的安全控制
- `RUNBOOK-001-incident-response.md` — 事故對應

---
id: ADR-0006
title: Auth and Identity Strategy
status: accepted
date: 2026-05-15
deciders: CTO
tier: 1
---

# ADR-0006 — 身份與認證策略

## Context

AEOS Phase 1 有 3 類「使用者」需要認證：

1. **Tenant Admin**（客戶方管理員）— 登入後台、看 dashboard、改 prompt、上傳 KB
2. **End-user**（客戶的終端使用者）— 透過 LINE 與 AI 互動；**不直接登入我們系統**，身份由 LINE 提供
3. **內部員工**（AEOS team）— SRE、CS、開發；需登入 admin console / DB / 監控

需求：
- Pilot 期 3~5 家客戶 × 1~3 admin/客戶 = 最多 15 個 admin user
- 多租戶資料隔離（對應 ADR-0007）
- 客戶可能要求 SSO（Phase 1 可不支援，但設計要為 Phase 2 預留）
- 內部員工需 MFA（NFR-001 §3）
- 必須 audit 每次 admin 動作

## Decision

### 1. Tenant Admin Auth

**選 Email + Password + MFA（TOTP），自建 auth service，預留 OIDC 介面。**

- 密碼存 Argon2id hash（不用 bcrypt — Argon2 是當前 OWASP 推薦）
- MFA 強制（TOTP via Google Authenticator / Authy）
- Session 機制：JWT（access token 15min）+ refresh token（rotating, 7 days）
- Login throttle：5 次失敗 → 15 分鐘鎖
- Recovery：email magic link（24h expiry）

**Phase 2 升級**：透過 OIDC adapter 支援客戶 SSO（Okta / Azure AD / Google Workspace）。介面從 day 1 就設計成「auth provider 可替換」。

**不選的方案**：
- ❌ **Auth0 / Clerk / Supabase Auth** — vendor lock-in + 每 user $0.05~0.15 在多 tenant 場景燒錢 + 客戶可能要求私有部署
- ❌ **OAuth via Google only** — 客戶 admin 不一定有 Google 帳號
- ❌ **Magic link only**（無密碼） — UX 對 B2B admin 不友善（每次登入點 email 太慢）

### 2. End-user Identity（LINE 使用者）

**透過 LINE User ID（`U` 開頭 33 字元）作為 stable identifier；不在我方系統建立帳號。**

- 每筆對話以 `(tenant_id, line_user_id)` 為主鍵
- 我方不存 LINE 使用者的 access token（不需要）
- 個資範圍：LINE displayName + 對話內容；遵 ADR-0005
- 跨 channel（Phase 2 加 Messenger/WhatsApp）：用 `external_id_provider` + `external_id` 表結構

### 3. 內部員工 Auth

**Google Workspace SSO（透過 OIDC）+ MFA 強制 + RBAC**

- SSO provider：Google Workspace（公司既有）
- 角色：
  - `aeos_admin`（CTO）— 全權
  - `aeos_engineer` — code deploy + prod read
  - `aeos_cs` — tenant admin console 代客操作（受限）
  - `aeos_finance` — billing dashboard read only
- 任何 prod 動作必走 SSH bastion + audit log
- SSH key 90 天輪換；MFA 強制
- Production DB 訪問必須走 jumphost + 雙人核可（敏感操作）

### 4. Service-to-Service Auth

- Internal API：mTLS（cert from internal CA）
- External webhook（接 LINE）：HMAC 簽章驗證（API-002 已定義）
- LLM Provider：API key 存 KMS；每月輪換
- 任何 secret 禁止進 git；用 env var + KMS 或 Vault（Phase 2）

### 5. Session 安全

| 屬性 | 值 |
|---|---|
| Access token | JWT, RS256, 15 min |
| Refresh token | Opaque, DB-backed, 7 days, rotating |
| Cookie flags | HttpOnly, Secure, SameSite=Lax |
| CSRF 防護 | Double-submit cookie pattern |
| Logout | Refresh token blacklist + access token 15min 自然過期 |
| Concurrent session | 同 user 最多 5 個 active session |

### 6. Password Policy

- 最少 12 字元
- 必含 3 種類別（大寫/小寫/數字/符號擇三）
- 不可與最近 5 次密碼重複
- 不檢查「定期換」（NIST SP 800-63B 已棄此要求）
- 與 haveibeenpwned API 比對（k-anonymity 模式，僅查 hash 前 5 字元）

## Consequences

### 正向

- 完全自有，無 vendor lock-in
- 預留 OIDC adapter 讓 Phase 2 SSO 接入成本低
- 多 tenant 場景成本可控（不按 user 計費）
- Audit trail 完整在我方

### 負向

- 自建 auth = 自負安全責任（必須通過 SEC-001 threat model 與外部 pentest）
- 開發成本 ~1 週（Pilot 期接受）
- MFA recovery 流程需要 CS 介入（Pilot 期可接受）

### 風險與緩解

| 風險 | 緩解 |
|---|---|
| Argon2 參數選錯（太弱或太重） | 採 OWASP 2024 推薦：memory=19MB, iterations=2, parallelism=1；每年 review |
| JWT secret 洩漏 → 全 user 受影響 | RS256（非對稱）+ key rotation + JWT 含 `kid` 支援 multi-key 並存 |
| Brute force | Login throttle + haveibeenpwned check + MFA |
| Session hijack | Cookie flags + SameSite + IP/UA 異常檢測（Phase 2） |
| MFA bypass via support 社工 | 嚴格 recovery 流程：書面 + CEO approve + 24h waiting period |

## Alternatives Considered

| 方案 | 為何不選 |
|---|---|
| **Auth0** | $228/月 + 多 tenant 場景 user 成本不可控 + 私有部署需 Enterprise plan（更貴）|
| **Clerk** | 同上，且台灣資料中心未必合規 |
| **Supabase Auth** | 綁 Supabase 整個 stack；我們已選自建 Postgres |
| **Keycloak self-host** | 重型，運維成本高；Pilot 期 over-engineer |
| **Ory（Hydra+Kratos）** | 過於 fragmented；Pilot 期難快速上線 |

## Implementation Notes

- 主程式碼：`services/auth/`
- 核心 lib：python `passlib[argon2]`、`pyjwt`、`pyotp`
- DB schema 變更：`migrations/20260520_auth.sql`（users, sessions, mfa_secrets, refresh_tokens, audit_log）
- 對應 contract：API-001 §1.2 Authentication

## Related

- ADR-0005 — PII 處理（auth 也產生 PII：email、IP）
- ADR-0007 — Tenant isolation（auth 與 tenant_id 綁定的邊界）
- ADR-0009 — Prompt versioning（admin 操作 prompt 需 audit）
- SEC-001 — Threat model（auth 是主要攻擊面）
- LEGAL-001 — DPA §4.1 對外承諾
- NFR-001 §3 — Security baseline

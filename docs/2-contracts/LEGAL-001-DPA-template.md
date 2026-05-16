---
id: LEGAL-001
title: Data Processing Agreement (DPA) Template
status: active
type: legal-template
created: 2026-05-15
last-synced-with: a5d7a75bd822b8cf7d2b6d8c3157060f50848e86
owner: CEO + CTO
tier: 2
related: [ADR-0005, NFR-001, SEC-001, OBS-001]
---

# LEGAL-001 — Data Processing Agreement 範本

> **這份是範本，不是法律意見。** 第一家 Pilot 客戶簽約前必須由律師審閱定稿。本文件目的：讓客戶 procurement / 法務 review 時，我們 30 分鐘內能交出可討論的草案，不卡進度。

## 0. 使用說明

| 角色 | 用法 |
|---|---|
| **CEO** | 對客戶代表 AEOS 簽約；填 §1 雙方資訊；§7 例外條款談判 |
| **CTO** | 確認 §3 §4 §5 技術措施與實際系統一致；任何不一致 → 立即修系統或更新文件 |
| **律師** | 第一家客戶簽約前審閱；之後每 6 個月或法規重大變更時審閱 |

填空項用 `<<...>>` 標示。

---

# Data Processing Agreement

This Data Processing Agreement (**"DPA"**) supplements the Service Agreement entered into between:

- **Data Controller**: <<Client Legal Name>>, with registered address at <<Client Address>> (**"Controller"** or **"Client"**)
- **Data Processor**: AEOS <<Legal Entity>>, with registered address at <<AEOS Address>> (**"Processor"** or **"AEOS"**)

Effective Date: <<YYYY-MM-DD>>

---

## 1. Definitions

- **"Personal Data"** has the meaning given in the applicable Data Protection Laws (including Taiwan《個人資料保護法》, EU GDPR where applicable).
- **"Processing"** means any operation performed on Personal Data, including collection, recording, storage, retrieval, use, disclosure, or erasure.
- **"Sub-processor"** means any third party engaged by Processor to assist in Processing.
- **"Data Subject"** means an identifiable natural person whose Personal Data is Processed.
- **"Applicable Data Protection Laws"** means Taiwan PDPA, and where applicable, GDPR, CCPA, and any successor or equivalent law.

## 2. Scope and Purpose

### 2.1 Nature of Processing

Processor processes Personal Data **solely** to provide the AI Customer Service Service ("Service") defined in the Service Agreement, including:

- Receiving and responding to end-user messages via LINE Official Account
- Generating AI replies using Large Language Models
- Storing conversation history for service continuity
- Generating analytics for Client

### 2.2 Categories of Personal Data

Processor may process the following categories:

| Category | Examples |
|---|---|
| Contact data | Name, phone, LINE user ID, email |
| Conversation content | Messages between end-users and AI |
| Order / transaction reference | Order IDs, partial product names |
| Technical data | IP address, user agent, timestamps |
| Behavioral data | Click events, session duration |

Processor **shall not** process special category data (health, biometric, financial card numbers) unless explicitly agreed in writing.

### 2.3 Categories of Data Subjects

- End-users (customers) of Client interacting with Client's LINE Official Account
- Client's internal users (administrators)

### 2.4 Duration

Processing duration matches the Service Agreement term plus the retention period in §6.

## 3. Processor Obligations

Processor shall:

1. **Process only on documented instructions** from Controller, unless required by law (in which case Processor will inform Controller before processing, unless legally prohibited);
2. **Ensure confidentiality** — all personnel authorized to process Personal Data are bound by confidentiality obligations;
3. **Implement technical and organizational measures** as set out in §4;
4. **Assist Controller** in fulfilling Data Subject Rights requests (§8) within the time limits set by applicable law;
5. **Notify Controller without undue delay** (and in any case within **72 hours**) upon becoming aware of a Personal Data Breach, providing:
   - Nature and scope of the breach
   - Categories and approximate number of Data Subjects affected
   - Likely consequences
   - Measures taken or proposed
6. **Allow audits** by Controller or its mandated auditor, with reasonable prior notice (not less than 14 days), no more than once per 12-month period unless triggered by a Breach;
7. **Delete or return** all Personal Data upon termination per §6;
8. **Maintain records** of Processing activities as required by Applicable Data Protection Laws.

## 4. Technical and Organizational Measures

Processor implements the following measures (aligned with `ADR-0005`, `SEC-001`, `OBS-001`):

### 4.1 Access Control
- Role-Based Access Control (RBAC) with least privilege
- Multi-Factor Authentication for all production access
- Access logs retained ≥ 13 months
- Access reviews every 6 months

### 4.2 Encryption
- **In transit**: TLS 1.2+ for all external communications
- **At rest**: AES-256 for databases, object storage, backups
- Key management: dedicated KMS; key rotation every 12 months

### 4.3 Network Security
- Production isolated in dedicated VPC / network
- Firewall with default-deny ingress
- DDoS mitigation at edge

### 4.4 Data Segregation
- Multi-tenant data segregation via `tenant_id` enforcement at application and DB layer
- Per-tenant cryptographic key (Phase 2 target)

### 4.5 Backup and Recovery
- Daily encrypted backups, retained 30 days
- Backup restoration tested quarterly
- Recovery objectives: RTO ≤ 4 hours, RPO ≤ 24 hours (see `RUNBOOK-003`)

### 4.6 Logging and Monitoring
- All access to Personal Data logged in audit log (`OBS-001 §4.2`)
- Anomaly detection on data access patterns
- 24/7 alerting on security events

### 4.7 Vulnerability Management
- Dependency scanning on every commit
- Quarterly penetration testing (commissioned externally)
- Critical CVE patched within 7 days

### 4.8 Personnel
- Background checks on production access personnel
- Annual security training
- Documented onboarding/offboarding procedures

## 5. Sub-processors

### 5.1 General Authorization

Controller grants Processor general authorization to engage Sub-processors, **provided** Processor:

1. Imposes data protection obligations on Sub-processors equivalent to this DPA;
2. Remains fully liable to Controller for Sub-processor performance;
3. Maintains an up-to-date list of Sub-processors (see §5.2);
4. Notifies Controller of changes with **at least 30 days** notice; Controller may object on reasonable data protection grounds.

### 5.2 Current Sub-processors

| Sub-processor | Service | Location | Personal Data |
|---|---|---|---|
| <<LLM Provider e.g., OpenAI / Anthropic>> | AI model inference | <<US / EU>> | Conversation content (no raw PII per ADR-0001 mitigation) |
| <<Cloud Provider e.g., Hetzner / AWS>> | Compute, storage | <<EU>> | All data |
| LINE Corporation | Messaging channel | Japan | Conversation routing metadata |
| <<Email Provider e.g., SendGrid>> | Transactional email | <<US>> | Email addresses only |
| <<Monitoring e.g., Better Uptime>> | Uptime monitoring | <<EU>> | No PII (technical metrics only) |

*Current as of <<DPA execution date>>.*

### 5.3 International Transfers

Where Personal Data is transferred outside Taiwan / EEA, Processor relies on:
- Standard Contractual Clauses (EU SCCs) where applicable;
- Adequacy decisions where applicable;
- Other transfer mechanisms per Applicable Data Protection Laws.

## 6. Retention and Deletion

| Data Category | Retention |
|---|---|
| Conversation content | 13 months from last interaction, then anonymized |
| Order / transaction references | 13 months |
| Technical / behavioral data | 13 months |
| Audit logs | 13 months (legal minimum) |
| Backups | 30 days rolling |

**Upon termination**:
- Processor returns Personal Data in machine-readable format within 30 days upon Controller's written request;
- After return (or if no request), Processor securely deletes all Personal Data within 60 days from termination;
- Deletion confirmation provided in writing.

**Exceptions**: Processor may retain data only to the extent required by law, in which case it must inform Controller of the legal basis and retention period.

## 7. Data Subject Rights

Processor shall assist Controller in fulfilling the following rights of Data Subjects within the time limits required by Applicable Data Protection Laws (typically 30 days):

| Right | Mechanism |
|---|---|
| Access | Controller's admin console + Processor support |
| Rectification | Controller's admin console |
| Erasure ("right to be forgotten") | Controller initiates via admin console or written request to Processor |
| Restriction of Processing | Controller initiates |
| Data Portability | Machine-readable export from admin console |
| Objection | Routed to Controller |

Costs of assistance: included in Service fee for ≤ 10 requests/month; above this, time-and-materials per Service Agreement.

## 8. Breach Notification

### 8.1 By Processor to Controller
- Within **72 hours** of becoming aware
- Include information per §3 item 5
- Single point of contact: <<AEOS Security Email>>

### 8.2 By Controller to Authorities / Data Subjects
- Controller's responsibility under Applicable Data Protection Laws
- Processor assists with documentation and remediation

## 9. Audits

- Annual SOC 2 / ISO 27001 reports (when available, Phase 3+) shared on request and under NDA
- On-site audit: 14 days prior written notice, business hours, no more than once per 12 months
- Audit must not unreasonably interfere with Processor operations

## 10. Liability and Indemnification

Liability under this DPA is governed by the Service Agreement.

Notwithstanding the foregoing, Processor's liability for breaches of data protection obligations is **uncapped** to the extent required by Applicable Data Protection Laws.

## 11. Termination

This DPA terminates upon the later of:
- Termination of the Service Agreement
- Completion of return / deletion obligations under §6

Sections 6, 8, 10 survive termination.

## 12. Governing Law and Jurisdiction

Governed by <<jurisdiction, e.g., laws of Taiwan>>.
Disputes: <<courts of Taipei>> (or arbitration per Service Agreement).

## 13. Order of Precedence

In case of conflict:
1. Applicable Data Protection Laws
2. This DPA
3. Service Agreement
4. Any other written agreements

---

**Signed**:

| Controller | Processor |
|---|---|
| Name: <<Client Rep>> | Name: <<AEOS Rep>> |
| Title: | Title: |
| Date: | Date: |
| Signature: | Signature: |

---

## Annex A — Processing Activities Record (Article 30 GDPR equivalent)

| Item | Detail |
|---|---|
| Controller | <<Client>> |
| Processor | AEOS |
| Categories of Data Subjects | §2.3 |
| Categories of Personal Data | §2.2 |
| Recipients (incl. Sub-processors) | §5.2 |
| Transfers to third countries | §5.3 |
| Retention | §6 |
| Technical measures | §4 |

---

**See also**:
- `ADR-0005-data-retention-pii.md` — 內部 PII 政策（與本 DPA 一致性必須維護）
- `SEC-001-threat-model.md` (TODO) — 安全控管細節
- `OBS-001-observability-spec.md` §4.2, §9 — audit log 與 PII 處理
- `RUNBOOK-001-incident-response.md` §4.4 — PII 洩漏事故處理
- `RUNBOOK-003-backup-dr.md` — RTO/RPO 實作
- `LEGAL-002-SOW-template.md` (TODO) — 商業合約範本

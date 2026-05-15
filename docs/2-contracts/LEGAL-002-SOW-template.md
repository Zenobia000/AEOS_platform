---
id: LEGAL-002
title: Statement of Work (SOW) Template — Pilot
status: active
type: legal-template
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CEO + CTO
tier: 2
related: [LEGAL-001, PILOT-001, PRD-001, AC-001-to-005, PLAYBOOK-001, NFR-001]
---

# LEGAL-002 — Pilot SOW 範本

> 本文件是 Pilot 期合約範本。**第一家客戶簽約前須由律師審閱定稿**。CEO 用此範本作為談判起點，避免每次重寫。

填空項用 `<<...>>` 標示。

---

# Statement of Work — AEOS Pilot Program

This Statement of Work (**"SOW"**) is entered into between:

- **Client**: <<Client Legal Name>>, <<Address>>
- **Provider**: AEOS <<Legal Entity>>, <<Address>>

**Effective Date**: <<YYYY-MM-DD>>
**SOW Number**: AEOS-PILOT-<<YYYY-MM-###>>

This SOW is governed by the Master Service Agreement / Service Agreement and Data Processing Agreement (LEGAL-001) executed between the parties.

---

## 1. Definitions

- **"Service"** — AEOS AI Customer Service platform, including AI agent, KB ingest, test set tooling, admin console, and LINE channel integration.
- **"Pilot Period"** — defined in §2.
- **"AI Employee"** — the configured AI agent instance for Client.
- **"End User"** — Client's customer interacting with AI Employee via LINE.
- **"Test Set"** — collaboratively authored 50 questions with expected responses, used for quality measurement.

## 2. Pilot Period

- **Start Date**: <<2026-MM-DD>>
- **End Date**: <<2026-MM-DD>> (12 weeks)
- **Includes**: 7-day onboarding (Week 0) + 11 weeks Active Pilot
- **Total Duration**: 12 weeks

## 3. Scope of Service

### 3.1 Provider Delivers

| Deliverable | Timing |
|---|---|
| AI Employee instance configured for Client | Week 0 (7-day onboarding per PRD-001) |
| KB ingest of Client-provided materials (≤ 500 pages) | Week 0 |
| LINE channel integration | Week 0 |
| Admin Console access for Client (≤ 5 admin seats) | Week 0 |
| Initial Test Set baseline | Week 1 |
| Weekly health report (auto-generated) | Each Friday |
| Bi-weekly 30-min sync call (CEO/CTO present) | Every 2nd Tuesday |
| Monthly KPI dashboard review | Last week each month |
| Incident response per SLA (§5) | Continuous |
| End-of-Pilot report with GA recommendation | Week 12 |

### 3.2 Client Provides

| Item | Timing |
|---|---|
| LINE Official Account access (channel access token, secret) | Pre-Week 0 |
| Knowledge materials (FAQ, SOP, product info, ≤ 500 pages) | Pre-Week 0 |
| Designated point of contact (1 primary, 1 backup) | Pre-Week 0 |
| Co-authoring of Test Set (target: 50 Q&A pairs) | Weeks 1-3 |
| Feedback on AI responses (escalations reviewed weekly) | Continuous |
| Attendance at sync calls | Bi-weekly |
| Approval to be referenced (anonymized) in marketing materials | Optional, post-Pilot |

### 3.3 Out of Scope (Phase 1)

The following are **excluded** from this Pilot and will be considered separately if Client engages for GA service:

- Channels other than LINE (Messenger, WhatsApp, web chat, voice)
- Custom integrations with Client's CRM / ERP / other systems
- Multilingual support beyond Traditional Chinese
- Custom AI model training / fine-tuning
- White-label / branded UI
- Self-serve admin features beyond what is provided
- Compliance certifications (SOC 2, ISO 27001) — currently in progress
- On-premise deployment

## 4. Fees and Payment

### 4.1 Pilot Pricing

- **Base Fee**: NT$ <<Amount>> per month (50% discount from standard pricing)
- **Setup Fee**: Waived for Pilot participants
- **Usage Allowance**: Included up to 10,000 conversations / month and 100,000 LLM tokens / day (see Annex A)
- **Overage**: Provider notifies Client before any charges; Client may approve overage or operate within Allowance

### 4.2 Payment Terms

- Invoiced monthly in advance, net 30 days
- Currency: TWD (or USD if agreed)
- Payment method: bank transfer / credit card (via Client's preferred method)
- Late payment: 1.5% monthly interest after 30 days past due

### 4.3 Pilot to GA Conversion

If Client elects to continue post-Pilot:
- Standard pricing (TBD per usage tier) applies from Week 13
- 30-day notice if Client increases / decreases usage tier
- Pilot pricing **does not** carry over

## 5. Service Levels (SLA)

### 5.1 Availability

| Metric | Target |
|---|---|
| Service Uptime (rolling 30 days) | 99.5% |
| Scheduled Maintenance | ≤ 4 hours / month, with ≥ 24 hour notice |

**Service Credits** (Pilot-discounted credit, applied to next invoice):

| Uptime | Credit |
|---|---|
| < 99.5% and ≥ 99.0% | 5% of monthly fee |
| < 99.0% and ≥ 98.0% | 10% of monthly fee |
| < 98.0% | 20% of monthly fee |

### 5.2 Incident Response

(Per PLAYBOOK-001 §3.2)

| Severity | First Response | Resolution Target |
|---|---|---|
| S1 (service down / data breach) | 15 minutes | 4 hours (mitigation) |
| S2 (core function unusable) | 1 hour | 1 business day |
| S3 (partial degradation) | 4 hours | 5 business days |
| S4 (cosmetic / docs) | 1 business day | Next sprint |

### 5.3 Performance

Per NFR-001 §1:

| Metric | Target (p95) |
|---|---|
| End-to-end reply latency | ≤ 8 seconds |
| Webhook acknowledgment | ≤ 800ms |
| Admin Console response time | ≤ 2 seconds |

### 5.4 Quality

(Per PILOT-001 §2.1)

| Metric | Target by Week 12 |
|---|---|
| Auto-resolution rate | ≥ 70% |
| Test Set pass rate | ≥ 85% |
| Escalation correctness | ≥ 95% |

If targets are not met by Week 12, Provider commits to remedy plan; failure to meet within 4 weeks gives Client right to terminate without penalty.

## 6. Data and Privacy

Governed by the Data Processing Agreement (LEGAL-001) executed separately. Highlights:

- All data segregated per tenant (ADR-0007)
- Encrypted in transit (TLS 1.2+) and at rest (AES-256)
- 13-month retention; deletion on termination per LEGAL-001 §6
- Provider does not use Client data to train AI models
- 72-hour breach notification (LEGAL-001 §8)

Client retains ownership of all knowledge materials and conversation data.

## 7. Termination

### 7.1 Termination for Convenience
Either party may terminate this Pilot SOW with **14 days written notice**. No early-termination fees apply.

### 7.2 Termination for Cause
Either party may terminate immediately upon material breach unremedied within 14 days of written notice, including:
- Failure to pay invoices within 60 days of due date (Provider)
- Breach of confidentiality / data protection obligations (either)
- Insolvency / bankruptcy

### 7.3 Effect of Termination
- Provider stops processing data within 24 hours of termination
- Provider returns data in machine-readable format within 30 days upon Client request
- Provider deletes data within 60 days (LEGAL-001 §6)
- Pro-rata refund of pre-paid unused fees
- Service Credits accrued become payable as monetary refund if Client terminates for Provider's breach

### 7.4 Survival
§§6 (Data and Privacy), 8 (Confidentiality), 10 (Liability), 11 (IP) survive termination.

## 8. Confidentiality

Each party agrees to:
- Use the other's Confidential Information solely to perform this SOW
- Protect with at least the same care as own confidential data (and no less than reasonable care)
- Not disclose to third parties except sub-processors (under equivalent obligations) or as legally required
- Return / destroy upon termination

Obligations survive 3 years post-termination.

Excludes information that is: (a) public; (b) independently developed; (c) lawfully received from third party without obligation; (d) required by law to disclose (with prompt notice to the other party).

## 9. Representations and Warranties

### 9.1 Mutual
- Each party has authority to enter this SOW
- Performance does not violate any agreement or law

### 9.2 Provider
- Service performs materially as described in PRD-001
- Free from malicious code (commercially reasonable measures)
- Complies with Applicable Data Protection Laws

### 9.3 Client
- Has authority to provide knowledge materials
- Knowledge materials do not infringe third-party rights
- Has obtained necessary consents for End User data processing (LINE Terms of Service)

### 9.4 Disclaimer
**AI Employee responses are AI-generated and may contain errors.** Client acknowledges this and agrees to use Provider's escalation tooling (PLAYBOOK-001) for cases where AI response is unsuitable. Provider does not warrant 100% accuracy.

## 10. Liability

### 10.1 Cap
Provider's aggregate liability under this SOW is capped at **the greater of**: (a) fees paid by Client in the 12 months preceding the claim; or (b) USD 10,000.

### 10.2 Exclusions from Cap (uncapped)
- Breach of confidentiality (§8)
- Breach of data protection obligations (LEGAL-001)
- Indemnification obligations (§12)
- Gross negligence or willful misconduct

### 10.3 Excluded Damages
Neither party liable for indirect, consequential, special, incidental, or punitive damages, except for breaches uncapped under §10.2.

## 11. Intellectual Property

### 11.1 Provider IP
Provider retains all rights in Service, including AI Employee software, prompts, infrastructure, methodology.

### 11.2 Client IP
Client retains all rights in knowledge materials, brand assets, conversation data.

### 11.3 License Grants
- Client grants Provider a limited, non-exclusive license to use knowledge materials and data **solely to provide the Service**.
- Provider grants Client a limited, non-exclusive, non-transferable license to use Service during the Pilot Period.

### 11.4 Test Set
Test Set is **jointly owned**; both parties may use post-termination for benchmarking and improvement (with PII removed).

## 12. Indemnification

### 12.1 Provider Indemnifies
Provider indemnifies Client against third-party claims that the Service (excluding Client-provided content) infringes third-party IP rights.

### 12.2 Client Indemnifies
Client indemnifies Provider against third-party claims arising from:
- Client-provided knowledge materials
- Client's use of Service outside the scope (§3.3)
- Breach of §9.3 representations

### 12.3 Process
Indemnified party gives prompt notice; indemnifying party controls defense (with indemnified party's counsel at indemnified party's cost permitted).

## 13. Insurance

Provider maintains:
- Commercial General Liability: ≥ USD 1M per occurrence (Phase 1 evolving target)
- Cyber Liability: ≥ USD 1M (target by GA)
- Errors & Omissions: ≥ USD 500K (target by GA)

Pilot phase: Provider working toward above; gaps disclosed in writing on request.

## 14. Force Majeure

Neither party liable for delay/failure due to events beyond reasonable control (natural disaster, war, pandemic, government action). Affected party provides prompt notice and works diligently to resume. If lasting > 30 days, either may terminate.

**Note**: LLM provider outages are NOT force majeure if Provider's fallback strategy (ADR-0001) reduces impact below SLA thresholds.

## 15. Governing Law and Dispute Resolution

- Governed by laws of <<Taiwan / agreed jurisdiction>>
- Venue: <<Taipei District Court>> exclusive jurisdiction
- Prior to litigation: 30-day good-faith negotiation period
- Optional: mediation via <<institution>>

## 16. Miscellaneous

### 16.1 Entire Agreement
This SOW + MSA + DPA constitute the entire agreement on the subject matter, superseding prior discussions.

### 16.2 Amendments
Written and signed by both parties.

### 16.3 Assignment
Neither party may assign without other's written consent, except to a successor in a merger / acquisition (with notice).

### 16.4 Severability
If any provision is unenforceable, remainder survives.

### 16.5 Notices
Email to designated representatives + courier for formal notices:

| Party | Email | Address |
|---|---|---|
| Provider | <<email>> | <<address>> |
| Client | <<email>> | <<address>> |

### 16.6 Counterparts / e-Signature
This SOW may be executed in counterparts and via e-signature.

---

**Signed**:

| Client | Provider (AEOS) |
|---|---|
| Name: | Name: |
| Title: | Title: |
| Date: | Date: |
| Signature: | Signature: |

---

## Annex A — Usage Allowance and Overage

| Resource | Pilot Allowance | Overage Pricing |
|---|---|---|
| Conversations / month | 10,000 | NT$ <<X>> per 1,000 extra |
| LLM tokens / day | 100,000 | NT$ <<X>> per 100K tokens |
| KB ingest pages | 500 (cumulative) | NT$ <<X>> per 100 pages |
| Admin seats | 5 | NT$ <<X>> per seat / month |

Per QUOTA-001. Provider monitors and notifies Client at 80% and 100% of allowance.

## Annex B — Onboarding Schedule (7 Days)

Per PRD-001:
- Day 1: Kickoff + access provisioning
- Day 2-3: KB ingest + initial config
- Day 4: Test Set co-authoring kickoff (10 questions)
- Day 5: AI tuning + Test Set 20 more
- Day 6: Sandbox testing + Test Set 20 more
- Day 7: Go-live + monitoring setup

## Annex C — Acceptance Criteria

Per AC-001 ~ AC-005:
- AC-001: Auto-resolution rate ≥ 70% by Week 8
- AC-002: Test Set pass rate ≥ 85% by Week 8
- AC-003: Escalation correctness ≥ 95%
- AC-004: p95 latency ≤ 8s
- AC-005: Onboarding completed within 7 days

---

**See also**:
- `LEGAL-001-DPA-template.md` — Data Processing Agreement (referenced §6)
- `PILOT-001-success-criteria.md` — Internal success metrics (basis for §5.4)
- `PRD-001-7day-ai-cs-onboarding.md` — Product definition (basis for §3, Annex B)
- `AC-001-to-005-acceptance-criteria.md` — Acceptance criteria (Annex C)
- `PLAYBOOK-001-cs-escalation.md` — Support and escalation
- `NFR-001-non-functional-requirements.md` §1, §2 — Performance / availability basis
- `QUOTA-001-llm-budget.md` — Usage allowances
- `ADR-0001-llm-provider-strategy.md` — Force majeure carve-out reference

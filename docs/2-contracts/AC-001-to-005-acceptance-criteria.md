---
id: AC-001..AC-005
title: Acceptance Criteria (BDD) for UF-001 to UF-005
status: active
type: acceptance-criteria
created: 2026-05-14
last-synced-with: efb63b3efff9a280e178f46124f39db8d0141b54
owner: CTO
tier: 2
related: [UF-001, UF-002, UF-003, UF-004, UF-005, NFR-001]
---

# Acceptance Criteria — AC-001 ~ AC-005

> BDD Gherkin 風格。每個 UF 對應一個 AC，內含 5–10 個 scenario。CI 用同樣 scenario 跑（pytest-bdd or behave）。
> 一個 scenario 跑得過才算 feature done。

## AC-001 — Expert 上傳 KB → KC draft → review → approve（對應 UF-001）

```gherkin
Feature: KB Ingest and Knowledge Card review
  As an Expert
  I want to upload existing FAQ documents and review the generated Knowledge Cards
  So that the AI employee has trustworthy knowledge to answer customers

  Background:
    Given a tenant "小貓咖啡" exists with an active subscription
    And I am logged in as an Expert of "小貓咖啡"

  Scenario: Successful PDF ingest
    Given I am on the "/knowledge" page
    When I upload a valid 5-page PDF named "faq.pdf"
    Then I see an "Ingest 中..." progress within 1 second
    And within 3 minutes the ingest_job status becomes "done"
    And I see at least 5 draft KnowledgeCards in the list

  Scenario: KC draft review and approval
    Given there are 5 draft KnowledgeCards from "faq.pdf"
    When I open the first KC and edit the title to "店家營業時間"
    And I click "Save Draft"
    Then the KC body is saved and status remains "draft"
    When I click "Approve"
    Then the KC status becomes "approved"
    And an audit event "KC_APPROVED" is recorded with my username

  Scenario: Reject obvious garbage
    Given there is a draft KC with content "page 3 footer ©2024"
    When I click "Archive" for that KC
    Then the KC status becomes "archived"
    And the archived KC is excluded from retrieval

  Scenario: File too large rejected
    When I upload a 25 MB PDF
    Then I see an error "File exceeds 20 MB limit"
    And no ingest_job is created

  Scenario: URL ingest
    Given the URL "https://example.com/faq" returns valid HTML
    When I submit it as a URL source
    Then KCs are generated from the parsed HTML within 1 minute

  Scenario: Approving already-approved KC is rejected
    Given a KC with status "approved"
    When the API receives POST /knowledge-cards/{id}/approve
    Then the response is 409 with code "CONFLICT"
```

---

## AC-002 — Test Set Co-Authoring + Run（對應 UF-002）

```gherkin
Feature: Test Set authoring and execution
  As an Expert
  I want to write 50 test questions and run them against the AI
  So that I can verify accuracy before going live

  Background:
    Given an Employee "小美客服" in status "draft" with at least 5 approved KCs

  Scenario: Save 50 test cases
    Given I am on "/test-sets/{id}"
    When I fill 50 rows with question + expected_outcome
    Then each row is autosaved within 5 seconds
    And the test set has exactly 50 cases

  Scenario: Run test set completes within 5 minutes
    Given a test set with 50 cases linked to "小美客服"
    When I click "Run Test"
    Then a test_run is created with status "running"
    And within 5 minutes the run status becomes "done"
    And pass_rate is computed and shown

  Scenario: Pass rate meets Day 5 gate
    Given a test_run completed
    When pass_rate >= 0.70
    Then the Day 5 decision point is marked "go"

  Scenario: Failed case detail viewable
    Given a test_run with a failed case
    When I expand the case row
    Then I see the AI response text, retrieved KC list, and judgment reason

  Scenario: Add KC from failed case
    Given a failed case
    When I click "Add KC to fix this"
    Then I am redirected to /knowledge with the failed question prefilled as context

  Scenario: Re-run a single case
    Given a failed case
    When I click "Re-run this"
    Then only that case is rerun and result updated in place

  Scenario: Override LLM judgment
    Given a case where AI response is correct but LLM judge marked fail
    When I click "Mark actually correct"
    Then the case is marked passed and pass_rate is recomputed
```

---

## AC-003 — Draft Mode 收訊 + Expert Approve（對應 UF-003）

```gherkin
Feature: Draft Mode message review
  As an Expert
  I want to review every AI draft before it is sent
  So that the customer never sees an unreviewed AI reply during Day 6

  Background:
    Given Employee "小美客服" status is "live" with auto_reply_pct = 0
    And LINE webhook is configured with valid signature
    And I am logged in as Expert

  Scenario: Webhook receives message and acks within 1 second
    Given a LINE user sends a text message
    When LINE POSTs the webhook event
    Then the AEOS API returns 200 within 1 second
    And a Message row with status="draft_pending" exists within 5 seconds

  Scenario: Reject invalid signature
    Given a webhook request with wrong X-Line-Signature
    When AEOS receives it
    Then the response is 403
    And no Message row is created
    And an audit event "WEBHOOK_SIG_INVALID" is recorded

  Scenario: Expert approves draft
    Given a draft message in Draft Inbox
    When I click "Approve & Send"
    Then the LINE Push API is called with the original draft text
    And the message status becomes "sent"
    And an audit event "EXPERT_APPROVED" is recorded

  Scenario: Expert edits and sends
    Given a draft message with original text "我們週日休息"
    When I edit to "我們週日固定公休，週一到週六營業 09:00-21:00" and click "Send"
    Then the LINE Push API receives the edited text
    And the audit event "EXPERT_EDITED" contains the diff

  Scenario: Expert rejects, takes over
    Given a draft message
    When I click "Reject"
    And I fill the reason "Customer angry, need human"
    Then the message status becomes "expert_takeover"
    And no auto reply is sent to the user

  Scenario: Draft generation under 5 seconds
    Given a user message just received
    When the worker processes it
    Then the draft message exists in DB with p95 <= 5 seconds

  Scenario: Pending overflow alerts
    Given 21 messages with status "draft_pending"
    When the count crosses 20
    Then an alert is sent to the Expert via LINE Notify

  Scenario: Idempotent webhook redelivery
    Given a webhook with webhookEventId="X1"
    When LINE redelivers the same event with isRedelivery=true
    Then AEOS returns 200 but only one Message row exists for X1
```

---

## AC-004 — Canary Auto Reply with Confidence（對應 UF-004）

```gherkin
Feature: Canary auto reply with confidence threshold
  As CTO
  I want to gradually enable auto reply with a safety threshold
  So that low-confidence messages still fall back to Draft Mode

  Background:
    Given Employee "小美客服" status is "live"
    And the system clock starts fresh (no anomaly flag)

  Scenario: Enable 10% canary
    Given I am logged in as CTO
    When I set auto_reply_pct to 10
    Then employee.auto_reply_pct is 10 in DB
    And an audit event "CANARY_ROLLOUT" is recorded

  Scenario: High-confidence message in auto bucket sent directly
    Given auto_reply_pct = 10
    And a user message with conv_id whose hash%100 = 5 (in bucket)
    And the LLM returns confidence 0.85
    When the worker processes the message
    Then the LINE Push is called within 8 seconds end-to-end
    And the message status is "sent" with auto=true

  Scenario: High-confidence but out of bucket falls to draft
    Given auto_reply_pct = 10
    And a conv_id whose hash%100 = 50 (out of bucket)
    And LLM confidence 0.90
    When the worker processes the message
    Then the message status is "draft_pending"

  Scenario: Low confidence always draft
    Given auto_reply_pct = 100
    And LLM confidence 0.50 (below 0.75 threshold)
    When the worker processes the message
    Then the message status is "draft_pending"
    And audit event "DRAFT_GENERATED" has fallback_reason "low_confidence"

  Scenario: Anomaly downgrades to draft mode
    Given a P0 incident occurred 30 minutes ago
    And auto_reply_pct = 100
    When a new user message arrives
    Then the message status is "draft_pending"
    And audit event has fallback_reason "anomaly_flag"

  Scenario: End-to-end latency under load
    Given 10 concurrent user messages all in auto bucket with high confidence
    When the worker processes them
    Then p95 end-to-end latency (LINE → user receives) is <= 8 seconds
```

---

## AC-005 — Emergency Kill Switch（對應 UF-005）

```gherkin
Feature: Emergency kill switch
  As CTO
  I want a one-click way to disable AI replies
  So that I can stop a runaway AI within 30 seconds

  Background:
    Given Employee "小美客服" status is "live"
    And I am logged in as CTO

  Scenario: Disable requires reason and confirmation
    Given I navigate to /admin
    When I click "DISABLE AI"
    Then I see a confirmation modal requiring a reason
    When I leave reason empty and click confirm
    Then the request is rejected with validation error

  Scenario: Disable takes effect within 30 seconds
    Given I confirm disable with reason "Customer angry incident"
    When the API returns 200
    Then employee.status is "paused" in DB
    And within 30 seconds new incoming messages get status "expert_takeover" (no LLM call)

  Scenario: Audit and notify on disable
    When I disable AI with a reason
    Then audit event "EMERGENCY_DISABLE" contains: actor=me, reason, timestamp
    And a Slack/Email alert is sent to CEO and CTO within 60 seconds

  Scenario: Messages during paused are not lost
    Given employee status is "paused"
    When 5 user messages arrive in 1 minute
    Then 5 Message rows exist with status="expert_takeover"
    And none of them triggered LLM calls

  Scenario: Re-enable returns to live
    Given employee status is "paused"
    When I click "Re-enable AI" and confirm
    Then employee.status is "live"
    And audit event "EMERGENCY_REENABLED" is recorded
    And subsequent messages route normally (auto/draft per pct)

  Scenario: Expert cannot disable
    Given I am logged in as Expert (not CTO)
    When I navigate to /admin
    Then the page returns 403 Forbidden
```

---

## 共通 Definition of Done（每個 feature 適用）

每個 scenario 通過後，還需：

- [ ] 對應 UF / SF / API 文件無 drift（執行 `sunnydata-doc-freshness` 通過）
- [ ] Unit test 覆蓋 ≥ 80%
- [ ] Integration test 覆蓋此 feature 的 happy path + 至少 1 個 alt flow
- [ ] Audit event 全發（cross-check audit_event table）
- [ ] NFR 對應指標達標（見 NFR-001）
- [ ] CTO 過 PR review

## 連結
- 對應 User Flow：`UF-001` ~ `UF-005`
- 對應 System Flow：`SF-001` ~ `SF-005`
- API contract：`API-001`, `API-002`
- NFR：`NFR-001`
- 測試框架：`vibecoding-write-bdd` skill 用同樣 Gherkin 結構

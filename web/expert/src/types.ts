export interface ReviewItem {
  outbound_id: string;
  conversation_id: string;
  channel: string;
  channel_user_id: string;
  message_id: string;
  draft_text: string | null;
  created_at: string | null;
}

export interface ReviewListResponse {
  items: ReviewItem[];
  count: number;
}

export interface ActionResponse {
  outbound_id: string;
  action: "approved" | "edited" | "rejected";
  new_status: string;
  handoff_id?: string | null;
}

export type ReviewAction = "approve" | "edit" | "reject";

export type KCCardType = "faq" | "policy" | "product" | "procedure" | "risk";

export interface KCDraftItem {
  kc_id: string;
  tenant_id: string;
  card_type: KCCardType;
  title: string;
  body_markdown: string;
  tags: string[];
  source_url: string | null;
  source_file_ref: string | null;
  created_at: string | null;
}

export interface KCListResponse {
  items: KCDraftItem[];
  count: number;
}

export interface KCActionResponse {
  kc_id: string;
  action: "approved" | "edited" | "archived";
  new_status: string;
}

// ── TestSet types ──

export interface TestCaseItem {
  case_id: string;
  tenant_id: string;
  name: string;
  user_input: string;
  expected_outcome: string;
  expected_keywords: string[];
  enabled: boolean;
  created_by: string | null;
  created_at: string | null;
}

export interface TestCaseListResponse {
  items: TestCaseItem[];
  count: number;
}

export type TestRunStatus = "pending" | "running" | "completed" | "failed";

export interface TestRunCreated {
  run_id: string;
  status: TestRunStatus;
  total_cases: number;
  skill_slug: string;
  skill_version: string;
}

export interface TestRunSummary {
  run_id: string;
  status: TestRunStatus;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
}

export type TestRunCaseStatus =
  | "pending"
  | "running"
  | "passed"
  | "failed"
  | "error";

export interface TestRunCaseItem {
  case_id: string;
  name: string;
  user_input: string;
  status: TestRunCaseStatus;
  actual_output: string | null;
  judge_score: number | null;
  judge_reason: string | null;
  executed_at: string | null;
}

export interface TestRunCaseListResponse {
  items: TestRunCaseItem[];
  count: number;
}

// ── Audit types ──

export interface AuditEvent {
  id: string;
  tenant_id: string | null;
  actor_id: string | null;
  event_type: string;
  resource_type: string | null;
  resource_id: string | null;
  payload: Record<string, unknown>;
  occurred_at: string;
}

export interface AuditEventListResponse {
  items: AuditEvent[];
  count: number;
}

export interface ConversationSummary {
  conversation_id: string;
  tenant_id: string;
  employee_id: string;
  channel: string;
  channel_user_id: string;
  status: string;
  outcome: string | null;
  message_count: number;
  started_at: string | null;
  last_message_at: string | null;
  ended_at: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  count: number;
}

export interface ConversationMessage {
  id: string;
  seq: number;
  role: string;
  content: string;
  token_count: number | null;
  created_at: string | null;
}

export interface ConversationOutbound {
  id: string;
  message_id: string;
  channel: string;
  status: string;
  retry_count: number;
  error_message: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface ConversationDetail {
  conversation: ConversationSummary & { id: string };
  messages: ConversationMessage[];
  outbounds: ConversationOutbound[];
  audit_events: AuditEvent[];
}

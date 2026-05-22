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

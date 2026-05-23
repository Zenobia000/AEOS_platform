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

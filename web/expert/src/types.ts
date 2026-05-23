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

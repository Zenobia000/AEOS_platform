import { ApiError } from "./expert";
import { authHeader } from "../lib/authStore";
import type {
  AuditEventListResponse,
  ConversationDetail,
  ConversationListResponse,
} from "../types";

const BASE = "/api/v1/audit";

async function parseJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export async function listEvents(opts?: {
  tenantId?: string;
  eventType?: string;
  sinceHours?: number;
  limit?: number;
  signal?: AbortSignal;
}): Promise<AuditEventListResponse> {
  const params = new URLSearchParams();
  if (opts?.tenantId) params.set("tenant_id", opts.tenantId);
  if (opts?.eventType) params.set("event_type", opts.eventType);
  if (opts?.sinceHours) params.set("since_hours", String(opts.sinceHours));
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  const resp = await fetch(`${BASE}/events${qs ? `?${qs}` : ""}`, {
    headers: authHeader(),
    signal: opts?.signal,
  });
  return parseJson<AuditEventListResponse>(resp);
}

export async function listConversations(opts?: {
  tenantId?: string;
  limit?: number;
  signal?: AbortSignal;
}): Promise<ConversationListResponse> {
  const params = new URLSearchParams();
  if (opts?.tenantId) params.set("tenant_id", opts.tenantId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  const resp = await fetch(`${BASE}/conversations${qs ? `?${qs}` : ""}`, {
    headers: authHeader(),
    signal: opts?.signal,
  });
  return parseJson<ConversationListResponse>(resp);
}

export async function getConversation(
  conversationId: string,
  signal?: AbortSignal,
): Promise<ConversationDetail> {
  const resp = await fetch(`${BASE}/conversations/${conversationId}`, {
    headers: authHeader(),
    signal,
  });
  return parseJson<ConversationDetail>(resp);
}

import { authHeader } from "../lib/authStore";
import type { ActionResponse, ReviewListResponse } from "../types";

const BASE = "/api/v1/expert";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function parseJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail) detail = JSON.stringify(body.detail);
    } catch {
      // ignore parse errors; fall back to statusText
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export async function listReviews(opts?: {
  tenantId?: string;
  limit?: number;
  signal?: AbortSignal;
}): Promise<ReviewListResponse> {
  const params = new URLSearchParams();
  if (opts?.tenantId) params.set("tenant_id", opts.tenantId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  const url = `${BASE}/reviews${qs ? `?${qs}` : ""}`;
  return parseJson<ReviewListResponse>(
    await fetch(url, { signal: opts?.signal, headers: authHeader() }),
  );
}

export async function approveReview(
  outboundId: string,
  expertId: string,
): Promise<ActionResponse> {
  const resp = await fetch(`${BASE}/reviews/${outboundId}/approve`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify({ expert_id: expertId }),
  });
  return parseJson<ActionResponse>(resp);
}

export async function editReview(
  outboundId: string,
  expertId: string,
  newContent: string,
): Promise<ActionResponse> {
  const resp = await fetch(`${BASE}/reviews/${outboundId}/edit`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify({ expert_id: expertId, new_content: newContent }),
  });
  return parseJson<ActionResponse>(resp);
}

export async function rejectReview(
  outboundId: string,
  expertId: string,
  reason: string,
  handoffMessage?: string,
): Promise<ActionResponse> {
  const resp = await fetch(`${BASE}/reviews/${outboundId}/reject`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify({
      expert_id: expertId,
      reason,
      handoff_message: handoffMessage ?? null,
    }),
  });
  return parseJson<ActionResponse>(resp);
}

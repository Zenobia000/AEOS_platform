import { ApiError } from "./expert";
import type {
  KCActionResponse,
  KCCardType,
  KCListResponse,
} from "../types";

const BASE = "/api/v1/kc";

async function parseJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export async function listDrafts(opts?: {
  tenantId?: string;
  limit?: number;
  signal?: AbortSignal;
}): Promise<KCListResponse> {
  const params = new URLSearchParams();
  if (opts?.tenantId) params.set("tenant_id", opts.tenantId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  const url = `${BASE}/drafts${qs ? `?${qs}` : ""}`;
  return parseJson<KCListResponse>(await fetch(url, { signal: opts?.signal }));
}

export async function approveDraft(
  kcId: string,
  expertId: string,
): Promise<KCActionResponse> {
  const resp = await fetch(`${BASE}/drafts/${kcId}/approve`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ expert_id: expertId }),
  });
  return parseJson<KCActionResponse>(resp);
}

export interface EditDraftPayload {
  title?: string;
  body_markdown?: string;
  tags?: string[];
  card_type?: KCCardType;
}

export async function editDraft(
  kcId: string,
  expertId: string,
  payload: EditDraftPayload,
): Promise<KCActionResponse> {
  const resp = await fetch(`${BASE}/drafts/${kcId}/edit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ expert_id: expertId, ...payload }),
  });
  return parseJson<KCActionResponse>(resp);
}

export async function archiveDraft(
  kcId: string,
  expertId: string,
  reason: string,
): Promise<KCActionResponse> {
  const resp = await fetch(`${BASE}/drafts/${kcId}/archive`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ expert_id: expertId, reason }),
  });
  return parseJson<KCActionResponse>(resp);
}

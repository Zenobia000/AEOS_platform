import { ApiError } from "./expert";
import { authHeader } from "../lib/authStore";

const BASE = "/api/v1/admin";

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

export interface ExpertAccountItem {
  id: string;
  email: string;
  name: string;
  role: "expert" | "admin";
  tenant_id: string | null;
  enabled: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface ExpertListResponse {
  items: ExpertAccountItem[];
  count: number;
}

export async function listExperts(): Promise<ExpertListResponse> {
  const resp = await fetch(`${BASE}/experts`, { headers: authHeader() });
  return parseJson<ExpertListResponse>(resp);
}

export interface CreateExpertPayload {
  email: string;
  password: string;
  name: string;
  role?: "expert" | "admin";
  tenant_id?: string | null;
}

export async function createExpert(
  payload: CreateExpertPayload,
): Promise<ExpertAccountItem> {
  const resp = await fetch(`${BASE}/experts`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return parseJson<ExpertAccountItem>(resp);
}

export async function disableExpert(id: string): Promise<ExpertAccountItem> {
  const resp = await fetch(`${BASE}/experts/${id}/disable`, {
    method: "POST",
    headers: authHeader(),
  });
  return parseJson<ExpertAccountItem>(resp);
}

export async function enableExpert(id: string): Promise<ExpertAccountItem> {
  const resp = await fetch(`${BASE}/experts/${id}/enable`, {
    method: "POST",
    headers: authHeader(),
  });
  return parseJson<ExpertAccountItem>(resp);
}

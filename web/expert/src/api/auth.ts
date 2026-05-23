import { ApiError } from "./expert";
import { authHeader, type ExpertProfile } from "../lib/authStore";

const BASE = "/api/v1/auth";

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

export interface LoginResponse {
  token: string;
  expires_at: string;
  expert: ExpertProfile;
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const resp = await fetch(`${BASE}/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJson<LoginResponse>(resp);
}

export async function logout(): Promise<{ revoked: boolean }> {
  const resp = await fetch(`${BASE}/logout`, {
    method: "POST",
    headers: authHeader(),
  });
  return parseJson<{ revoked: boolean }>(resp);
}

export async function fetchMe(
  signal?: AbortSignal,
): Promise<ExpertProfile> {
  const resp = await fetch(`${BASE}/me`, {
    headers: authHeader(),
    signal,
  });
  return parseJson<ExpertProfile>(resp);
}

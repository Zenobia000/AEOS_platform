import { ApiError } from "./expert";
import { authHeader } from "../lib/authStore";
import type {
  TestCaseItem,
  TestCaseListResponse,
  TestRunCaseListResponse,
  TestRunCreated,
  TestRunSummary,
} from "../types";

const BASE = "/api/v1/testset";

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

export async function listCases(opts: {
  tenantId: string;
  enabledOnly?: boolean;
  skillSlug?: string;
  signal?: AbortSignal;
}): Promise<TestCaseListResponse> {
  const params = new URLSearchParams({ tenant_id: opts.tenantId });
  if (opts.enabledOnly !== undefined) {
    params.set("enabled_only", String(opts.enabledOnly));
  }
  if (opts.skillSlug && opts.skillSlug !== "_all_") {
    params.set("skill_slug", opts.skillSlug);
  }
  const resp = await fetch(`${BASE}/cases?${params.toString()}`, {
    signal: opts.signal,
    headers: authHeader(),
  });
  return parseJson<TestCaseListResponse>(resp);
}

export interface CreateCasePayload {
  tenant_id: string;
  name: string;
  user_input: string;
  expected_outcome: string;
  expected_keywords: string[];
  created_by?: string;
}

export async function createCase(
  payload: CreateCasePayload,
): Promise<TestCaseItem> {
  const resp = await fetch(`${BASE}/cases`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return parseJson<TestCaseItem>(resp);
}

export async function disableCase(caseId: string): Promise<TestCaseItem> {
  const resp = await fetch(`${BASE}/cases/${caseId}/disable`, {
    method: "POST",
    headers: authHeader(),
  });
  return parseJson<TestCaseItem>(resp);
}

export async function createRun(payload: {
  tenant_id: string;
  skill_slug: string;
  skill_version: string;
  created_by?: string;
}): Promise<TestRunCreated> {
  const resp = await fetch(`${BASE}/runs`, {
    method: "POST",
    headers: { "content-type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return parseJson<TestRunCreated>(resp);
}

export async function getRun(runId: string): Promise<TestRunSummary> {
  const resp = await fetch(`${BASE}/runs/${runId}`, { headers: authHeader() });
  return parseJson<TestRunSummary>(resp);
}

export async function getRunCases(
  runId: string,
): Promise<TestRunCaseListResponse> {
  const resp = await fetch(`${BASE}/runs/${runId}/cases`, {
    headers: authHeader(),
  });
  return parseJson<TestRunCaseListResponse>(resp);
}

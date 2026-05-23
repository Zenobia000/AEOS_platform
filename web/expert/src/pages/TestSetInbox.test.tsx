import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TestSetInbox } from "./TestSetInbox";
import type { TestCaseItem } from "../types";

function makeCase(overrides: Partial<TestCaseItem> = {}): TestCaseItem {
  return {
    case_id: "c-1",
    tenant_id: "t-1",
    name: "退貨期限",
    user_input: "退貨多久",
    expected_outcome: "7 天",
    expected_keywords: ["7 天", "發票"],
    enabled: true,
    created_by: "expert",
    created_at: "2026-05-22T10:00:00Z",
    ...overrides,
  };
}

function mockFetchByUrl(handlers: Record<string, () => unknown>) {
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : String(input);
    const key = Object.keys(handlers).find((prefix) => url.startsWith(prefix));
    const payload = key ? handlers[key]() : { items: [], count: 0 };
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => payload,
    } as unknown as Response;
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

const TENANT_ID = "11111111-1111-1111-1111-111111111111";

describe("TestSetInbox", () => {
  beforeEach(() => {
    try {
      window.localStorage.clear();
      window.localStorage.setItem("aeos.testset.tenant_id", TENANT_ID);
    } catch {
      /* ignore */
    }
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("loads cases on mount when tenant_id is set", async () => {
    mockFetchByUrl({
      "/api/v1/testset/cases": () => ({
        items: [makeCase()],
        count: 1,
      }),
    });
    render(<TestSetInbox expertId="ex-1" />);

    expect(await screen.findByText("退貨期限")).toBeInTheDocument();
    expect(screen.getByText(/Q: 退貨多久/)).toBeInTheDocument();
  });

  it("shows empty hint when no tenant id", async () => {
    try {
      window.localStorage.clear();
    } catch {
      /* ignore */
    }
    mockFetchByUrl({});
    render(<TestSetInbox expertId="ex-1" />);
    expect(
      await screen.findByText(/尚無 case|請填寫 tenant_id/),
    ).toBeInTheDocument();
  });

  it("creates case and refreshes", async () => {
    let cases: TestCaseItem[] = [];
    const fetchMock = mockFetchByUrl({
      "/api/v1/testset/cases?": () => ({ items: cases, count: cases.length }),
      "/api/v1/testset/cases": () => {
        const created = makeCase({ case_id: "c-new", name: "新題目" });
        cases = [created];
        return created;
      },
    });

    render(<TestSetInbox expertId="ex-1" />);
    await screen.findByText(/尚無 case/);

    await userEvent.type(
      screen.getByPlaceholderText(/名稱/),
      "新題目",
    );
    await userEvent.type(screen.getByPlaceholderText(/User input/), "問題");
    await userEvent.type(
      screen.getByPlaceholderText(/Expected outcome/),
      "答案",
    );
    await userEvent.type(
      screen.getByPlaceholderText(/Expected keywords/),
      "關鍵字, 另一個",
    );
    await userEvent.click(screen.getByRole("button", { name: "新增" }));

    await waitFor(() => {
      expect(screen.queryByText("新題目")).toBeInTheDocument();
    });

    // 第二個 fetch 應該是 POST /cases
    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    const postCall = calls.find(
      (c) =>
        String(c[0]).endsWith("/api/v1/testset/cases") && c[1]?.method === "POST",
    );
    expect(postCall).toBeTruthy();
    const body = JSON.parse(postCall![1].body as string);
    expect(body.expected_keywords).toEqual(["關鍵字", "另一個"]);
    expect(body.created_by).toBe("ex-1");
  });

  it("triggers a run and shows pass rate stat", async () => {
    const cases = [makeCase()];
    const runId = "r-1";
    mockFetchByUrl({
      "/api/v1/testset/cases?": () => ({ items: cases, count: 1 }),
      "/api/v1/testset/runs/r-1/cases": () => ({
        items: [
          {
            case_id: "c-1",
            name: "退貨期限",
            user_input: "退貨多久",
            status: "passed",
            actual_output: "7 天內",
            judge_score: 1.0,
            judge_reason: "all matched",
            executed_at: "2026-05-22T10:01:00Z",
          },
        ],
        count: 1,
      }),
      "/api/v1/testset/runs/r-1": () => ({
        run_id: runId,
        status: "completed",
        total_cases: 1,
        passed_cases: 1,
        failed_cases: 0,
        pass_rate: 1.0,
      }),
      "/api/v1/testset/runs": () => ({
        run_id: runId,
        status: "pending",
        total_cases: 1,
        skill_slug: "x",
        skill_version: "v",
      }),
    });

    render(<TestSetInbox expertId="ex-1" />);
    await screen.findByText("退貨期限");

    await userEvent.click(
      screen.getByRole("button", { name: /跑一次 test run/ }),
    );

    const passRate = await screen.findByText(/100.0%/);
    expect(passRate).toBeInTheDocument();
    const recentRun = passRate.closest("div")?.parentElement?.parentElement;
    expect(recentRun).toBeTruthy();
    if (recentRun) {
      expect(within(recentRun).getByText("completed")).toBeInTheDocument();
    }
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

function mockFetch(returnByUrl: Record<string, unknown>) {
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : String(input);
    const matched = Object.entries(returnByUrl).find(([prefix]) =>
      url.startsWith(prefix),
    );
    const payload = matched ? matched[1] : { items: [], count: 0 };
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

describe("App tab navigation", () => {
  beforeEach(() => {
    try {
      window.localStorage.clear();
    } catch {
      /* ignore */
    }
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("switches between drafts and KC tabs and fetches correct endpoint", async () => {
    const fetchMock = mockFetch({
      "/api/v1/expert/reviews": { items: [], count: 0 },
      "/api/v1/kc/drafts": { items: [], count: 0 },
    });

    render(<App />);

    // 初始 = drafts tab → 應該呼叫 /api/v1/expert/reviews
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]));
      expect(calls.some((u) => u.startsWith("/api/v1/expert/reviews"))).toBe(true);
    });

    await userEvent.click(screen.getByRole("tab", { name: /KC 知識卡/ }));

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]));
      expect(calls.some((u) => u.startsWith("/api/v1/kc/drafts"))).toBe(true);
    });

    expect(
      screen.getByText(/目前沒有待審的 KC draft/),
    ).toBeInTheDocument();
  });
});

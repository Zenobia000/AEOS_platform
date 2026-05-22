import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import type { ReviewItem } from "./types";

function makeItem(overrides: Partial<ReviewItem> = {}): ReviewItem {
  return {
    outbound_id: "out-1",
    conversation_id: "conv-1",
    channel: "line",
    channel_user_id: "U-abc",
    message_id: "msg-1",
    draft_text: "您好，本店退貨期限為 7 天",
    created_at: "2026-05-22T10:00:00Z",
    ...overrides,
  };
}

interface FakeResponse {
  ok?: boolean;
  status?: number;
  statusText?: string;
  json: unknown;
}

function mockFetchSequence(responses: FakeResponse[]) {
  let call = 0;
  const fn = vi.fn(async () => {
    const r = responses[call] ?? responses[responses.length - 1];
    call += 1;
    return {
      ok: r.ok ?? true,
      status: r.status ?? 200,
      statusText: r.statusText ?? "OK",
      json: async () => r.json,
    } as unknown as Response;
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("Expert Console App", () => {
  beforeEach(() => {
    try {
      window.localStorage.clear();
    } catch {
      /* not available in this env */
    }
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("loads draft list on mount and renders cards", async () => {
    mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
    ]);

    render(<App />);

    expect(await screen.findByText(/AEOS Expert Console/)).toBeInTheDocument();
    expect(
      await screen.findByText(/您好，本店退貨期限為 7 天/),
    ).toBeInTheDocument();
  });

  it("shows empty state when API returns no items", async () => {
    mockFetchSequence([{ json: { items: [], count: 0 } }]);
    render(<App />);
    expect(
      await screen.findByText(/目前沒有待審的 draft/),
    ).toBeInTheDocument();
  });

  it("shows error message when API fails", async () => {
    mockFetchSequence([
      {
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: { detail: "boom" },
      },
    ]);
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("boom");
  });

  it("approve removes the card and POSTs with expert_id", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      {
        json: {
          outbound_id: "out-1",
          action: "approved",
          new_status: "pending",
        },
      },
    ]);

    render(<App />);
    const card = await screen.findByTestId("review-card-out-1");
    await userEvent.click(within(card).getByRole("button", { name: /同意送出/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("review-card-out-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/expert/reviews/out-1/approve");
    expect(calls[1][1].method).toBe("POST");
    expect(JSON.parse(calls[1][1].body as string)).toEqual({
      expert_id: "expert-local",
    });
  });

  it("edit flow sends new_content", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      { json: { outbound_id: "out-1", action: "edited", new_status: "pending" } },
    ]);

    render(<App />);
    const card = await screen.findByTestId("review-card-out-1");
    await userEvent.click(within(card).getByRole("button", { name: /編輯後送出/ }));

    const textarea = within(card).getByLabelText("編輯後的回覆內容");
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "改過的回覆");
    await userEvent.click(within(card).getByRole("button", { name: /送出編輯版/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("review-card-out-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/expert/reviews/out-1/edit");
    const body = JSON.parse(calls[1][1].body as string);
    expect(body.new_content).toBe("改過的回覆");
    expect(body.expert_id).toBe("expert-local");
  });

  it("reject flow sends reason + handoff_message", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      {
        json: {
          outbound_id: "out-1",
          action: "rejected",
          new_status: "rejected",
          handoff_id: "h-1",
        },
      },
    ]);

    render(<App />);
    const card = await screen.findByTestId("review-card-out-1");
    await userEvent.click(within(card).getByRole("button", { name: /拒絕並轉接/ }));

    await userEvent.type(
      within(card).getByLabelText("拒絕原因"),
      "AI 答錯",
    );
    await userEvent.type(
      within(card).getByLabelText("轉接訊息"),
      "請接手",
    );
    await userEvent.click(
      within(card).getByRole("button", { name: /確認拒絕並建立 handoff/ }),
    );

    await waitFor(() => {
      expect(screen.queryByTestId("review-card-out-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/expert/reviews/out-1/reject");
    const body = JSON.parse(calls[1][1].body as string);
    expect(body.reason).toBe("AI 答錯");
    expect(body.handoff_message).toBe("請接手");
  });

  it("expert_id input persists to localStorage", async () => {
    mockFetchSequence([{ json: { items: [], count: 0 } }]);
    render(<App />);

    const input = await screen.findByLabelText("Expert ID");
    await userEvent.clear(input);
    await userEvent.type(input, "expert-sunny");

    expect(window.localStorage.getItem("aeos.expert_id")).toBe("expert-sunny");
  });
});

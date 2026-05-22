import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KCInbox } from "./KCInbox";
import type { KCDraftItem } from "../types";

function makeItem(overrides: Partial<KCDraftItem> = {}): KCDraftItem {
  return {
    kc_id: "kc-1",
    tenant_id: "t-1",
    card_type: "policy",
    title: "退貨政策",
    body_markdown: "本店退貨期限為到貨後 7 天",
    tags: ["退貨"],
    source_url: null,
    source_file_ref: null,
    created_at: "2026-05-22T10:00:00Z",
    ...overrides,
  };
}

function mockFetchSequence(
  responses: Array<{ ok?: boolean; status?: number; json: unknown }>,
) {
  let call = 0;
  const fn = vi.fn(async () => {
    const r = responses[call] ?? responses[responses.length - 1];
    call += 1;
    return {
      ok: r.ok ?? true,
      status: r.status ?? 200,
      statusText: "OK",
      json: async () => r.json,
    } as unknown as Response;
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("KCInbox", () => {
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

  it("loads drafts and renders KC cards", async () => {
    mockFetchSequence([{ json: { items: [makeItem()], count: 1 } }]);
    render(<KCInbox expertId="ex-1" />);

    expect(await screen.findByText("退貨政策")).toBeInTheDocument();
    expect(screen.getByText("policy")).toBeInTheDocument();
  });

  it("approve POSTs to /approve and removes card", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      { json: { kc_id: "kc-1", action: "approved", new_status: "approved" } },
    ]);

    render(<KCInbox expertId="ex-1" />);
    const card = await screen.findByTestId("kc-card-kc-1");
    await userEvent.click(within(card).getByRole("button", { name: /同意收錄/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("kc-card-kc-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/kc/drafts/kc-1/approve");
    expect(JSON.parse(calls[1][1].body as string)).toEqual({ expert_id: "ex-1" });
  });

  it("edit sends only changed fields", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      { json: { kc_id: "kc-1", action: "edited", new_status: "approved" } },
    ]);

    render(<KCInbox expertId="ex-1" />);
    const card = await screen.findByTestId("kc-card-kc-1");
    await userEvent.click(within(card).getByRole("button", { name: /編輯後收錄/ }));

    const titleInput = within(card).getByLabelText("標題");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "退貨政策修訂");
    await userEvent.click(within(card).getByRole("button", { name: /送出編輯版/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("kc-card-kc-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/kc/drafts/kc-1/edit");
    const body = JSON.parse(calls[1][1].body as string);
    expect(body.title).toBe("退貨政策修訂");
    expect(body.body_markdown).toBeUndefined();
    expect(body.expert_id).toBe("ex-1");
  });

  it("edit changes card_type via select", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      { json: { kc_id: "kc-1", action: "edited", new_status: "approved" } },
    ]);

    render(<KCInbox expertId="ex-1" />);
    const card = await screen.findByTestId("kc-card-kc-1");
    await userEvent.click(within(card).getByRole("button", { name: /編輯後收錄/ }));

    await userEvent.selectOptions(within(card).getByLabelText("類別"), "faq");
    await userEvent.click(within(card).getByRole("button", { name: /送出編輯版/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("kc-card-kc-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    const body = JSON.parse(calls[1][1].body as string);
    expect(body.card_type).toBe("faq");
  });

  it("archive sends reason", async () => {
    const fetchMock = mockFetchSequence([
      { json: { items: [makeItem()], count: 1 } },
      { json: { kc_id: "kc-1", action: "archived", new_status: "archived" } },
    ]);

    render(<KCInbox expertId="ex-1" />);
    const card = await screen.findByTestId("kc-card-kc-1");
    await userEvent.click(within(card).getByRole("button", { name: /封存/ }));

    await userEvent.type(within(card).getByLabelText("封存原因"), "重複內容");
    await userEvent.click(
      within(card).getByRole("button", { name: /確認封存/ }),
    );

    await waitFor(() => {
      expect(screen.queryByTestId("kc-card-kc-1")).not.toBeInTheDocument();
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    expect(calls[1][0]).toBe("/api/v1/kc/drafts/kc-1/archive");
    const body = JSON.parse(calls[1][1].body as string);
    expect(body.reason).toBe("重複內容");
  });

  it("shows error on 409", async () => {
    mockFetchSequence([
      {
        ok: false,
        status: 409,
        json: { detail: "knowledge_card kc-1 not in draft" },
      },
    ]);
    render(<KCInbox expertId="ex-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("not in draft");
  });
});

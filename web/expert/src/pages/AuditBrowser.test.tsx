import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuditBrowser } from "./AuditBrowser";

interface FakeResponse {
  ok?: boolean;
  status?: number;
  json: unknown;
}

function mockFetchByUrl(handlers: Record<string, () => FakeResponse>) {
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : String(input);
    const key = Object.keys(handlers).find((prefix) => url.startsWith(prefix));
    const r = key
      ? handlers[key]()
      : { ok: true, status: 200, json: { items: [], count: 0 } };
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

describe("AuditBrowser", () => {
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

  it("default loads conversation list", async () => {
    mockFetchByUrl({
      "/api/v1/audit/conversations": () => ({
        json: {
          items: [
            {
              conversation_id: "c-1",
              tenant_id: "t-1",
              employee_id: "e-1",
              channel: "line",
              channel_user_id: "U-abc",
              status: "active",
              outcome: null,
              message_count: 3,
              started_at: "2026-05-22T10:00:00Z",
              last_message_at: "2026-05-22T10:05:00Z",
              ended_at: null,
            },
          ],
          count: 1,
        },
      }),
    });
    render(<AuditBrowser />);
    expect(await screen.findByText("U-abc")).toBeInTheDocument();
    expect(screen.getByText(/3 msgs/)).toBeInTheDocument();
  });

  it("switches to events tab and shows filter input", async () => {
    mockFetchByUrl({
      "/api/v1/audit/events": () => ({
        json: {
          items: [
            {
              id: "a-1",
              tenant_id: "t-1",
              actor_id: "expert-amy",
              event_type: "expert.draft_approved",
              resource_type: "outbound_message",
              resource_id: "out-1",
              payload: { channel: "line" },
              occurred_at: "2026-05-23T08:00:00Z",
            },
          ],
          count: 1,
        },
      }),
      "/api/v1/audit/conversations": () => ({ json: { items: [], count: 0 } }),
    });

    render(<AuditBrowser />);
    await userEvent.click(screen.getByRole("button", { name: /Audit 事件/ }));

    expect(await screen.findByText("expert.draft_approved")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/event_type filter/)).toBeInTheDocument();
  });

  it("clicking conversation row opens detail view", async () => {
    let detailFetched = false;
    const fn = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.startsWith("/api/v1/audit/conversations/c-1")) {
        detailFetched = true;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            conversation: {
              id: "c-1",
              conversation_id: "c-1",
              tenant_id: "t",
              employee_id: "e",
              channel: "line",
              channel_user_id: "U-x",
              status: "active",
              outcome: null,
              message_count: 2,
              started_at: null,
              last_message_at: null,
              ended_at: null,
            },
            messages: [
              {
                id: "m-1",
                seq: 1,
                role: "user",
                content: "退貨多久",
                token_count: null,
                tool_invocations: [],
                created_at: null,
              },
              {
                id: "m-2",
                seq: 2,
                role: "assistant",
                content: "7 天",
                token_count: 5,
                tool_invocations: [],
                created_at: null,
              },
            ],
            outbounds: [],
            audit_events: [
              {
                id: "a-1",
                tenant_id: "t",
                actor_id: "outbound_worker",
                event_type: "channel.message_pushed",
                resource_type: "outbound_message",
                resource_id: "o-1",
                payload: {},
                occurred_at: "2026-05-23T08:00:00Z",
              },
            ],
          }),
        } as unknown as Response;
      }
      if (url.startsWith("/api/v1/audit/conversations")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            items: [
              {
                conversation_id: "c-1",
                tenant_id: "t",
                employee_id: "e",
                channel: "line",
                channel_user_id: "U-x",
                status: "active",
                outcome: null,
                message_count: 2,
                started_at: null,
                last_message_at: "2026-05-23T08:00:00Z",
                ended_at: null,
              },
            ],
            count: 1,
          }),
        } as unknown as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ items: [], count: 0 }),
      } as unknown as Response;
    });
    vi.stubGlobal("fetch", fn);

    render(<AuditBrowser />);
    await userEvent.click(await screen.findByTestId("conv-row-c-1"));

    await waitFor(() => {
      expect(screen.queryByTestId("conversation-detail")).toBeInTheDocument();
    });
    expect(detailFetched).toBe(true);
    expect(screen.getByText("退貨多久")).toBeInTheDocument();
    expect(screen.getByText("7 天")).toBeInTheDocument();
    expect(screen.getByText("channel.message_pushed")).toBeInTheDocument();
  });

  it("shows error on 401", async () => {
    mockFetchByUrl({
      "/api/v1/audit/conversations": () => ({
        ok: false,
        status: 401,
        json: { detail: "missing Bearer token" },
      }),
    });
    render(<AuditBrowser />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "missing Bearer token",
    );
  });
});

describe("AuditBrowser tool_invocations", () => {
  beforeEach(() => {
    try { window.localStorage.clear(); } catch { /* ignore */ }
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders KC refs in assistant message detail", async () => {
    const fn = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.startsWith("/api/v1/audit/conversations/c-tool")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            conversation: {
              id: "c-tool",
              conversation_id: "c-tool",
              tenant_id: "t",
              employee_id: "e",
              channel: "line",
              channel_user_id: "U",
              status: "active",
              outcome: null,
              message_count: 1,
              started_at: null,
              last_message_at: null,
              ended_at: null,
            },
            messages: [
              {
                id: "m-assistant",
                seq: 1,
                role: "assistant",
                content: "您好，退貨可於 7 天內",
                token_count: 20,
                tool_invocations: [
                  {
                    name: "search_knowledge",
                    input: { query: "退貨多久", top_k: 5 },
                    ok: true,
                    kc_refs: [
                      "11111111-aaaa-bbbb-cccc-111111111111",
                      "22222222-aaaa-bbbb-cccc-222222222222",
                    ],
                  },
                ],
                created_at: null,
              },
            ],
            outbounds: [],
            audit_events: [],
          }),
        } as unknown as Response;
      }
      if (url.startsWith("/api/v1/audit/conversations")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            items: [
              {
                conversation_id: "c-tool",
                tenant_id: "t",
                employee_id: "e",
                channel: "line",
                channel_user_id: "U",
                status: "active",
                outcome: null,
                message_count: 1,
                started_at: null,
                last_message_at: "2026-05-24T10:00:00Z",
                ended_at: null,
              },
            ],
            count: 1,
          }),
        } as unknown as Response;
      }
      return { ok: true, status: 200, json: async () => ({ items: [], count: 0 }) } as unknown as Response;
    });
    vi.stubGlobal("fetch", fn);

    render(<AuditBrowser />);
    await userEvent.click(await screen.findByTestId("conv-row-c-tool"));

    const toolList = await screen.findByTestId("tool-invocations-m-assistant");
    expect(toolList).toHaveTextContent("search_knowledge");
    expect(toolList).toHaveTextContent("引用 2 張 KC");
    expect(toolList).toHaveTextContent("11111111");
    expect(toolList).toHaveTextContent("22222222");
  });
});

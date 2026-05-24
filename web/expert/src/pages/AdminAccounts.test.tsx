import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminAccounts } from "./AdminAccounts";

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

const ACCOUNT = {
  id: "e-1",
  email: "amy@aeos",
  name: "Amy",
  role: "expert" as const,
  tenant_id: null,
  enabled: true,
  last_login_at: "2026-05-24T08:00:00Z",
  created_at: "2026-05-20T00:00:00Z",
};

describe("AdminAccounts", () => {
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

  it("loads + renders expert list on mount", async () => {
    mockFetchByUrl({
      "/api/v1/admin/experts": () => ({
        json: { items: [ACCOUNT], count: 1 },
      }),
    });
    render(<AdminAccounts />);
    expect(await screen.findByText("Amy")).toBeInTheDocument();
    expect(screen.getByText("amy@aeos")).toBeInTheDocument();
    expect(screen.getByText("expert")).toBeInTheDocument();
  });

  it("shows create form when click 新增帳號", async () => {
    mockFetchByUrl({
      "/api/v1/admin/experts": () => ({
        json: { items: [], count: 0 },
      }),
    });
    render(<AdminAccounts />);
    await screen.findByText(/尚無帳號|載入中/);
    await userEvent.click(screen.getByRole("button", { name: /新增帳號/ }));
    expect(screen.getByPlaceholderText("Email")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("姓名")).toBeInTheDocument();
  });

  it("creates account via POST + refreshes", async () => {
    let listCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.startsWith("/api/v1/admin/experts") && init?.method === "POST") {
        return {
          ok: true,
          status: 200,
          statusText: "OK",
          json: async () => ({ ...ACCOUNT, id: "e-new", email: "new@aeos" }),
        } as unknown as Response;
      }
      if (url.startsWith("/api/v1/admin/experts")) {
        listCalls += 1;
        const items = listCalls === 1 ? [] : [{ ...ACCOUNT, id: "e-new", email: "new@aeos" }];
        return {
          ok: true,
          status: 200,
          statusText: "OK",
          json: async () => ({ items, count: items.length }),
        } as unknown as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      } as unknown as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminAccounts />);
    await screen.findByText(/尚無帳號/);
    await userEvent.click(screen.getByRole("button", { name: /新增帳號/ }));

    await userEvent.type(screen.getByPlaceholderText("Email"), "new@aeos");
    await userEvent.type(screen.getByPlaceholderText("姓名"), "New");
    await userEvent.type(screen.getByPlaceholderText(/密碼/), "secret123");
    await userEvent.click(screen.getByRole("button", { name: /建立$/ }));

    await waitFor(() => {
      expect(screen.queryByText("new@aeos")).toBeInTheDocument();
    });

    const postCall = (fetchMock.mock.calls as unknown as Array<[string, RequestInit]>).find(
      (c) => c[0].endsWith("/api/v1/admin/experts") && c[1]?.method === "POST",
    );
    expect(postCall).toBeTruthy();
    const body = JSON.parse(postCall![1].body as string);
    expect(body.email).toBe("new@aeos");
    expect(body.name).toBe("New");
    expect(body.role).toBe("expert");
  });

  it("disable / enable toggles role state", async () => {
    let toggled = false;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.includes("/disable")) {
        toggled = true;
        return {
          ok: true,
          status: 200,
          statusText: "OK",
          json: async () => ({ ...ACCOUNT, enabled: false }),
        } as unknown as Response;
      }
      const items = toggled ? [{ ...ACCOUNT, enabled: false }] : [ACCOUNT];
      return {
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => ({ items, count: items.length }),
      } as unknown as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminAccounts />);
    await screen.findByText("Amy");
    await userEvent.click(screen.getByRole("button", { name: /停用/ }));

    await waitFor(() => {
      expect(screen.queryByText("disabled")).toBeInTheDocument();
    });
  });

  it("shows error on 403", async () => {
    mockFetchByUrl({
      "/api/v1/admin/experts": () => ({
        ok: false,
        status: 403,
        json: { detail: "admin role required" },
      }),
    });
    render(<AdminAccounts />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "admin role required",
    );
  });
});

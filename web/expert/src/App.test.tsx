import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

interface FakeResponse {
  ok?: boolean;
  status?: number;
  json: unknown;
}

function mockFetchByUrl(handlers: Record<string, () => FakeResponse>) {
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : String(input);
    const key = Object.keys(handlers).find((prefix) => url.startsWith(prefix));
    const r = key ? handlers[key]() : { ok: true, status: 200, json: { items: [], count: 0 } };
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

const EXPERT_OK = {
  id: "ex-1",
  email: "amy@example.com",
  name: "Amy",
  role: "expert",
  tenant_id: null,
};

describe("App — auth gate", () => {
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

  it("shows Login form when /auth/me returns 401", async () => {
    mockFetchByUrl({
      "/api/v1/auth/me": () => ({
        ok: false,
        status: 401,
        json: { detail: "missing Bearer token" },
      }),
    });
    render(<App />);
    expect(
      await screen.findByRole("form", { name: /login/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("shows tabs when /auth/me returns expert", async () => {
    mockFetchByUrl({
      "/api/v1/auth/me": () => ({ json: EXPERT_OK }),
      "/api/v1/expert/reviews": () => ({ json: { items: [], count: 0 } }),
    });
    render(<App />);
    expect(
      await screen.findByRole("tab", { name: /訊息草稿/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /KC 知識卡/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Test Set/ })).toBeInTheDocument();
    expect(screen.getByText("Amy")).toBeInTheDocument();
  });

  it("login error 401 shows alert and stays on form", async () => {
    mockFetchByUrl({
      "/api/v1/auth/me": () => ({
        ok: false,
        status: 401,
        json: { detail: "401" },
      }),
      "/api/v1/auth/login": () => ({
        ok: false,
        status: 401,
        json: { detail: "invalid credentials" },
      }),
    });
    render(<App />);
    await screen.findByRole("form", { name: /login/i });
    await userEvent.type(screen.getByLabelText("Email"), "x@y.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /登入/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "invalid credentials",
    );
    expect(screen.getByRole("form", { name: /login/i })).toBeInTheDocument();
  });

  it("login success → switches to authenticated app + stores token", async () => {
    let loggedIn = false;
    const fn = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.startsWith("/api/v1/auth/login")) {
        loggedIn = true;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            token: "tok-success",
            expires_at: "2026-06-22T00:00:00Z",
            expert: EXPERT_OK,
          }),
        } as unknown as Response;
      }
      if (url.startsWith("/api/v1/auth/me")) {
        return loggedIn
          ? ({
              ok: true,
              status: 200,
              json: async () => EXPERT_OK,
            } as unknown as Response)
          : ({
              ok: false,
              status: 401,
              json: async () => ({ detail: "401" }),
            } as unknown as Response);
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ items: [], count: 0 }),
      } as unknown as Response;
    });
    vi.stubGlobal("fetch", fn);

    render(<App />);
    await screen.findByRole("form", { name: /login/i });
    await userEvent.type(screen.getByLabelText("Email"), "amy@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "secret");
    await userEvent.click(screen.getByRole("button", { name: /登入/ }));

    await waitFor(() => {
      expect(
        screen.queryByRole("form", { name: /login/i }),
      ).not.toBeInTheDocument();
    });
    expect(window.localStorage.getItem("aeos.expert_token")).toBe(
      "tok-success",
    );
  });

  it("logout clears token and returns to Login", async () => {
    let loggedIn = true;
    const fn = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : String(input);
      if (url.startsWith("/api/v1/auth/me")) {
        return loggedIn
          ? ({
              ok: true,
              status: 200,
              json: async () => EXPERT_OK,
            } as unknown as Response)
          : ({
              ok: false,
              status: 401,
              json: async () => ({ detail: "401" }),
            } as unknown as Response);
      }
      if (url.startsWith("/api/v1/auth/logout")) {
        loggedIn = false;
        return {
          ok: true,
          status: 200,
          json: async () => ({ revoked: true }),
        } as unknown as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ items: [], count: 0 }),
      } as unknown as Response;
    });
    vi.stubGlobal("fetch", fn);
    window.localStorage.setItem("aeos.expert_token", "pre-set-token");

    render(<App />);
    await screen.findByText("Amy");
    await userEvent.click(screen.getByRole("button", { name: /登出/ }));

    await waitFor(() => {
      expect(screen.queryByText("Amy")).not.toBeInTheDocument();
    });
    expect(window.localStorage.getItem("aeos.expert_token")).toBeNull();
  });

  it("tab switching fires correct endpoints", async () => {
    const fetchMock = mockFetchByUrl({
      "/api/v1/auth/me": () => ({ json: EXPERT_OK }),
      "/api/v1/expert/reviews": () => ({ json: { items: [], count: 0 } }),
      "/api/v1/kc/drafts": () => ({ json: { items: [], count: 0 } }),
    });

    render(<App />);
    await screen.findByText("Amy");

    await userEvent.click(screen.getByRole("tab", { name: /KC 知識卡/ }));

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]));
      expect(calls.some((u) => u.startsWith("/api/v1/kc/drafts"))).toBe(true);
    });
  });
});

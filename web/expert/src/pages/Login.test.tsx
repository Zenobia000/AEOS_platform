import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Login } from "./Login";

function mockFetch(handler: (body: unknown) => { ok: boolean; status: number; json: unknown }) {
  const fn = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
    const body = init?.body ? JSON.parse(init.body as string) : null;
    const r = handler(body);
    return {
      ok: r.ok,
      status: r.status,
      statusText: "OK",
      json: async () => r.json,
    } as unknown as Response;
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("Login", () => {
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

  it("disables submit until email + password filled", async () => {
    mockFetch(() => ({ ok: true, status: 200, json: {} }));
    render(<Login />);
    const submit = screen.getByRole("button", { name: /登入/ });
    expect(submit).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Email"), "x@y.com");
    expect(submit).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Password"), "pw");
    expect(submit).toBeEnabled();
  });

  it("stores token on success + calls onLoggedIn", async () => {
    const fetchMock = mockFetch(() => ({
      ok: true,
      status: 200,
      json: {
        token: "tok-xyz",
        expires_at: "2026-06-22T00:00:00Z",
        expert: {
          id: "e-1",
          email: "amy@example.com",
          name: "Amy",
          role: "expert",
          tenant_id: null,
        },
      },
    }));
    const cb = vi.fn();
    render(<Login onLoggedIn={cb} />);

    await userEvent.type(screen.getByLabelText("Email"), "amy@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "secret");
    await userEvent.click(screen.getByRole("button", { name: /登入/ }));

    await waitFor(() => {
      expect(cb).toHaveBeenCalled();
    });
    expect(window.localStorage.getItem("aeos.expert_token")).toBe("tok-xyz");

    // 確認 fetch 帶了正確 body
    const call = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(call[0]).toBe("/api/v1/auth/login");
    expect(JSON.parse(call[1].body as string)).toEqual({
      email: "amy@example.com",
      password: "secret",
    });
  });

  it("shows error message on 401", async () => {
    mockFetch(() => ({
      ok: false,
      status: 401,
      json: { detail: "invalid credentials" },
    }));
    const cb = vi.fn();
    render(<Login onLoggedIn={cb} />);

    await userEvent.type(screen.getByLabelText("Email"), "amy@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /登入/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "invalid credentials",
    );
    expect(cb).not.toHaveBeenCalled();
    expect(window.localStorage.getItem("aeos.expert_token")).toBeNull();
  });
});

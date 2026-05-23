import { useState } from "react";
import { ApiError } from "../api/expert";
import { login } from "../api/auth";
import { setSession } from "../lib/authStore";
import { Button } from "../components/Button";

interface Props {
  /** 由 App.tsx 注入；登入成功後重新讀 /auth/me。 */
  onLoggedIn?: () => void;
}

export function Login({ onLoggedIn }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setBusy(true);
    setError(null);
    try {
      const resp = await login(email.trim(), password);
      setSession(resp.token, resp.expert);
      onLoggedIn?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold">AEOS Expert Console</h1>
        <p className="mb-5 text-sm text-slate-500">請使用 expert 帳號登入</p>

        <form onSubmit={submit} className="space-y-3" aria-label="login form">
          <div>
            <label
              htmlFor="login-email"
              className="mb-1 block text-xs text-slate-600"
            >
              Email
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="mb-1 block text-xs text-slate-600"
            >
              Password
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {error && (
            <div
              role="alert"
              className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={busy || !email.trim() || !password}
            className="w-full justify-center"
          >
            {busy ? "登入中…" : "登入"}
          </Button>
        </form>

        <p className="mt-4 text-xs text-slate-400">
          帳號管理 Phase 1 由 CTO 透過 CLI 建立；忘記密碼請聯絡管理員。
        </p>
      </div>
    </div>
  );
}

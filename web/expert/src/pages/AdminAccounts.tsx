import { useCallback, useEffect, useState } from "react";
import {
  createExpert,
  disableExpert,
  enableExpert,
  listExperts,
  type ExpertAccountItem,
} from "../api/admin";
import { ApiError } from "../api/expert";
import { Button } from "../components/Button";

export function AdminAccounts() {
  const [items, setItems] = useState<ExpertAccountItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // create form state
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"expert" | "admin">("expert");
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listExperts();
      setItems(resp.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitCreate = async () => {
    if (!email.trim() || !name.trim() || password.length < 6) {
      setError("email / name 必填，password ≥ 6 字");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      await createExpert({ email, name, password, role });
      setEmail("");
      setName("");
      setPassword("");
      setRole("expert");
      setShowCreate(false);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setCreating(false);
    }
  };

  const toggle = async (account: ExpertAccountItem) => {
    setError(null);
    try {
      if (account.enabled) {
        await disableExpert(account.id);
      } else {
        await enableExpert(account.id);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    }
  };

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-700">
          Expert 帳號（{items.length}）
        </h2>
        <div className="flex gap-2">
          <Button onClick={() => void refresh()} disabled={loading} variant="ghost">
            ↻ 重新整理
          </Button>
          <Button
            onClick={() => setShowCreate((v) => !v)}
            variant={showCreate ? "ghost" : "primary"}
          >
            {showCreate ? "取消" : "+ 新增帳號"}
          </Button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {showCreate && (
        <div className="mb-4 rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold">新增 Expert 帳號</h3>
          <div className="space-y-2">
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              type="email"
              autoComplete="off"
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="姓名"
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="密碼（≥ 6 字）"
              type="password"
              autoComplete="new-password"
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as "expert" | "admin")}
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="expert">expert</option>
              <option value="admin">admin</option>
            </select>
            <Button onClick={() => void submitCreate()} disabled={creating}>
              {creating ? "建立中…" : "建立"}
            </Button>
          </div>
        </div>
      )}

      {loading && items.length === 0 ? (
        <p className="text-sm text-slate-500">載入中…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-500">尚無帳號。</p>
      ) : (
        <ul className="space-y-2">
          {items.map((a) => (
            <li
              key={a.id}
              className="rounded-md border border-slate-200 bg-white p-3"
              data-testid={`expert-row-${a.id}`}
            >
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="font-medium">{a.name}</span>
                  <span className="ml-2 text-xs text-slate-500">{a.email}</span>
                  <span
                    className={`ml-2 rounded px-1.5 py-0.5 text-xs ${
                      a.role === "admin"
                        ? "bg-brand-50 text-brand-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {a.role}
                  </span>
                  {!a.enabled && (
                    <span className="ml-2 rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
                      disabled
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <time className="text-xs text-slate-400">
                    {a.last_login_at
                      ? `last login ${new Date(a.last_login_at).toLocaleDateString()}`
                      : "未登入"}
                  </time>
                  <Button
                    onClick={() => void toggle(a)}
                    variant={a.enabled ? "danger" : "secondary"}
                  >
                    {a.enabled ? "停用" : "啟用"}
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

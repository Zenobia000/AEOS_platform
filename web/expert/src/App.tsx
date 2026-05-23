import { useCallback, useEffect, useState } from "react";
import { DraftsInbox } from "./pages/DraftsInbox";
import { KCInbox } from "./pages/KCInbox";
import { TestSetInbox } from "./pages/TestSetInbox";
import { Login } from "./pages/Login";
import { fetchMe, logout as apiLogout } from "./api/auth";
import { ApiError } from "./api/expert";
import {
  clearSession,
  getStoredExpert,
  getToken,
  type ExpertProfile,
} from "./lib/authStore";
import { Button } from "./components/Button";
import { cn } from "./lib/cn";

type Tab = "drafts" | "kc" | "testset";

type AuthState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated"; expert: ExpertProfile };

export default function App() {
  const [tab, setTab] = useState<Tab>("drafts");
  const [auth, setAuth] = useState<AuthState>({ kind: "loading" });

  const refreshAuth = useCallback(async (signal?: AbortSignal) => {
    try {
      const me = await fetchMe(signal);
      setAuth({ kind: "authenticated", expert: me });
    } catch (err) {
      if (signal?.aborted) return;
      if (err instanceof ApiError && err.status === 401) {
        // 401 → token 過期 / 偽造 / bypass 關閉。清掉本地 token 但不 notify
        // （避免觸發 subscribe loop）
        if (getToken()) {
          clearSession();
        }
        setAuth({ kind: "anonymous" });
        return;
      }
      // 其他錯誤（network 等）— 退回 stored expert，否則 anonymous
      const stored = getStoredExpert();
      setAuth(
        stored
          ? { kind: "authenticated", expert: stored }
          : { kind: "anonymous" },
      );
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void refreshAuth(ctrl.signal);
    return () => ctrl.abort();
  }, [refreshAuth]);

  if (auth.kind === "loading") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-sm text-slate-500">
        載入中…
      </div>
    );
  }

  if (auth.kind === "anonymous") {
    return <Login onLoggedIn={() => void refreshAuth()} />;
  }

  return (
    <AuthenticatedApp
      expert={auth.expert}
      tab={tab}
      setTab={setTab}
      onLogout={() => setAuth({ kind: "anonymous" })}
    />
  );
}

interface AuthedProps {
  expert: ExpertProfile;
  tab: Tab;
  setTab: (t: Tab) => void;
  onLogout: () => void;
}

function AuthenticatedApp({ expert, tab, setTab, onLogout }: AuthedProps) {
  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      /* swallow — 即使 revoke 失敗也清本地 */
    }
    clearSession();
    onLogout();
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <header className="mb-4">
        <div className="flex items-baseline justify-between">
          <div>
            <h1 className="text-xl font-semibold">AEOS Expert Console</h1>
            <p className="text-sm text-slate-500">
              Draft Mode + KC + TestSet 審查介面
            </p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">
              <span className="text-xs text-slate-400">登入為</span>{" "}
              <span className="font-medium">{expert.name}</span>{" "}
              <span className="text-xs text-slate-400">({expert.role})</span>
            </span>
            <Button onClick={() => void handleLogout()} variant="ghost">
              登出
            </Button>
          </div>
        </div>
      </header>

      <nav className="mb-4 flex gap-1 border-b border-slate-200" role="tablist">
        <TabButton current={tab} value="drafts" onClick={setTab}>
          訊息草稿
        </TabButton>
        <TabButton current={tab} value="kc" onClick={setTab}>
          KC 知識卡
        </TabButton>
        <TabButton current={tab} value="testset" onClick={setTab}>
          Test Set
        </TabButton>
      </nav>

      {tab === "drafts" && <DraftsInbox expertId={expert.email} />}
      {tab === "kc" && <KCInbox expertId={expert.email} />}
      {tab === "testset" && <TestSetInbox expertId={expert.email} />}
    </div>
  );
}

interface TabButtonProps {
  current: Tab;
  value: Tab;
  onClick: (tab: Tab) => void;
  children: string;
}

function TabButton({ current, value, onClick, children }: TabButtonProps) {
  const active = current === value;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={() => onClick(value)}
      className={cn(
        "px-3 py-1.5 text-sm font-medium transition",
        active
          ? "border-b-2 border-brand-600 text-brand-700"
          : "border-b-2 border-transparent text-slate-500 hover:text-slate-700",
      )}
    >
      {children}
    </button>
  );
}

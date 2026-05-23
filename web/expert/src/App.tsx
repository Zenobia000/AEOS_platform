import { useState } from "react";
import { DraftsInbox } from "./pages/DraftsInbox";
import { KCInbox } from "./pages/KCInbox";
import { cn } from "./lib/cn";

type Tab = "drafts" | "kc";
const DEFAULT_EXPERT_ID = "expert-local";

export default function App() {
  const [tab, setTab] = useState<Tab>("drafts");
  const [expertId, setExpertId] = useState<string>(() => {
    try {
      return window.localStorage.getItem("aeos.expert_id") ?? DEFAULT_EXPERT_ID;
    } catch {
      return DEFAULT_EXPERT_ID;
    }
  });

  const persistExpertId = (next: string) => {
    setExpertId(next);
    try {
      window.localStorage.setItem("aeos.expert_id", next);
    } catch {
      /* localStorage unavailable; ignore */
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <header className="mb-4">
        <div className="flex items-baseline justify-between">
          <div>
            <h1 className="text-xl font-semibold">AEOS Expert Console</h1>
            <p className="text-sm text-slate-500">
              Draft Mode + KC 審查介面
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <label htmlFor="expert-id" className="text-slate-600">
              Expert ID
            </label>
            <input
              id="expert-id"
              value={expertId}
              onChange={(e) => persistExpertId(e.target.value)}
              className="w-40 rounded-md border border-slate-300 px-2 py-1 font-mono text-xs"
            />
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
      </nav>

      {tab === "drafts" && <DraftsInbox expertId={expertId} />}
      {tab === "kc" && <KCInbox expertId={expertId} />}
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

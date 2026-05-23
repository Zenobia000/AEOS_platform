import { useCallback, useEffect, useState } from "react";
import {
  approveReview,
  editReview,
  listReviews,
  rejectReview,
  ApiError,
} from "./api/expert";
import { ReviewCard } from "./components/ReviewCard";
import { Button } from "./components/Button";
import type { ReviewItem } from "./types";

const DEFAULT_EXPERT_ID = "expert-local";

export default function App() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [expertId, setExpertId] = useState<string>(() => {
    try {
      return localStorage.getItem("aeos.expert_id") ?? DEFAULT_EXPERT_ID;
    } catch {
      return DEFAULT_EXPERT_ID;
    }
  });

  const persistExpertId = (next: string) => {
    setExpertId(next);
    try {
      localStorage.setItem("aeos.expert_id", next);
    } catch {
      /* localStorage unavailable; ignore */
    }
  };

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listReviews({ signal });
      setItems(resp.items);
    } catch (err) {
      if (signal?.aborted) return;
      const message = err instanceof ApiError ? err.detail : String(err);
      setError(message);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void refresh(ctrl.signal);
    return () => ctrl.abort();
  }, [refresh]);

  const markBusy = (id: string, busy: boolean) => {
    setBusyIds((prev) => {
      const next = new Set(prev);
      if (busy) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const runAction = async (
    outboundId: string,
    fn: () => Promise<unknown>,
  ): Promise<void> => {
    markBusy(outboundId, true);
    setError(null);
    try {
      await fn();
      setItems((prev) => prev.filter((it) => it.outbound_id !== outboundId));
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : String(err);
      setError(message);
    } finally {
      markBusy(outboundId, false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <header className="mb-6 flex items-baseline justify-between">
        <div>
          <h1 className="text-xl font-semibold">AEOS Expert Console</h1>
          <p className="text-sm text-slate-500">Draft Mode review queue</p>
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
          <Button onClick={() => void refresh()} disabled={loading} variant="ghost">
            ↻ 重新整理
          </Button>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {loading && items.length === 0 && (
        <p className="text-sm text-slate-500">載入中…</p>
      )}

      {!loading && items.length === 0 && !error && (
        <p className="text-sm text-slate-500">目前沒有待審的 draft。</p>
      )}

      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.outbound_id}>
            <ReviewCard
              item={item}
              busy={busyIds.has(item.outbound_id)}
              onApprove={() =>
                void runAction(item.outbound_id, () =>
                  approveReview(item.outbound_id, expertId),
                )
              }
              onEdit={(newContent) =>
                void runAction(item.outbound_id, () =>
                  editReview(item.outbound_id, expertId, newContent),
                )
              }
              onReject={(reason, handoffMessage) =>
                void runAction(item.outbound_id, () =>
                  rejectReview(item.outbound_id, expertId, reason, handoffMessage),
                )
              }
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

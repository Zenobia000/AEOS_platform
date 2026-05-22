import { useCallback, useEffect, useState } from "react";
import {
  approveReview,
  editReview,
  listReviews,
  rejectReview,
  ApiError,
} from "../api/expert";
import { ReviewCard } from "../components/ReviewCard";
import { Button } from "../components/Button";
import type { ReviewItem } from "../types";

interface Props {
  expertId: string;
}

export function DraftsInbox({ expertId }: Props) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listReviews({ signal });
      setItems(resp.items);
    } catch (err) {
      if (signal?.aborted) return;
      setError(err instanceof ApiError ? err.detail : String(err));
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

  const runAction = async (id: string, fn: () => Promise<unknown>) => {
    markBusy(id, true);
    setError(null);
    try {
      await fn();
      setItems((prev) => prev.filter((it) => it.outbound_id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      markBusy(id, false);
    }
  };

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-700">
          Draft 待審佇列（{items.length}）
        </h2>
        <Button onClick={() => void refresh()} disabled={loading} variant="ghost">
          ↻ 重新整理
        </Button>
      </div>

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
    </section>
  );
}

import { useCallback, useEffect, useState } from "react";
import {
  approveDraft,
  archiveDraft,
  editDraft,
  listDrafts,
} from "../api/kc";
import { ApiError } from "../api/expert";
import { KCCard } from "../components/KCCard";
import { Button } from "../components/Button";
import type { KCDraftItem } from "../types";

interface Props {
  expertId: string;
}

export function KCInbox({ expertId }: Props) {
  const [items, setItems] = useState<KCDraftItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listDrafts({ signal });
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
      setItems((prev) => prev.filter((it) => it.kc_id !== id));
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
          KC Draft 待審佇列（{items.length}）
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
        <p className="text-sm text-slate-500">目前沒有待審的 KC draft。</p>
      )}

      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.kc_id}>
            <KCCard
              item={item}
              busy={busyIds.has(item.kc_id)}
              onApprove={() =>
                void runAction(item.kc_id, () =>
                  approveDraft(item.kc_id, expertId),
                )
              }
              onEdit={(payload) =>
                void runAction(item.kc_id, () =>
                  editDraft(item.kc_id, expertId, payload),
                )
              }
              onArchive={(reason) =>
                void runAction(item.kc_id, () =>
                  archiveDraft(item.kc_id, expertId, reason),
                )
              }
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

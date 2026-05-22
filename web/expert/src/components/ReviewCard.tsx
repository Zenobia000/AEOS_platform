import { useState } from "react";
import type { ReviewItem } from "../types";
import { Button } from "./Button";

interface Props {
  item: ReviewItem;
  busy: boolean;
  onApprove: () => void;
  onEdit: (newContent: string) => void;
  onReject: (reason: string, handoffMessage?: string) => void;
}

type Mode = "view" | "edit" | "reject";

export function ReviewCard({ item, busy, onApprove, onEdit, onReject }: Props) {
  const [mode, setMode] = useState<Mode>("view");
  const [draftEdit, setDraftEdit] = useState(item.draft_text ?? "");
  const [rejectReason, setRejectReason] = useState("");
  const [handoffMessage, setHandoffMessage] = useState("");

  const submitEdit = () => {
    if (!draftEdit.trim()) return;
    onEdit(draftEdit);
  };

  const submitReject = () => {
    if (!rejectReason.trim()) return;
    onReject(rejectReason, handoffMessage.trim() || undefined);
  };

  return (
    <article
      data-testid={`review-card-${item.outbound_id}`}
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <header className="mb-3 flex items-baseline justify-between gap-2">
        <div className="text-xs text-slate-500">
          <span className="font-mono">{item.channel}</span>
          <span className="mx-1.5">·</span>
          <span className="font-mono">{item.channel_user_id}</span>
        </div>
        <time className="text-xs text-slate-400">
          {item.created_at ? new Date(item.created_at).toLocaleString() : "—"}
        </time>
      </header>

      {mode === "view" && (
        <>
          <p className="mb-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
            {item.draft_text ?? <em className="text-slate-400">（無 draft 內容）</em>}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onApprove} disabled={busy} variant="primary">
              ✓ 同意送出
            </Button>
            <Button
              onClick={() => setMode("edit")}
              disabled={busy}
              variant="secondary"
            >
              ✎ 編輯後送出
            </Button>
            <Button
              onClick={() => setMode("reject")}
              disabled={busy}
              variant="danger"
            >
              ✕ 拒絕並轉接
            </Button>
          </div>
        </>
      )}

      {mode === "edit" && (
        <div className="space-y-3">
          <textarea
            value={draftEdit}
            onChange={(e) => setDraftEdit(e.target.value)}
            rows={6}
            aria-label="編輯後的回覆內容"
            className="w-full rounded-md border border-slate-300 p-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <div className="flex gap-2">
            <Button onClick={submitEdit} disabled={busy || !draftEdit.trim()}>
              送出編輯版
            </Button>
            <Button
              onClick={() => {
                setDraftEdit(item.draft_text ?? "");
                setMode("view");
              }}
              disabled={busy}
              variant="ghost"
            >
              取消
            </Button>
          </div>
        </div>
      )}

      {mode === "reject" && (
        <div className="space-y-3">
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={2}
            placeholder="拒絕原因（會進 audit log）"
            aria-label="拒絕原因"
            className="w-full rounded-md border border-slate-300 p-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <textarea
            value={handoffMessage}
            onChange={(e) => setHandoffMessage(e.target.value)}
            rows={2}
            placeholder="轉接訊息（選填，給接手 expert 看）"
            aria-label="轉接訊息"
            className="w-full rounded-md border border-slate-300 p-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <div className="flex gap-2">
            <Button
              onClick={submitReject}
              disabled={busy || !rejectReason.trim()}
              variant="danger"
            >
              確認拒絕並建立 handoff
            </Button>
            <Button
              onClick={() => {
                setRejectReason("");
                setHandoffMessage("");
                setMode("view");
              }}
              disabled={busy}
              variant="ghost"
            >
              取消
            </Button>
          </div>
        </div>
      )}
    </article>
  );
}

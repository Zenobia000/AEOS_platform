import { useState } from "react";
import type { KCCardType, KCDraftItem } from "../types";
import { Button } from "./Button";

interface Props {
  item: KCDraftItem;
  busy: boolean;
  onApprove: () => void;
  onEdit: (payload: {
    title?: string;
    body_markdown?: string;
    tags?: string[];
    card_type?: KCCardType;
  }) => void;
  onArchive: (reason: string) => void;
}

type Mode = "view" | "edit" | "archive";

const CARD_TYPES: KCCardType[] = ["faq", "policy", "product", "procedure", "risk"];

export function KCCard({ item, busy, onApprove, onEdit, onArchive }: Props) {
  const [mode, setMode] = useState<Mode>("view");
  const [title, setTitle] = useState(item.title);
  const [body, setBody] = useState(item.body_markdown);
  const [tagsStr, setTagsStr] = useState(item.tags.join(", "));
  const [cardType, setCardType] = useState<KCCardType>(item.card_type);
  const [archiveReason, setArchiveReason] = useState("");

  const submitEdit = () => {
    const payload: Parameters<typeof onEdit>[0] = {};
    if (title.trim() && title !== item.title) payload.title = title;
    if (body.trim() && body !== item.body_markdown) payload.body_markdown = body;
    const parsedTags = tagsStr
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (JSON.stringify(parsedTags) !== JSON.stringify(item.tags)) {
      payload.tags = parsedTags;
    }
    if (cardType !== item.card_type) payload.card_type = cardType;
    if (Object.keys(payload).length === 0) return;
    onEdit(payload);
  };

  const submitArchive = () => {
    if (!archiveReason.trim()) return;
    onArchive(archiveReason);
  };

  return (
    <article
      data-testid={`kc-card-${item.kc_id}`}
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <header className="mb-3 flex items-baseline justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded bg-brand-50 px-1.5 py-0.5 font-mono text-xs text-brand-700">
            {item.card_type}
          </span>
          <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
        </div>
        <time className="text-xs text-slate-400">
          {item.created_at ? new Date(item.created_at).toLocaleString() : "—"}
        </time>
      </header>

      {mode === "view" && (
        <>
          <p className="mb-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
            {item.body_markdown}
          </p>
          {item.tags.length > 0 && (
            <ul className="mb-3 flex flex-wrap gap-1">
              {item.tags.map((tag) => (
                <li
                  key={tag}
                  className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600"
                >
                  #{tag}
                </li>
              ))}
            </ul>
          )}
          <div className="flex flex-wrap gap-2">
            <Button onClick={onApprove} disabled={busy} variant="primary">
              ✓ 同意收錄
            </Button>
            <Button
              onClick={() => setMode("edit")}
              disabled={busy}
              variant="secondary"
            >
              ✎ 編輯後收錄
            </Button>
            <Button
              onClick={() => setMode("archive")}
              disabled={busy}
              variant="danger"
            >
              ✕ 封存
            </Button>
          </div>
        </>
      )}

      {mode === "edit" && (
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-slate-500" htmlFor={`t-${item.kc_id}`}>
              標題
            </label>
            <input
              id={`t-${item.kc_id}`}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-500" htmlFor={`b-${item.kc_id}`}>
              內容
            </label>
            <textarea
              id={`b-${item.kc_id}`}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={6}
              className="w-full rounded-md border border-slate-300 p-2 text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label
                className="mb-1 block text-xs text-slate-500"
                htmlFor={`tg-${item.kc_id}`}
              >
                標籤（逗號分隔）
              </label>
              <input
                id={`tg-${item.kc_id}`}
                value={tagsStr}
                onChange={(e) => setTagsStr(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-sm"
              />
            </div>
            <div>
              <label
                className="mb-1 block text-xs text-slate-500"
                htmlFor={`ct-${item.kc_id}`}
              >
                類別
              </label>
              <select
                id={`ct-${item.kc_id}`}
                value={cardType}
                onChange={(e) => setCardType(e.target.value as KCCardType)}
                className="w-full rounded-md border border-slate-300 p-2 text-sm"
              >
                {CARD_TYPES.map((ct) => (
                  <option key={ct} value={ct}>
                    {ct}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={submitEdit} disabled={busy}>
              送出編輯版
            </Button>
            <Button
              onClick={() => {
                setTitle(item.title);
                setBody(item.body_markdown);
                setTagsStr(item.tags.join(", "));
                setCardType(item.card_type);
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

      {mode === "archive" && (
        <div className="space-y-3">
          <textarea
            value={archiveReason}
            onChange={(e) => setArchiveReason(e.target.value)}
            rows={2}
            placeholder="封存原因（會進 audit log）"
            aria-label="封存原因"
            className="w-full rounded-md border border-slate-300 p-2 text-sm"
          />
          <div className="flex gap-2">
            <Button
              onClick={submitArchive}
              disabled={busy || !archiveReason.trim()}
              variant="danger"
            >
              確認封存
            </Button>
            <Button
              onClick={() => {
                setArchiveReason("");
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

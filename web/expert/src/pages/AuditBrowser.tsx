import { useCallback, useEffect, useState } from "react";
import {
  getConversation,
  listConversations,
  listEvents,
} from "../api/audit";
import { ApiError } from "../api/expert";
import { Button } from "../components/Button";
import type {
  AuditEvent,
  ConversationDetail,
  ConversationSummary,
} from "../types";

type View = "events" | "conversations" | "conversation_detail";

export function AuditBrowser() {
  const [view, setView] = useState<View>("conversations");
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [eventTypeFilter, setEventTypeFilter] = useState("");

  const refreshEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listEvents({
        eventType: eventTypeFilter.trim() || undefined,
        sinceHours: 24,
        limit: 100,
      });
      setEvents(resp.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setLoading(false);
    }
  }, [eventTypeFilter]);

  const refreshConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listConversations({ limit: 50 });
      setConversations(resp.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const openConversation = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConversation(id);
      setDetail(data);
      setView("conversation_detail");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (view === "events") void refreshEvents();
    else if (view === "conversations") void refreshConversations();
  }, [view, refreshEvents, refreshConversations]);

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <SubTab current={view} value="conversations" onClick={setView}>
          對話列表
        </SubTab>
        <SubTab current={view} value="events" onClick={setView}>
          Audit 事件
        </SubTab>
        <div className="ml-auto">
          <Button
            onClick={() =>
              view === "events"
                ? void refreshEvents()
                : void refreshConversations()
            }
            disabled={loading || view === "conversation_detail"}
            variant="ghost"
          >
            ↻ 重新整理
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

      {view === "events" && (
        <div>
          <div className="mb-3 flex gap-2">
            <input
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              placeholder="event_type filter (e.g. expert.draft_approved)"
              className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <Button onClick={() => void refreshEvents()} disabled={loading}>
              套用
            </Button>
          </div>
          {events.length === 0 ? (
            <p className="text-sm text-slate-500">
              過去 24 小時無 audit 事件{eventTypeFilter ? "（filter）" : ""}
            </p>
          ) : (
            <ul className="space-y-1.5">
              {events.map((e) => (
                <li
                  key={e.id}
                  className="rounded-md border border-slate-200 bg-white p-2 text-xs"
                  data-testid={`audit-event-${e.id}`}
                >
                  <div className="flex items-baseline justify-between">
                    <span className="font-mono font-semibold text-brand-700">
                      {e.event_type}
                    </span>
                    <time className="text-slate-400">
                      {new Date(e.occurred_at).toLocaleString()}
                    </time>
                  </div>
                  <div className="mt-0.5 text-slate-500">
                    actor: <span className="font-mono">{e.actor_id}</span>
                    {e.resource_type && (
                      <>
                        {" "}
                        · {e.resource_type}:
                        <span className="ml-1 font-mono text-slate-600">
                          {e.resource_id?.slice(0, 8)}…
                        </span>
                      </>
                    )}
                  </div>
                  {Object.keys(e.payload).length > 0 && (
                    <pre className="mt-1 whitespace-pre-wrap break-all rounded bg-slate-50 p-1 font-mono text-[10px] text-slate-700">
                      {JSON.stringify(e.payload, null, 2)}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {view === "conversations" && (
        <ul className="space-y-2">
          {conversations.length === 0 && !loading ? (
            <p className="text-sm text-slate-500">尚無對話。</p>
          ) : (
            conversations.map((c) => (
              <li
                key={c.conversation_id}
                className="cursor-pointer rounded-md border border-slate-200 bg-white p-3 text-sm hover:bg-slate-50"
                data-testid={`conv-row-${c.conversation_id}`}
                onClick={() => void openConversation(c.conversation_id)}
              >
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">
                      {c.channel}
                    </span>{" "}
                    <span className="font-mono text-xs">
                      {c.channel_user_id}
                    </span>
                    <span className="ml-2 text-xs text-slate-400">
                      {c.message_count} msgs
                    </span>
                  </div>
                  <time className="text-xs text-slate-400">
                    {c.last_message_at
                      ? new Date(c.last_message_at).toLocaleString()
                      : "—"}
                  </time>
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  status: {c.status}
                  {c.outcome && <span> · outcome: {c.outcome}</span>}
                </div>
              </li>
            ))
          )}
        </ul>
      )}

      {view === "conversation_detail" && detail && (
        <ConversationDetailView
          detail={detail}
          onBack={() => {
            setDetail(null);
            setView("conversations");
          }}
        />
      )}
    </section>
  );
}

function ConversationDetailView({
  detail,
  onBack,
}: {
  detail: ConversationDetail;
  onBack: () => void;
}) {
  const conv = detail.conversation;
  return (
    <div className="space-y-4" data-testid="conversation-detail">
      <div className="flex items-center justify-between">
        <Button onClick={onBack} variant="ghost">
          ← 返回列表
        </Button>
        <div className="text-xs text-slate-500">
          <span className="font-mono">{conv.id.slice(0, 8)}…</span>
          {" · "}status: <span className="font-medium">{conv.status}</span>
          {conv.outcome && <> · outcome: {conv.outcome}</>}
        </div>
      </div>

      <section>
        <h3 className="mb-2 text-sm font-semibold">訊息（{detail.messages.length}）</h3>
        <ul className="space-y-1.5">
          {detail.messages.map((m) => (
            <li
              key={m.id}
              className={`rounded-md border p-2 text-sm ${
                m.role === "user"
                  ? "border-slate-200 bg-slate-50"
                  : m.role === "assistant"
                    ? "border-brand-100 bg-brand-50"
                    : "border-amber-200 bg-amber-50"
              }`}
            >
              <div className="mb-0.5 text-xs text-slate-500">
                #{m.seq} · {m.role}
                {m.token_count !== null && <> · {m.token_count} tokens</>}
              </div>
              <div className="whitespace-pre-wrap text-slate-800">
                {m.content}
              </div>
              {m.tool_invocations.length > 0 && (
                <ul
                  className="mt-2 space-y-0.5 border-t border-slate-200 pt-1.5 text-xs"
                  data-testid={`tool-invocations-${m.id}`}
                >
                  {m.tool_invocations.map((t, idx) => (
                    <li key={idx} className="text-slate-600">
                      <span className={t.ok ? "text-green-700" : "text-red-700"}>
                        🔧 {t.name}
                      </span>
                      {t.kc_refs && t.kc_refs.length > 0 && (
                        <span className="ml-1.5">
                          引用 {t.kc_refs.length} 張 KC:{" "}
                          {t.kc_refs.map((id, i) => (
                            <span
                              key={id}
                              className="ml-0.5 rounded bg-brand-50 px-1 font-mono text-[10px] text-brand-700"
                            >
                              {id.slice(0, 8)}
                              {i < t.kc_refs!.length - 1 ? "," : ""}
                            </span>
                          ))}
                        </span>
                      )}
                      {t.error && (
                        <span className="ml-1.5 text-red-600">— {t.error}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      {detail.outbounds.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold">
            Outbound 推送（{detail.outbounds.length}）
          </h3>
          <ul className="space-y-1 text-xs">
            {detail.outbounds.map((o) => (
              <li
                key={o.id}
                className="rounded border border-slate-200 bg-white p-1.5"
              >
                <span
                  className={`font-mono ${
                    o.status === "sent"
                      ? "text-green-700"
                      : o.status === "failed"
                        ? "text-red-700"
                        : "text-slate-700"
                  }`}
                >
                  [{o.status}]
                </span>{" "}
                {o.channel}
                {o.retry_count > 0 && <> · retried {o.retry_count}x</>}
                {o.error_message && (
                  <span className="text-red-600"> · {o.error_message}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3 className="mb-2 text-sm font-semibold">
          Audit 事件（{detail.audit_events.length}）
        </h3>
        <ul className="space-y-1 text-xs">
          {detail.audit_events.map((e) => (
            <li
              key={e.id}
              className="rounded border border-slate-200 bg-white p-1.5"
            >
              <div className="flex items-baseline justify-between">
                <span className="font-mono font-semibold text-brand-700">
                  {e.event_type}
                </span>
                <time className="text-slate-400">
                  {new Date(e.occurred_at).toLocaleString()}
                </time>
              </div>
              <div className="text-slate-500">
                actor: {e.actor_id ?? "—"}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function SubTab({
  current,
  value,
  onClick,
  children,
}: {
  current: View;
  value: View;
  onClick: (v: View) => void;
  children: string;
}) {
  const active = current === value;
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className={`rounded-md px-2.5 py-1 text-sm ${
        active
          ? "bg-brand-50 text-brand-700 font-medium"
          : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

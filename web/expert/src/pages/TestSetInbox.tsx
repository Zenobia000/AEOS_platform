import { useCallback, useEffect, useState } from "react";
import {
  createCase,
  createRun,
  disableCase,
  getRun,
  getRunCases,
  listCases,
} from "../api/testset";
import { ApiError } from "../api/expert";
import { Button } from "../components/Button";
import type {
  TestCaseItem,
  TestRunCaseItem,
  TestRunSummary,
} from "../types";

interface Props {
  expertId: string;
  skillSlug?: string;  // CR-0001 後續 #23：top-level SkillSelector 傳入；_all_ 視同無 filter
}

const DEFAULT_TENANT_KEY = "aeos.testset.tenant_id";
const DEFAULT_SKILL_SLUG = "customer-service/faq-respond";
const DEFAULT_SKILL_VERSION = "v1.0.0";

export function TestSetInbox({ expertId, skillSlug }: Props) {
  const [tenantId, setTenantId] = useState<string>(() => {
    try {
      return window.localStorage.getItem(DEFAULT_TENANT_KEY) ?? "";
    } catch {
      return "";
    }
  });
  const [cases, setCases] = useState<TestCaseItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [runSummary, setRunSummary] = useState<TestRunSummary | null>(null);
  const [runCases, setRunCases] = useState<TestRunCaseItem[]>([]);

  // ── form state ──
  const [name, setName] = useState("");
  const [userInput, setUserInput] = useState("");
  const [expectedOutcome, setExpectedOutcome] = useState("");
  const [keywords, setKeywords] = useState("");

  const persistTenant = (next: string) => {
    setTenantId(next);
    try {
      window.localStorage.setItem(DEFAULT_TENANT_KEY, next);
    } catch {
      /* ignore */
    }
  };

  const refreshCases = useCallback(
    async (signal?: AbortSignal) => {
      if (!tenantId) {
        setCases([]);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const resp = await listCases({ tenantId, skillSlug, signal });
        setCases(resp.items);
      } catch (err) {
        if (signal?.aborted) return;
        setError(err instanceof ApiError ? err.detail : String(err));
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [tenantId, skillSlug],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void refreshCases(ctrl.signal);
    return () => ctrl.abort();
  }, [refreshCases]);

  const submitCreate = async () => {
    if (!tenantId || !name.trim() || !userInput.trim() || !expectedOutcome.trim()) {
      setError("請填寫 tenant_id / name / user_input / expected_outcome");
      return;
    }
    setError(null);
    try {
      await createCase({
        tenant_id: tenantId,
        name,
        user_input: userInput,
        expected_outcome: expectedOutcome,
        expected_keywords: keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
        created_by: expertId,
      });
      setName("");
      setUserInput("");
      setExpectedOutcome("");
      setKeywords("");
      await refreshCases();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    }
  };

  const submitDisable = async (caseId: string) => {
    setError(null);
    try {
      await disableCase(caseId);
      setCases((prev) => prev.filter((c) => c.case_id !== caseId));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    }
  };

  const submitRun = async () => {
    if (!tenantId) return;
    setError(null);
    setRunSummary(null);
    setRunCases([]);
    try {
      const created = await createRun({
        tenant_id: tenantId,
        skill_slug: DEFAULT_SKILL_SLUG,
        skill_version: DEFAULT_SKILL_VERSION,
        created_by: expertId,
      });
      const summary = await getRun(created.run_id);
      setRunSummary(summary);
      const runCasesResp = await getRunCases(created.run_id);
      setRunCases(runCasesResp.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : String(err));
    }
  };

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="testset-tenant" className="text-sm text-slate-600">
          Tenant ID
        </label>
        <input
          id="testset-tenant"
          value={tenantId}
          onChange={(e) => persistTenant(e.target.value)}
          placeholder="UUID"
          className="w-80 rounded-md border border-slate-300 px-2 py-1 font-mono text-xs"
        />
        <Button onClick={() => void refreshCases()} disabled={loading} variant="ghost">
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

      {/* 新增 case form */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold">新增 Test Case</h3>
        <div className="space-y-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="名稱（e.g. 退貨期限）"
            className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          />
          <input
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="User input（e.g. 退貨多久）"
            className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          />
          <input
            value={expectedOutcome}
            onChange={(e) => setExpectedOutcome(e.target.value)}
            placeholder="Expected outcome（描述期望回答）"
            className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          />
          <input
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="Expected keywords（逗號分隔，e.g. 7 天, 發票）"
            className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          />
          <Button onClick={submitCreate}>新增</Button>
        </div>
      </div>

      {/* cases 列表 */}
      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">已啟用 Test Cases（{cases.length}）</h3>
          <Button
            onClick={submitRun}
            disabled={cases.length === 0}
            variant="primary"
          >
            ▶ 跑一次 test run
          </Button>
        </div>
        {cases.length === 0 ? (
          <p className="text-sm text-slate-500">尚無 case；請先新增。</p>
        ) : (
          <ul className="space-y-2">
            {cases.map((c) => (
              <li
                key={c.case_id}
                className="rounded-md border border-slate-200 bg-white p-3"
                data-testid={`testcase-${c.case_id}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-900">
                      {c.name}
                    </div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      Q: {c.user_input}
                    </div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      Expected: {c.expected_outcome}
                    </div>
                    {c.expected_keywords.length > 0 && (
                      <ul className="mt-1 flex flex-wrap gap-1">
                        {c.expected_keywords.map((kw) => (
                          <li
                            key={kw}
                            className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600"
                          >
                            #{kw}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <Button
                    onClick={() => void submitDisable(c.case_id)}
                    variant="danger"
                  >
                    停用
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* run 結果 */}
      {runSummary && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold">最近一次 Test Run</h3>
          <div className="grid grid-cols-4 gap-3 text-sm">
            <Stat label="Status" value={runSummary.status} />
            <Stat
              label="Pass rate"
              value={`${(runSummary.pass_rate * 100).toFixed(1)}%`}
              highlight={runSummary.pass_rate >= 0.8 ? "good" : "bad"}
            />
            <Stat label="Passed" value={String(runSummary.passed_cases)} />
            <Stat label="Failed" value={String(runSummary.failed_cases)} />
          </div>
          {runCases.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs">
              {runCases.map((rc) => (
                <li key={rc.case_id} className="border-t border-slate-100 pt-1">
                  <span className="font-mono text-slate-500">[{rc.status}]</span>{" "}
                  <span className="text-slate-700">{rc.name}</span>
                  {rc.judge_reason && (
                    <span className="ml-2 text-slate-400">— {rc.judge_reason}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "good" | "bad";
}) {
  const color =
    highlight === "good"
      ? "text-green-700"
      : highlight === "bad"
        ? "text-red-700"
        : "text-slate-900";
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`font-semibold ${color}`}>{value}</div>
    </div>
  );
}

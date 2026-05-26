/**
 * AdminSkills — Skills inspector + bindings 管理 UI (Phase 1 後續 #14 + #18).
 *
 * 對應 CR-0001 §9 #6 API（POST /admin/skills/bindings 等）已落地，
 * 但缺對應 UI。本頁面：
 * - 列出當前 tenant 的 skills（含 version + status）
 * - 列出 skill_binding（含 routing_rule + is_default）
 * - 顯示 quality gate / approve 狀態
 *
 * Phase 1 範圍：read-only view（CRUD 留 admin API 直接 curl；
 * 未來可加 inline edit）。
 */
import { useCallback, useEffect, useState } from "react";

import { authHeader } from "../lib/authStore";

const DEFAULT_TENANT_KEY = "aeos.testset.tenant_id";

interface SkillRow {
  id: string;
  slug: string;
  vertical: string;
  name: string;
  current_production_version: string | null;
}

interface SkillVersionRow {
  id: string;
  skill_id: string;
  version: string;
  status: string;
}

interface SkillBindingRow {
  id: string;
  employee_id: string;
  skill_version_id: string;
  routing_rule: Record<string, unknown>;
  is_default: boolean;
  priority: number;
}

interface SkillsResponse {
  tenant_id: string;
  skills: SkillRow[];
  skill_versions: SkillVersionRow[];
  bindings: SkillBindingRow[];
}

export function AdminSkills() {
  const [tenantId, setTenantId] = useState<string>(() => {
    try {
      return window.localStorage.getItem(DEFAULT_TENANT_KEY) ?? "";
    } catch {
      return "";
    }
  });
  const [data, setData] = useState<SkillsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`/api/v1/admin/skills/${tenantId}`, {
        headers: authHeader(),
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      setData((await resp.json()) as SkillsResponse);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    if (tenantId) void refresh();
  }, [refresh, tenantId]);

  return (
    <div data-testid="admin-skills" className="space-y-4">
      <h2 className="text-lg font-semibold">Skill Registry Inspector</h2>

      <div className="flex gap-2">
        <input
          value={tenantId}
          onChange={(e) => {
            const v = e.target.value;
            setTenantId(v);
            try {
              window.localStorage.setItem(DEFAULT_TENANT_KEY, v);
            } catch {
              /* ignore */
            }
          }}
          placeholder="tenant_id (UUID)"
          className="w-96 rounded-md border border-slate-300 px-2 py-1 text-sm"
        />
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={!tenantId || loading}
          className="rounded-md bg-brand-600 px-3 py-1 text-sm text-white disabled:opacity-50"
        >
          {loading ? "載入中..." : "查詢"}
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {data && (
        <>
          <section>
            <h3 className="mb-2 text-sm font-semibold">
              Skills ({data.skills.length})
            </h3>
            {data.skills.length === 0 ? (
              <p className="text-sm text-slate-500">未綁定 skill</p>
            ) : (
              <ul className="space-y-1.5">
                {data.skills.map((s) => (
                  <li
                    key={s.id}
                    data-testid={`admin-skill-${s.id}`}
                    className="rounded-md border border-slate-200 p-2 text-sm"
                  >
                    <div className="font-medium">{s.name}</div>
                    <div className="text-xs text-slate-600">
                      {s.slug} · vertical: {s.vertical}
                    </div>
                    {s.current_production_version && (
                      <div className="text-xs text-green-700">
                        production: {s.current_production_version}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h3 className="mb-2 text-sm font-semibold">
              Versions ({data.skill_versions.length})
            </h3>
            {data.skill_versions.length === 0 ? (
              <p className="text-sm text-slate-500">無 version</p>
            ) : (
              <ul className="space-y-1.5">
                {data.skill_versions.map((v) => (
                  <li
                    key={v.id}
                    data-testid={`admin-skill-version-${v.id}`}
                    className="rounded-md border border-slate-200 p-2 text-sm"
                  >
                    <span className="font-mono">v{v.version}</span>{" "}
                    <span
                      className={
                        v.status === "production"
                          ? "rounded bg-green-100 px-1.5 text-xs text-green-800"
                          : "rounded bg-slate-200 px-1.5 text-xs text-slate-700"
                      }
                    >
                      {v.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h3 className="mb-2 text-sm font-semibold">
              Bindings ({data.bindings.length})
            </h3>
            {data.bindings.length === 0 ? (
              <p className="text-sm text-slate-500">無 binding</p>
            ) : (
              <ul className="space-y-1.5">
                {data.bindings.map((b) => (
                  <li
                    key={b.id}
                    data-testid={`admin-skill-binding-${b.id}`}
                    className="rounded-md border border-slate-200 p-2 text-sm"
                  >
                    <div className="flex items-center gap-2">
                      {b.is_default && (
                        <span className="rounded bg-amber-100 px-1.5 text-xs text-amber-800">
                          default
                        </span>
                      )}
                      <span className="text-xs text-slate-600">
                        priority: {b.priority}
                      </span>
                    </div>
                    <div className="mt-1 font-mono text-xs text-slate-700">
                      rule: {JSON.stringify(b.routing_rule)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}

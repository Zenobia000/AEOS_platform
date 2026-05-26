/**
 * SkillSelector — top-level dropdown 切換目前審查的 skill scope.
 *
 * CR-0001 §9 #7 落地。設計（CR-0001 §8 #5）：
 * - top-level selector（vs per-tab filter）— 心智模型清楚
 * - URL ?skill_slug= 同步 — deep link 支援
 * - 全頁共享（React Context 在父層）
 *
 * Phase 1.5: 直接 hard-code 4 個已知 vertical skill；S2 之後改打
 * GET /api/v1/admin/skills/{tenant_id} 動態載入。
 */
import { cn } from "../lib/cn";

export interface SkillOption {
  slug: string;
  label: string;
}

export const KNOWN_SKILLS: SkillOption[] = [
  { slug: "customer-service/faq-respond", label: "客服 FAQ" },
  { slug: "hr/leave-request", label: "HR 請假" },
  { slug: "it-helpdesk/password-reset", label: "IT 密碼重設" },
  { slug: "sales/quote-request", label: "Sales 報價" },
  { slug: "finance/expense-claim", label: "Finance 報帳" },
  { slug: "legal/contract-review", label: "Legal 合約初審" },
  { slug: "_all_", label: "全部 skill" },
];

interface Props {
  value: string;
  onChange: (slug: string) => void;
  className?: string;
}

export function SkillSelector({ value, onChange, className }: Props) {
  return (
    <label
      className={cn("flex items-center gap-2 text-sm text-slate-600", className)}
    >
      <span className="text-xs text-slate-400">Skill</span>
      <select
        data-testid="skill-selector"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      >
        {KNOWN_SKILLS.map((s) => (
          <option key={s.slug} value={s.slug}>
            {s.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/**
 * SkillSelector — vitest unit + useSkillSlug URL sync test.
 * CR-0001 §9 #7 完成定義：vitest 通過驗證。
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { KNOWN_SKILLS, SkillSelector } from "./SkillSelector";

describe("SkillSelector", () => {
  it("renders all known skill options", () => {
    render(<SkillSelector value="_all_" onChange={() => {}} />);
    const select = screen.getByTestId("skill-selector") as HTMLSelectElement;
    expect(select).toBeInTheDocument();
    expect(select.options).toHaveLength(KNOWN_SKILLS.length);
    expect(select.value).toBe("_all_");
  });

  it("calls onChange with new slug when user picks an option", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SkillSelector value="_all_" onChange={onChange} />);

    const select = screen.getByTestId("skill-selector") as HTMLSelectElement;
    await user.selectOptions(select, "hr/leave-request");

    expect(onChange).toHaveBeenCalledWith("hr/leave-request");
  });

  it("controlled component reflects value prop", () => {
    render(<SkillSelector value="sales/quote-request" onChange={() => {}} />);
    const select = screen.getByTestId("skill-selector") as HTMLSelectElement;
    expect(select.value).toBe("sales/quote-request");
  });

  it("KNOWN_SKILLS contains 6 vertical + 1 ALL fallback (CR-0002 adds finance + legal)", () => {
    const slugs = KNOWN_SKILLS.map((s) => s.slug);
    expect(slugs).toContain("customer-service/faq-respond");
    expect(slugs).toContain("hr/leave-request");
    expect(slugs).toContain("it-helpdesk/password-reset");
    expect(slugs).toContain("sales/quote-request");
    expect(slugs).toContain("finance/expense-claim");
    expect(slugs).toContain("legal/contract-review");
    expect(slugs).toContain("_all_");
    expect(slugs).toHaveLength(7);
  });
});

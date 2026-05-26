/**
 * useSkillSlug — URL ?skill_slug= sync hook test.
 * CR-0001 §9 #7.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { DEFAULT_SLUG, useSkillSlug } from "./useSkillSlug";

describe("useSkillSlug", () => {
  beforeEach(() => {
    // 重置 URL
    window.history.replaceState({}, "", "/");
  });

  afterEach(() => {
    window.history.replaceState({}, "", "/");
  });

  it("returns default slug when URL has no query", () => {
    const { result } = renderHook(() => useSkillSlug());
    expect(result.current[0]).toBe(DEFAULT_SLUG);
  });

  it("reads initial slug from URL ?skill_slug=", () => {
    window.history.replaceState({}, "", "/?skill_slug=hr/leave-request");
    const { result } = renderHook(() => useSkillSlug());
    expect(result.current[0]).toBe("hr/leave-request");
  });

  it("writes to URL when setter called", () => {
    const { result } = renderHook(() => useSkillSlug());
    act(() => result.current[1]("sales/quote-request"));
    expect(result.current[0]).toBe("sales/quote-request");
    expect(window.location.search).toContain("skill_slug=sales");
  });

  it("removes query param when set to default", () => {
    window.history.replaceState({}, "", "/?skill_slug=hr/leave-request");
    const { result } = renderHook(() => useSkillSlug());
    act(() => result.current[1](DEFAULT_SLUG));
    expect(window.location.search).toBe("");
  });
});

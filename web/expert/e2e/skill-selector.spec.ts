/**
 * Playwright E2E — SkillSelector + URL ?skill_slug= sync.
 *
 * CR-0001 §9 #7 完成定義（goal）：Playwright 通過驗證。
 *
 * 驗證：
 * - SkillSelector dropdown 出現在登入後的 header
 * - 選 vertical → URL ?skill_slug= 同步
 * - 直接打 URL ?skill_slug=xxx → SkillSelector 顯示對應值
 * - 選 _all_ → URL query 移除
 */
import { test, expect } from "@playwright/test";
import { resetDemo } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  resetDemo();
});

test.describe("SkillSelector URL sync (CR-0001 #7)", () => {
  test("dropdown 出現在已登入的 header + 有 7 個選項 (CR-0002 加 finance + legal)", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("skill-selector");
    await expect(selector).toBeVisible();
    const options = await selector.locator("option").count();
    expect(options).toBe(7);
  });

  test("選 hr/leave-request → URL ?skill_slug= 同步", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("skill-selector");
    await selector.selectOption("hr/leave-request");
    await expect(page).toHaveURL(/skill_slug=hr%2Fleave-request|skill_slug=hr\/leave-request/);
  });

  test("直接打 ?skill_slug=sales/quote-request → selector 顯示對應值", async ({ page }) => {
    await page.goto("/?skill_slug=sales/quote-request");
    const selector = page.getByTestId("skill-selector");
    await expect(selector).toHaveValue("sales/quote-request");
  });

  test("選 全部 skill (_all_) → URL query 被移除", async ({ page }) => {
    await page.goto("/?skill_slug=hr/leave-request");
    const selector = page.getByTestId("skill-selector");
    await selector.selectOption("_all_");
    const url = new URL(page.url());
    expect(url.searchParams.has("skill_slug")).toBe(false);
  });

  test("切換 skill 不影響 tab 切換", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("skill-selector").selectOption("it-helpdesk/password-reset");
    // 切到 KC tab，URL 仍保留 skill_slug
    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    await expect(page).toHaveURL(/skill_slug=it-helpdesk/);
  });
});

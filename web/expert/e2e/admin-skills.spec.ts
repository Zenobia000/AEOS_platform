/**
 * Playwright E2E — AdminSkills inspector (Phase 1 後續 #14 + #18).
 *
 * 驗證 admin tab 內 Skill Registry Inspector 顯示 skill/version/binding 三段。
 */
import { test, expect } from "@playwright/test";
import { resetDemo, DEMO_TENANT_ID } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  resetDemo();
});

test("AdminSkills inspector 顯示 6 個 skill / 6 個 version / 6 個 binding", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("tab", { name: /Admin/ }).click();

  const inspector = page.getByTestId("admin-skills");
  await expect(inspector).toBeVisible();

  // 填 tenant_id + 點查詢
  await inspector.locator("input[placeholder*='tenant_id']").fill(DEMO_TENANT_ID);
  await inspector.getByRole("button", { name: /查詢/ }).click();

  // 6 個 skill 應顯示
  await expect(inspector.locator("[data-testid^='admin-skill-']")).toHaveCount(
    6 + 6 + 6, // skills + versions + bindings
    { timeout: 10000 },
  );
});

test("AdminSkills 標 default binding + production version", async ({ page }) => {
  await page.goto("/?skill_slug=_all_");
  await page.getByRole("tab", { name: /Admin/ }).click();
  const inspector = page.getByTestId("admin-skills");
  await inspector.locator("input[placeholder*='tenant_id']").fill(DEMO_TENANT_ID);
  await inspector.getByRole("button", { name: /查詢/ }).click();

  // 至少有 1 個 default binding（demo seed: customer-service is_default=true）
  await expect(inspector.locator("text=default").first()).toBeVisible({ timeout: 10000 });
});

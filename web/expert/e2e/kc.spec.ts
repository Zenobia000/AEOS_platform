/**
 * KC tab — edit / approve / archive 寫 DB 動作測試.
 * 對應 manual-ui-test §3.2-3.5.
 */
import { test, expect } from "@playwright/test";
import { resetDemo } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeEach(() => {
  resetDemo();
});

test.describe("KC tab write actions", () => {
  test("3.3 approve KC → 列表 3→2 + DB approved", async ({ page, request }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(3, { timeout: 10000 });

    await page
      .locator("[data-testid^='kc-card-']")
      .first()
      .getByRole("button", { name: /同意收錄/ })
      .click();

    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(2, { timeout: 5000 });

    const listResp = await request.get(
      `/api/v1/kc/drafts?tenant_id=${"9e7ffb09-4f53-475a-a771-29b02f04906a"}`,
    );
    expect((await listResp.json()).count).toBe(2);
  });

  test("3.2 edit card_type from faq → policy", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(3, { timeout: 10000 });

    // 找「保固期限」(card_type=faq) 那張卡
    const card = page
      .locator("[data-testid^='kc-card-']")
      .filter({ hasText: "保固期限" });
    await card.getByRole("button", { name: /編輯後收錄/ }).click();
    await card.getByLabel("類別").selectOption("policy");
    await card.getByRole("button", { name: /送出編輯版/ }).click();

    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(2, { timeout: 5000 });
  });

  test("3.4 archive KC + 填封存原因 → 列表 -1", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(3, { timeout: 10000 });

    const card = page.locator("[data-testid^='kc-card-']").first();
    await card.getByRole("button", { name: /封存/ }).click();
    await card.getByLabel("封存原因").fill("重複內容；已被另一張取代");
    await card.getByRole("button", { name: /確認封存/ }).click();

    await expect(
      page.locator("[data-testid^='kc-card-']"),
    ).toHaveCount(2, { timeout: 5000 });
  });
});

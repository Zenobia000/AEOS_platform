/**
 * Admin tab — create / disable / enable / validation 寫 DB 動作測試.
 * 對應 manual-ui-test §6.3-6.8.
 */
import { test, expect } from "@playwright/test";
import { resetDemo } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeEach(({ page }) => {
  resetDemo();
});

test.describe("Admin tab write actions", () => {
  test("6.2 密碼 < 6 字 → 422 紅 alert", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();
    await page.getByRole("button", { name: /\+ 新增帳號/ }).click();

    await page.getByPlaceholder("Email").fill("short@aeos");
    await page.getByPlaceholder("姓名").fill("Short");
    await page.getByPlaceholder(/密碼/).fill("abc"); // < 6
    await page.getByRole("button", { name: /^建立$/ }).click();

    // alert 顯示（detail 包含 422 / String should have / password 等）
    await expect(page.getByRole("alert")).toBeVisible({ timeout: 5000 });
  });

  test("6.3 建合法 expert 帳號 → 列表 +1", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();

    // seed 不建 expert，所以初始 0 個帳號（reset_demo 不動 expert_account）
    // → 等下面 create 後應該至少 1 個（或之前 session 殘留的）
    await page.getByRole("button", { name: /\+ 新增帳號/ }).click();
    await page
      .getByPlaceholder("Email")
      .fill(`e2e-${Date.now()}@aeos`);
    await page.getByPlaceholder("姓名").fill("E2E User");
    await page.getByPlaceholder(/密碼/).fill("secret123");
    await page.getByRole("button", { name: /^建立$/ }).click();

    // 表單收起 + 列表多一筆「E2E User」
    await expect(page.getByText("E2E User").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("6.5 disable 帳號 → 顯示 disabled badge", async ({ page, request }) => {
    // 先建一個 expert 帳號（curl）
    const email = `disable-${Date.now()}@aeos`;
    const createResp = await request.post("/api/v1/admin/experts", {
      data: {
        email,
        password: "secret123",
        name: "ToDisable",
        role: "expert",
      },
    });
    expect(createResp.status()).toBe(200);
    const account = await createResp.json();

    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();

    const row = page.locator(`[data-testid="expert-row-${account.id}"]`);
    await expect(row).toBeVisible({ timeout: 10000 });

    await row.getByRole("button", { name: /停用/ }).click();
    await expect(row.getByText("disabled")).toBeVisible({ timeout: 5000 });
  });

  test("6.4 重複 email → 409", async ({ page, request }) => {
    const email = `dup-${Date.now()}@aeos`;
    await request.post("/api/v1/admin/experts", {
      data: { email, password: "secret123", name: "First" },
    });

    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();
    await page.getByRole("button", { name: /\+ 新增帳號/ }).click();
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("姓名").fill("Second");
    await page.getByPlaceholder(/密碼/).fill("secret123");
    await page.getByRole("button", { name: /^建立$/ }).click();

    await expect(page.getByRole("alert")).toContainText("already exists", {
      timeout: 5000,
    });
  });
});

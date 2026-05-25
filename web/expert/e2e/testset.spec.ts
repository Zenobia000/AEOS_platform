/**
 * TestSet tab — 新增 case / 停用 / 跑 run 寫 DB 動作測試.
 * 對應 manual-ui-test §4.2-4.4.
 */
import { test, expect } from "@playwright/test";
import { resetDemo, DEMO_TENANT_ID } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  resetDemo();
  // 預先把 tenant_id 寫入 localStorage
  await page.goto("/");
  await page.evaluate((tid) => {
    window.localStorage.setItem("aeos.testset.tenant_id", tid);
  }, DEMO_TENANT_ID);
});

test.describe("TestSet write actions", () => {
  test("4.2 新增 case → 列表 +1", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Test Set/ }).click();

    // seed 完應該 5 個
    await expect(page.getByText(/已啟用 Test Cases（5/)).toBeVisible({
      timeout: 10000,
    });

    await page.getByPlaceholder(/名稱/).fill("E2E 測試題目");
    await page.getByPlaceholder(/User input/).fill("這是測試問題");
    await page.getByPlaceholder(/Expected outcome/).fill("這是預期答案");
    await page.getByPlaceholder(/Expected keywords/).fill("測試, 答案");
    await page.getByRole("button", { name: /^新增$/ }).click();

    // 應變 6 個
    await expect(page.getByText(/已啟用 Test Cases（6/)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("E2E 測試題目")).toBeVisible();
  });

  test("4.3 停用 case → 列表 -1", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Test Set/ }).click();
    await expect(page.getByText(/已啟用 Test Cases（5/)).toBeVisible({
      timeout: 10000,
    });

    // 點第一個 case 的「停用」按鈕
    await page
      .locator("[data-testid^='testcase-']")
      .first()
      .getByRole("button", { name: /停用/ })
      .click();

    await expect(page.getByText(/已啟用 Test Cases（4/)).toBeVisible({
      timeout: 5000,
    });
  });

  test("4.4 跑 test run（無 LLM key fallback 路徑）", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Test Set/ }).click();
    await expect(page.getByText(/已啟用 Test Cases（5/)).toBeVisible({
      timeout: 10000,
    });

    await page.getByRole("button", { name: /跑一次 test run/ }).click();

    // 應顯示 pass rate stat（即使 0%）+ Status 卡
    await expect(page.getByText(/Pass rate/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Status/)).toBeVisible();
  });
});

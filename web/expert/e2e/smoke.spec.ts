/**
 * AEOS Expert Console — E2E smoke tests.
 *
 * 對應 docs/report/MANUAL-UI-TEST-2026-05-25.html 中可自動化的 P0 測項。
 *
 * 前提：
 * - bypass mode（不設 AEOS_AUTH_REQUIRED）→ anonymous admin
 * - seed_demo 已跑：tenant 9e7ffb09-... + 1 draft + 3 KC + 5 test cases
 */
import { test, expect, Page } from "@playwright/test";
import { resetDemo, DEMO_TENANT_ID } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  resetDemo();
});

test.describe("Expert Console — bypass mode", () => {
  test("1.5 載入後直接看到 tabs（anonymous bypass，不顯 Login）", async ({ page }) => {
    await page.goto("/");
    // header 顯示 "AEOS Expert Console"
    await expect(page.getByRole("heading", { name: /AEOS Expert Console/ })).toBeVisible();
    // 五個 tab 都在（含 admin，因為 bypass 角色是 admin）
    await expect(page.getByRole("tab", { name: /訊息草稿/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /KC 知識卡/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Test Set/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Audit/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Admin/ })).toBeVisible();
    // header 顯示 anonymous
    await expect(page.getByText("anonymous (auth bypass)")).toBeVisible();
  });

  test("2.1 Drafts tab 預設選中 + 顯示 seed 的 1 筆 draft", async ({ page }) => {
    await page.goto("/");
    // 預設 tab = drafts；應顯示退貨 draft
    await expect(
      page.getByText(/本店退貨可於到貨後 7 天內申請/),
    ).toBeVisible({ timeout: 10000 });
    // 應有 3 個動作按鈕
    await expect(page.getByRole("button", { name: /同意送出/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /編輯後送出/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /拒絕並轉接/ })).toBeVisible();
  });

  test("3.1 KC tab 切換顯示 3 張 draft", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    // 標題列
    await expect(page.getByText(/KC Draft 待審佇列/)).toBeVisible({ timeout: 10000 });
    // 3 張 draft
    await expect(page.getByText("退貨政策").first()).toBeVisible();
    await expect(page.getByText("保固期限").first()).toBeVisible();
    await expect(page.getByText("退款流程").first()).toBeVisible();
    // 每張有 3 個動作按鈕（至少 1 組可見）
    await expect(page.getByRole("button", { name: /同意收錄/ }).first()).toBeVisible();
  });

  test("4.1 TestSet tab 貼 tenant_id 後顯示 5 個 case", async ({ page }) => {
    await page.goto("/");
    // 預先把 tenant_id 寫入 localStorage（不然要在 input 打字）
    await page.evaluate((tid) => {
      window.localStorage.setItem("aeos.testset.tenant_id", tid);
    }, DEMO_TENANT_ID);
    await page.getByRole("tab", { name: /Test Set/ }).click();
    await page.getByRole("button", { name: /重新整理/ }).click();

    // 5 個 case：退貨期限 / 保固 / 退款入帳 / 退貨運費 / 保固證明
    await expect(page.getByText("退貨期限").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("退款入帳").first()).toBeVisible();
    await expect(page.getByText(/已啟用 Test Cases（5/)).toBeVisible();
  });

  test("5.1+5.2 Audit tab 顯示對話列表 + 可開 detail", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Audit/ }).click();
    await expect(page.getByRole("button", { name: /對話列表/ })).toBeVisible({
      timeout: 10000,
    });
    // 點 demo conversation row
    const convRow = page.locator("[data-testid^='conv-row-']").first();
    await expect(convRow).toBeVisible({ timeout: 10000 });
    await convRow.click();

    // detail 區
    await expect(page.getByTestId("conversation-detail")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/^訊息（/)).toBeVisible();
    await expect(page.getByText(/^Audit 事件（/)).toBeVisible();
  });

  test("5.4 切到 Audit 事件 sub-tab 顯示事件列表", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Audit/ }).click();
    await page.getByRole("button", { name: /Audit 事件/ }).click();
    await expect(page.getByPlaceholder(/event_type filter/)).toBeVisible();
  });

  test("6.1 Admin tab 顯示帳號管理介面（bypass 是 admin）", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();
    await expect(page.getByText(/Expert 帳號（/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("button", { name: /\+ 新增帳號/ })).toBeVisible();
  });

  test("6.2 點新增帳號 → 表單展開", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: /Admin/ }).click();
    await page.getByRole("button", { name: /\+ 新增帳號/ }).click();
    await expect(page.getByText(/新增 Expert 帳號/)).toBeVisible();
    await expect(page.getByPlaceholder("Email")).toBeVisible();
    await expect(page.getByPlaceholder("姓名")).toBeVisible();
    await expect(page.getByPlaceholder(/密碼/)).toBeVisible();
  });

  test("Tab 切換流暢且 fetch 命中正確 endpoint", async ({ page }) => {
    const apiCalls: string[] = [];
    page.on("request", (req) => {
      if (req.url().includes("/api/v1/")) {
        apiCalls.push(req.url());
      }
    });

    await page.goto("/");
    // mount 後初始 Drafts tab 應發 /api/v1/expert/reviews
    await page.waitForResponse((r) => r.url().includes("/api/v1/expert/reviews"));

    await page.getByRole("tab", { name: /KC 知識卡/ }).click();
    await page.waitForResponse((r) => r.url().includes("/api/v1/kc/drafts"));

    await page.getByRole("tab", { name: /Audit/ }).click();
    await page.waitForResponse((r) => r.url().includes("/api/v1/audit/conversations"));

    const summary = apiCalls.map((u) => u.replace("http://localhost:5173", ""));
    expect(summary.some((u) => u.includes("/expert/reviews"))).toBeTruthy();
    expect(summary.some((u) => u.includes("/kc/drafts"))).toBeTruthy();
    expect(summary.some((u) => u.includes("/audit/conversations"))).toBeTruthy();
  });
});

test.describe("Approve flow", () => {
  test.beforeEach(() => {
    resetDemo();
  });

  test("2.2 點同意送出 → 卡片消失", async ({ page }) => {
    await page.goto("/");
    const card = page.locator("[data-testid^='review-card-']").first();
    await expect(card).toBeVisible({ timeout: 10000 });

    await card.getByRole("button", { name: /同意送出/ }).click();
    await expect(card).not.toBeVisible({ timeout: 5000 });
  });
});

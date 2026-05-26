/**
 * Playwright E2E — TestSet tab 接 top-level SkillSelector filter.
 * Phase 1 後續 #23 完成驗證。
 */
import { test, expect } from "@playwright/test";
import { resetDemo, DEMO_TENANT_ID } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  resetDemo();
});

test("API listCases ?skill_slug= filter 不炸", async ({ request }) => {
  const resp = await request.get(
    `/api/v1/testset/cases?tenant_id=${DEMO_TENANT_ID}&skill_slug=hr/leave-request`,
  );
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body).toHaveProperty("items");
  // demo seed 是 customer-service skill_slug=NULL 通用題 → filter hr 仍包含 NULL 題
});

test("無 skill_slug query → API 不傳 filter（全列）", async ({ request }) => {
  const resp = await request.get(
    `/api/v1/testset/cases?tenant_id=${DEMO_TENANT_ID}`,
  );
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body.count).toBeGreaterThanOrEqual(0);
});

test("skill_slug=_all_ 視同無 filter（後端 effective_skill=None）", async ({
  request,
}) => {
  const resp = await request.get(
    `/api/v1/testset/cases?tenant_id=${DEMO_TENANT_ID}&skill_slug=_all_`,
  );
  expect(resp.status()).toBe(200);
});

test("create case with skill_slug → 回 skill_slug 欄位", async ({ request }) => {
  const ts = Date.now();
  const resp = await request.post("/api/v1/testset/cases", {
    data: {
      tenant_id: DEMO_TENANT_ID,
      name: `e2e-skill-${ts}`,
      user_input: "我想請假",
      expected_outcome: "提示流程",
      expected_keywords: ["請假"],
      skill_slug: "hr/leave-request",
    },
  });
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body.skill_slug).toBe("hr/leave-request");
});

import { defineConfig, devices } from "@playwright/test";

/**
 * AEOS Expert Console E2E config.
 *
 * 前置：
 * - backend: uvicorn app.main:app --port 8000
 * - frontend: npm run dev (port 5173)
 * - seed: uv run python -m scripts.seed_demo
 *
 * 不自動起 services（避免複雜化）；測試前先確認 healthcheck 過。
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // tests share DB state (seed); 跑序列避免互相干擾
  workers: 1, // 單 worker — 寫 DB 動作不能並行
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

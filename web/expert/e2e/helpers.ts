/**
 * E2E helpers — 共用 setup / teardown utilities.
 *
 * 主要功能：呼叫 `scripts/seed_demo.py --reset` 把 demo tenant 重置成已知狀態。
 * 每個會改 DB 的 test 在 beforeEach 呼叫。
 */
import { execSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const DEMO_TENANT_ID = "9e7ffb09-4f53-475a-a771-29b02f04906a";

// __dirname workaround for ES modules
const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = resolve(dirname(__filename), "../../..");

/**
 * 呼叫 `uv run python -m scripts.seed_demo --reset` 把 demo state 還原。
 *
 * - 同步呼叫（用 execSync）；spec beforeEach 不需要等 promise
 * - cwd = repo root（避免 cwd 不對找不到 .venv）
 * - 失敗會 throw，整支 spec 中止
 */
export function resetDemo(): void {
  execSync("uv run python -m scripts.seed_demo --reset", {
    cwd: REPO_ROOT,
    stdio: "pipe", // 不污染 playwright reporter
    timeout: 30_000,
  });
}

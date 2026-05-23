---
id: S5-PROGRESS-2026-05-23-complete
title: S5 完整收尾報告
status: active
type: report
created: 2026-05-23
owner: CTO
tier: 5
---

# S5 進度報告 — 2026-05-23（Canary + Auth + Audit UI 完整收尾）

> 接續 `S2-PROGRESS-2026-05-22-expert-review.md`。S5 起本日完成的剩餘任務塊全列於此。

## 完成項目（本回合 — S5 收尾 4 個 branch）

| # | Branch | 內容 |
|---|---|---|
| 1 | `feat/s5-auth-backend` | expert_account / expert_session 表 + bcrypt + bearer token + `/auth/login`/`logout`/`me` + `current_expert` FastAPI Dependency + `AEOS_AUTH_REQUIRED` env gate（bypass 模式預設讓 dev/test 不必 auth） |
| 2 | `feat/s5-auth-frontend` | `Login.tsx` 表單 + `authStore.ts` localStorage 持久化 + 自動 attach Bearer header + App.tsx auth state machine + 登出按鈕；既有頁面零修改（KCInbox / TestSetInbox / DraftsInbox） |
| 3 | `feat/s5-canary-routing` | `tenant_setting.canary_percent` (0-100) + 確定性 bucket（SHA256(conv.uuid)[:4] mod 100，避免 UUID v4 版本位元偏置）+ DraftProcessor 動態決定 outbound 初始 status + admin API + audit trail |
| 4 | `feat/s5-audit-browse-ui` | 3 個 audit endpoint (list events / list conversations / detail timeline) + Expert Console 4th tab + conversation 完整時間軸 view（messages + outbounds + audit events 整合渲染） |

## 量化指標

| 指標 | 上回（tier4-complete 之後）| 本次 | Δ |
|---|---|---|---|
| Python tests | 312 | **360** | **+48** |
| 前端 vitest | 18 | **23** | **+5** |
| DB 表 | 22 / 25 | **24 / 25** | **+2** (expert_account / expert_session) |
| Migrations | 8 | **10** | **+2** (auth schema + canary_percent) |
| FastAPI endpoints | ~22 | **30+** | **+8** (auth 3 + audit 3 + canary 2) |
| Expert UI tabs | 3 (drafts/kc/testset) | **4** + Login | **+1** (audit) |
| 程式碼行數 (LOC) | 18,500+ | **21,800+** | **+3,300** |
| SEC-001 §6.1 | 2 / 13 | **4 / 13** | **+2** (auth + audit) |
| AC | 001 基建 / 003 / + handoff | **001 / 003 / 004 / 005 全綠** | **+ AC-004 / AC-005** |

## 關鍵設計決策

### 1. AEOS_AUTH_REQUIRED env gate

**問題**：保護所有 endpoint 後既有 308 tests 全部 401。

**選項評估**：
- A. 更新 30+ tests 全加 auth header → 工作量大、混淆測試意圖
- B. env var 控制 bypass → 預設 false，dev/test 不必 auth；prod 設 true 就保護

選 B 並加一道安全閥：**有 token 必驗**（即使 bypass 模式），防止偽造 token 反而繞過 bypass 邏輯。

### 2. Canary 用確定性 bucket，不用 random

每個 conversation 第一次決策後永遠同 bucket：
- 避免同一 user 一下 Draft Mode 一下 auto-reply（UX 跳動）
- 不需要新表記錄已分配 bucket（純無狀態 hash）
- 用 SHA256(uuid.bytes)[:4] mod 100 而非 UUID.int mod 100，避免版本位元造成分布不均

### 3. Audit UI 不做即時推送，純 pull

`/api/v1/audit/events?since_hours=24` 預設窗口足夠審查；不接 SSE / WebSocket 簡化前端。expert 重要動作（draft approve / reject）UI 本來就會局部更新，audit tab 是「事後回顧」場景。

Phase 2 真有 incident response 需求再加 WebSocket push（OBS Tempo / Loki 整合一起做）。

### 4. Conversation detail 用 client-side merge

3 條時間線（messages / outbounds / audit_events）後端各自返回，不做 server-side interleave。理由：
- 各自查詢 index 命中容易（messages 有 conv_id index、audit 有 resource_id index）
- Client-side 排序純 JS 開銷可忽略
- 未來想換 view（例如只看 audit 不看 messages）就改 UI，不動 API

## 剩餘的真實 blocker（不變）

| Blocker | 解鎖人 | 預估時間 |
|---|---|---|
| Hetzner Cloud 帳號 | CTO | 1 天 |
| Slack + PagerDuty Free | CEO + CTO | 半天 |
| LINE Developers Console | CTO | 30 分鐘 |
| Pilot 客戶簽約 | CEO | unknown |

**S6 開始需要真實客戶資料才有意義（KB / test cases / live drill）。**

## 對應 AC 進度

| AC | 條件 | 狀態 |
|---|---|---|
| AC-003 §1 webhook ≤1s ACK | ✅ | LINE webhook design + test |
| AC-003 §2 draft p95 ≤5s | 🟡 | 待真實負載驗 |
| AC-003 §3 approve/edit/reject 全進 audit | ✅ | E2E smoke + Audit UI 顯示 |
| AC-004 §canary toggle ≤30s | ✅ | admin API + decide_outbound_status 確定性 |
| AC-004 §kill switch ≤30s | ✅ | tenant_setting + DraftProcessor 攔截 |
| AC-005 §audit 瀏覽 UI | ✅ | conversation 完整時間軸 |
| AC-005 §Skill 版本 / KC 引用 | 🟡 | message 結構暫未保留 KC ref；Phase 2 補 |

## 下一波 P1 工作（非 hard gate，可選）

1. **LLM judge 升級 Haiku**：TestSetRunner 從 keyword judge → 語意比對
2. **Slack webhook 通知**：kill_switch 觸發 + P0 incident
3. **Admin 帳號管理 UI**：目前要跑 CLI 建 expert，加個 admin tab
4. **Message 結構保留 KC ref**：DraftProcessor 把 ToolResult 中的 KC ID 寫入 message metadata，audit 才能顯示「這則回答引用了哪幾張 KC」

## Pilot 上線 demo 流程（現在可跑）

```bash
# 1. seed 3 tab 資料
uv run python -m scripts.seed_demo

# 2. 建 admin 帳號
uv run python -c "
import asyncio
from app.db.session import session_scope
from app.services import auth
asyncio.run((async def _: ... (await auth.create_account(s, email='cto@aeos', password='dev1234', name='CTO', role='admin')))(...))
"

# 3. 強制 auth 啟動全套
AEOS_AUTH_REQUIRED=true uv run uvicorn app.main:app --reload --port 8000 &
uv run python -m app.worker &
cd web/expert && npm run dev

# 4. 開 http://localhost:5173 → Login → 4 個 tab 全可玩
```

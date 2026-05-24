---
id: S5-PROGRESS-2026-05-24-p1-complete
title: P1 全部收尾報告 — Admin UI / KC refs / PII masking
status: active
type: report
created: 2026-05-24
owner: CTO
tier: 5
---

# P1 全部收尾報告（2026-05-24）

> 接續 `S5-PROGRESS-2026-05-24-llm-judge-slack.md`。
> **Phase 1 code 階段進無可進** — 剩全部外部 blocker。

## 完成項目（本回合 3 個 branch）

| # | Branch | 內容 |
|---|---|---|
| 1 | `feat/s5-admin-accounts-ui` | Admin 帳號管理 — list/create/disable/enable 4 endpoint + Expert Console 第 5 個 tab (admin role only); disable 同步 revoke active sessions |
| 2 | `feat/s5-message-kc-refs` | DraftProcessor 收集 tool 呼叫紀錄 → message.tool_invocations JSONB；Audit UI 渲染「引用 N 張 KC」chip — **AC-005 §2 完整** |
| 3 | `feat/sec-pii-masking` | webhook ingress PII 過濾 — 6 種 pattern + Luhn 驗證；raw PII 不進 DB / log + audit + Prometheus counter — **SEC-001 §6.1 #11** |

## 量化指標

| 指標 | 上回（LLM judge + Slack） | 本次 | Δ |
|---|---|---|---|
| Python tests | 381 | **408** | **+27** |
| 前端 vitest | 23 | **29** | **+6** |
| 總 tests | 404 | **437** | **+33** |
| LOC（app） | 8,180 | 8,515 | +335 |
| LOC（tests） | 8,900 | 9,410 | +510 |
| LOC（web/expert/src）| 3,170 | 3,770 | +600 |
| `dev` merge commits | 22 | **28** | +6 |
| Expert UI tabs | 4 | **5** | +1 (admin) |
| SEC-001 §6.1 | 4 / 13 | **5 / 13** | +1 (#11 PII) |
| mypy source files | 151 | **155** | +4 |

## 關鍵設計

### Admin 帳號 UI — Defense in Depth

`require_admin` dependency chain：
1. `current_expert`（從 Bearer token 解析）
2. 檢查 `role == 'admin'`，否則 403

**disable 動作同步 revoke active sessions**（DELETE FROM expert_session）——
避免已登入 token 在 disable 後還能用。Frontend 端，admin tab 只在
`expert.role === 'admin'` 才 render TabButton，雙重保護（UI 與 API）。

### Message tool_invocations — AC-005 §2 收尾

DraftProcessor 在 dispatch 處用 closure 收集本 turn 所有 tool 呼叫：

```python
async def _dispatch(name, args):
    result = await tool_exec.dispatch(name, args, ctx=tool_ctx)
    record = {
        "name": name,
        "input": _sanitize_input(args),  # 去掉 query_embedding
        "ok": result.error_message is None,
        "kc_refs": _extract_kc_refs(name, result.output),  # search_knowledge → list[kc_id]
    }
    tool_invocations.append(record)
    return result.output
```

寫進 message 表時用 `CAST(:ti AS JSONB)`，向後相容（舊 row 仍是 `'[]'`）。

### PII masking — Pattern + Luhn 雙層

6 種 regex pattern，順序設計避免長吞短：
1. email（特定，最少 false positive）
2. 台灣手機 / 市話
3. 台灣身分證
4. 信用卡（**Luhn 驗證**過濾假陽性 — "1234567890123" 13 位但 Luhn fail 不算卡號)
5. bank_like 連續 8-12 位數字（兜底）

**raw PII 永遠不進 DB**：webhook 收到 → mask_text → INSERT masked + audit pii.redacted_in_ingress。Expert UI / Audit UI / LLM 看到的全是 `[REDACTED:type]`。

## SEC-001 §6.1 進度：5 / 13

剩 8 條需外部資源或合規流程：
- container image scan（待 Dockerfile）
- 紅隊 pentest
- DPA / Privacy notice / Cookie consent
- incident drill（每月一次）
- TLS prod 部署（待 Hetzner）
- backup PITR drill
- secrets rotation policy
- access log retention 12 月

## Phase 1 code 階段全部清完

純技術上：
- 4 個 AC 全綠（AC-001 / 003 / 004 / 005）
- Expert Console 5 tab 全可用
- Worker 4 polling cycles 全跑通
- Auth + canary + kill switch + audit + PII masking 全 production-ready
- 28 支 branch 合入 dev / `main` 暫不動

## 剩全部外部 blocker

| Blocker | 解鎖人 | 解鎖後立即可做 |
|---|---|---|
| Hetzner Cloud 帳號 | CTO | infra/observability/ → Grafana / TLS / production deploy |
| Slack workspace + PagerDuty | CEO + CTO | kill switch 通知活化 + oncall |
| LINE Developers Console | CTO | 真實 HMAC + ngrok end-to-end smoke |
| Pilot 客戶簽約 | CEO | S6 真實 KB ingest + test set + S7 上線 |

下一步建議排程：CTO 優先處理 Hetzner（解鎖 infra）；CEO 同步推 pilot 簽約。

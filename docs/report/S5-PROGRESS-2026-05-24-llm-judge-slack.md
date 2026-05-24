---
id: S5-PROGRESS-2026-05-24-llm-judge-slack
title: S5+ P1 進度 — LLM judge + Slack 通知
status: active
type: report
created: 2026-05-24
owner: CTO
tier: 5
---

# S5+ P1 進度報告（2026-05-24）

> 接續 `S5-PROGRESS-2026-05-23-complete.md`。S5 hard gate 之外的 P1 工作。

## 完成項目（本回合 2 個 branch）

| # | Branch | 內容 |
|---|---|---|
| 1 | `feat/s3-llm-judge` | `Judge` Protocol + `KeywordJudge` / `LLMJudge`（Haiku 4.5 語意比對）；可注入 TestSetRunner；LLMJudge 自帶 keyword fallback（LLM 失敗不炸 test run）|
| 2 | `feat/s5-slack-notifications` | `app/services/notifications.py` best-effort webhook；接 kill_switch + outbound permanent fail；未設 `SLACK_WEBHOOK_URL` silently skip |

## 量化指標

| 指標 | 上回（S5 complete） | 本次 | Δ |
|---|---|---|---|
| Python tests | 360 | **381** | **+21** |
| 前端 vitest | 23 | 23 | 0 |
| LOC（app） | 7,900 | 8,180 | +280 |
| `dev` merge commits | 20 | **22** | +2 |
| Mypy source files | 148 | 151 | +3 |

## 關鍵設計

### LLM Judge — 容錯三層防禦

1. **Structured JSON prompt**：明確要求 `{"score": 0~1, "reason": "<80 字"}`，不要 markdown
2. **容錯 parser**：用 regex 抓 `{...}` 區段，即使 LLM 加 ```json``` wrapping 也能解
3. **`keyword_fallback_on_error=True`**：LLM API down / JSON 解析失敗 → 自動降級為 KeywordJudge，reason 標明 `[llm-judge failed → keyword fallback]`

→ TestSet pass rate 量測**不會**因為 judge LLM 暫時 outage 而炸掉。

### Slack notifications — best-effort 原則

`notify_slack()` 對失敗保持沉默：
- 未設 `SLACK_WEBHOOK_URL` → skip + debug log
- HTTP 5xx / network error → log warning + 回 `False`
- **不 raise**

→ kill switch / outbound 業務流不受 Slack 可用性影響（通知不是業務 invariant）。

## 接點清單（之後加 alert 照樣式擴）

```python
await notify_slack(
    severity="P0" | "P1" | "P2" | "info",
    title="短標題",
    message="主說明",
    fields={"k": "v", ...},  # optional Slack attachment fields
)
```

目前接點：
- `kill_switch.disable_ai` → P0
- `kill_switch.enable_ai` → info
- `OutboundProcessor._fail_permanent` → P1

之後可加：
- `KbIngestProcessor._fail` → P1
- `audit.idle_drift_detected`（Phase 2 偵測 audit 異常 pattern）

## 剩 P1 工作

| 項目 | 預估 | 性質 |
|---|---|---|
| Admin 帳號管理 UI（取代 CLI 建帳號） | 1 天 | DX |
| Message metadata 加 KC ref（Audit UI 顯示引用了哪幾張 KC） | 1 天 | AC-005 §2 完整度 |
| SEC-001 §6.1 PII masking（webhook + LLM 前後）| 2 天 | 合規 hard gate |
| Daily digest email（對話數 / handoff 率 / cost） | 半天 | 待 Slack/SES |
| D3 cost dashboard | 半天 | 待 Hetzner 部署 |

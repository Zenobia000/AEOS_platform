---
id: API-002
title: LINE Webhook Integration Contract
status: active
type: api-contract
created: 2026-05-14
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CTO
tier: 2
related: [SAD-v0.1, UF-003, UF-004, SF-003, SF-004, ADR-0005]
---

# API-002 — LINE Messaging API Integration

> AEOS 與 LINE Platform 的雙向整合。Phase 1 唯一 channel。
> 官方參考：https://developers.line.biz/en/docs/messaging-api/

## 1. Architecture Position

```
LINE Platform ⇄ AEOS API (/webhooks/line/{channel_id})
                  ↓ enqueue
                Worker
                  ↓ LINE Messaging API (push/reply)
                LINE Platform → End User
```

**兩個方向**：
- **Inbound**（LINE → AEOS）：webhook，AEOS 收訊息
- **Outbound**（AEOS → LINE）：呼叫 LINE Push/Reply API 送訊息

## 2. Setup（客戶 onboarding 時做）

| Step | Owner | 動作 |
|---|---|---|
| 1 | 客戶 | 申請 LINE Official Account + Messaging API channel |
| 2 | 客戶 | 取得 `Channel ID`、`Channel Secret`、`Channel Access Token`（long-lived） |
| 3 | 客戶 | 在 LINE Developers Console 設 Webhook URL = `https://{slug}.aeos.app/api/v1/webhooks/line/{channel_id}` |
| 4 | 客戶 | Enable "Use webhook"、Disable "Auto-reply messages"、Disable "Greeting messages"（或自訂） |
| 5 | AEOS | 經 POST `/employees/{id}/channels`（見 API-001 §2）寫入加密保存 |
| 6 | AEOS | 點 LINE Console "Verify" 按鈕 → AEOS webhook 須回 200 |

## 3. Inbound Webhook

### Endpoint
`POST /api/v1/webhooks/line/{channel_id}`

### Headers
| Header | 必要 | 用途 |
|---|---|---|
| `X-Line-Signature` | ✅ | HMAC-SHA256(channel_secret, body) base64；**必驗** |
| `Content-Type` | ✅ | `application/json` |

### Verification
```python
import hmac, hashlib, base64
def verify(body_bytes: bytes, sig_header: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(sig_header, expected)
```
驗證失敗 → 立即 `403 Forbidden` + audit `WEBHOOK_SIG_INVALID`，**不進處理**。

### Request Body（LINE 標準）
```json
{
  "destination": "U01234...",
  "events": [
    {
      "type": "message",
      "message": { "type": "text", "id": "1234", "text": "你好" },
      "timestamp": 1462629479859,
      "source": { "type": "user", "userId": "Uabcd..." },
      "replyToken": "0f3779fba3b349968c5d07db31eabf65",
      "mode": "active",
      "webhookEventId": "01H...",
      "deliveryContext": { "isRedelivery": false }
    }
  ]
}
```

### Phase 1 處理的 event types
| event.type | message.type | 處理 |
|---|---|---|
| `message` | `text` | 主要處理路徑 — 進 SF-003 / SF-004 |
| `message` | `image` / `video` / `audio` / `file` / `sticker` / `location` | Phase 1 回 fallback「我目前只看得懂文字訊息」 |
| `follow` | — | 記錄 end_user_pseudo_id；optional welcome message |
| `unfollow` | — | mark conversation outcome=`abandoned` |
| `postback` | — | Phase 1 不用（無 rich menu / quick reply 互動） |
| `join` / `leave` / `memberJoined` / `memberLeft` | — | ignore（不接群組） |

### Response（必須 ≤ 1 秒）
`200 OK`，body 任意（LINE 不檢）。
- 處理流程：**驗簽 → INSERT message(role=user) → INSERT audit MESSAGE_RECEIVED → enqueue Redis → return 200**
- 真正的 LLM 處理在 Worker，**絕不**在 webhook 內同步呼叫 LLM

### Idempotency
- LINE 可能 redeliver（`deliveryContext.isRedelivery=true`）
- 用 `webhookEventId` 做 dedup（DB unique constraint）
- 已處理過 → 仍回 200，**不**重複處理

### Rate Limit
LINE 入站不限速，但我們：
- 單 IP > 1000 req/min → drop + alert（疑似攻擊）
- 單 channel > 100 訊息 / 分鐘 → 仍處理但 alert（疑似 spam）

## 4. Outbound — Push / Reply

### 4.1 Reply（30 秒內有效）
LINE 提供 `replyToken`，30 秒內可用一次。
```
POST https://api.line.me/v2/bot/message/reply
Authorization: Bearer {channel_access_token}
Content-Type: application/json

{ "replyToken": "<from webhook>",
  "messages": [ { "type": "text", "text": "..." } ] }
```

Phase 1 策略：**主流程用 Push API**，不依賴 replyToken（因 Draft Mode 可能 > 30 秒才送）。

### 4.2 Push（任意時間，計費）
```
POST https://api.line.me/v2/bot/message/push
Authorization: Bearer {channel_access_token}

{ "to": "U<userId>",
  "messages": [ { "type": "text", "text": "..." } ] }
```

### 4.3 Message types（Phase 1）
| type | 用 | Notes |
|---|---|---|
| `text` | 100% | 5000 字上限；含 emoji 可 |
| `image` | 否 | Phase 2 才用 |
| `template` (quickReply / confirm / buttons) | 選用 | 簡化 handoff yes/no 選項 |
| `flex` | 否 | Phase 2 |

### 4.4 Rate Limit & Retry
- LINE Free / Verified plan：每月 push 配額；超過 → 429
- AEOS 策略：
  - 429 → backoff 60s → retry 2 次
  - 5xx → backoff exp(2, 4, 8) → retry 3 次
  - 仍失敗 → DLQ + alert + audit `LINE_PUSH_FAILED`
  - 終端使用者**看不到 error**（透過 fallback 文案：「客服稍後回覆」）

### 4.5 Quota Monitoring
- 每日 cron：GET `https://api.line.me/v2/bot/message/quota/consumption` → 寫入 daily stats
- 使用率 > 80% → alert CEO（要升級 plan 或 throttle）

## 5. End User Identity

| LINE 提供 | AEOS 內 |
|---|---|
| `userId` (32-char `U` prefix) | hash → `end_user_pseudo_id` (SHA-256 + tenant salt) |
| `displayName` (optional via Profile API) | 可選性 fetch；**不存原文**；存 hashed 或不存 |
| 頭像 / 狀態訊息 | 不抓不存 |

**原則**：LINE userId 是 pseudonymous identifier；我們 hash 後再存，加 tenant-specific salt 確保跨 tenant 不可關聯。

## 6. Profile Fetch
若需要 displayName（e.g. 客服說「您好，X 先生」）：
```
GET https://api.line.me/v2/bot/profile/{userId}
Authorization: Bearer {token}
```
- 結果 ttl 24h cache（Redis）
- displayName 進 LLM context 時走 pseudonymize（見 ADR-0005）

## 7. 失敗模式與緩解

| 失敗 | 緩解 |
|---|---|
| Webhook 簽章漏設或錯 secret | startup health check 驗一遍；錯則服務啟動失敗（fail fast） |
| LINE 端 webhook 失效（disable） | 客戶 onboarding checklist 含 verify 步驟；定期 readyz 探測 |
| Channel Access Token 過期 / rotate | 重新 issue → 客戶通知 AEOS → 更新加密 config；舊 token 失效偵測 → alert |
| LINE 服務中斷 | webhook ACK 仍 200（內部記）；push retry；fallback 訊息僅在恢復後送 |
| User block AEOS OA（unfollow） | mark conversation outcome=abandoned；不再嘗試 push |

## 8. Phase 2+ extensions（不在 Phase 1）

- Rich menu / quick reply / flex message
- 多 channel（multiple LINE OA per tenant）
- LINE Login / LIFF（深度 LINE App 整合）
- LINE Notify 給 Expert（**Phase 1 已用** — only as notification channel for Draft Inbox）
- 多媒體（圖、語音）處理

## 9. 連結
- 對應 user flow：`UF-003 (Draft Mode)`, `UF-004 (Canary auto reply)`
- 對應 system flow：`SF-003`, `SF-004`
- PII 規範：`ADR-0005`
- 整體架構位置：`SAD-v0.1.md` §3

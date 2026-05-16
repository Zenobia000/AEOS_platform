---
id: PLAYBOOK-001
title: Customer Support Escalation Playbook
status: active
type: playbook
created: 2026-05-15
last-synced-with: c22ad6cf305b5f5efeb2e2b2c998606181709f0b
owner: CEO + CTO
tier: 3
related: [PILOT-001, AC-001-to-005, NFR-001, RUNBOOK-001, ADR-0009]
---

# PLAYBOOK-001 — 客服升級流程

> 「**AI 答不出來才是客戶最在意的時刻。**」AI 永遠會錯，問題是錯之後怎麼接。本 playbook 定義三層升級：AI → AI 自信度低 escalate → 人類介入 → 內部 SRE。

## 1. 升級三層架構

```
┌────────────────────────────────────────────────────────┐
│ Layer 0: AI Auto-Reply（90%+ 對話）                    │
│   - Confidence ≥ 0.8                                    │
│   - 在 KB 知識範圍                                       │
│   - 無 guardrail trigger                                │
└────────────────────────────┬───────────────────────────┘
                             ▼
              ┌──────────────────────────┐
              │ Confidence < 0.8?         │
              │ 超出 KB?                  │
              │ Guardrail trigger?        │
              │ User 表達不滿?            │
              └────┬─────────────────────┘
                   │ Yes
                   ▼
┌────────────────────────────────────────────────────────┐
│ Layer 1: Tenant 客服介入（Tenant CS Agent）             │
│   - AI 回「我幫您轉接客服」+ 在後台 alert                │
│   - SLA: 工作時間 5 分鐘 / 非工作時間隔日                 │
│   - Tenant CS 看完整對話 context + AI 建議草稿            │
└────────────────────────┬───────────────────────────────┘
                         ▼
            ┌────────────────────────────┐
            │ Tenant CS 無法解決?         │
            │ 系統 bug?                   │
            │ 客戶要終止 / 合約問題?       │
            └────┬───────────────────────┘
                 │ Yes
                 ▼
┌────────────────────────────────────────────────────────┐
│ Layer 2: AEOS 內部支援（CS / Engineering）              │
│   - Tenant 透過 #aeos-support channel / email           │
│   - SLA 依 ticket severity                              │
│   - 我方 CS / Eng 直接看 OBS-001 + 介入                  │
└────────────────────────────────────────────────────────┘
```

## 2. AI → 人類 Escalation 觸發條件（Layer 0 → Layer 1）

對應 AC-003（不確定時正確 escalate ≥ 95%）。

### 2.1 自動觸發

| 條件 | 實作 |
|---|---|
| Agent confidence score < 0.8 | LLM 回覆含 `confidence` 自評；RAG retrieval score 加權 |
| 超出 KB 範圍 | RAG 無相關 chunk（score < threshold）|
| Guardrail trigger | PII echo / 政治 / 醫療 / 法律 / 投訴 / 退款 / 訴訟關鍵字 |
| User 表達不滿（情緒分析） | Negative sentiment > 0.7 連續 2 輪 |
| User 主動要求人工 | 偵測「找真人 / 客服 / 人工 / 接通 / 轉接」等關鍵詞 |
| Agent 工具呼叫失敗 | API error / timeout / unavailable |
| 同一對話超過 5 輪未解決 | 計數器 |
| 涉及金額 > $500 / 涉及人身安全 | Keyword + amount detection |

### 2.2 Escalation 動作

```python
# pseudo-code
def escalate(conversation, reason: EscalationReason):
    # 1. AI 給友善過渡訊息
    send_to_user(
        "了解您的需求，我幫您轉接專業客服協助處理，請稍候。"
    )
    # 2. 後台告警（tenant 後台 + Slack 至 tenant 設定 channel）
    create_ticket(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        reason=reason,
        ai_summary=generate_summary(conversation),
        ai_suggested_response=draft_response(conversation),
        priority=infer_priority(reason),
    )
    # 3. 對話狀態切換
    conversation.state = "escalated_to_human"
    # 4. AI 停止主動回覆，但仍可被 tenant CS 召喚 (sidekick mode)
    # 5. 寫入 audit (escalation event)
```

### 2.3 Tenant CS 介面

Tenant 後台應提供：

- **未處理 escalation 隊列**（依 priority + age 排序）
- **完整 context**：對話原文 + AI 建議草稿 + KB 引用 + 信心分數
- **動作**：傳訊息 / 標記為解決 / 升回 AEOS / 訓練 AI（補入 KB）
- **SLA 倒數**：剩餘時間醒目顯示

## 3. Tenant 無法解決 → AEOS（Layer 1 → Layer 2）

### 3.1 Tenant 發起 Ticket 渠道

| 渠道 | SLA | 用途 |
|---|---|---|
| **Slack Connect channel**（共享） | 工時內 1 hour | 一般問題 |
| **support@aeos.<domain>** | 工時內 4 hour | 較複雜 |
| **Emergency phone**（CEO） | 24/7 內 1 hour | P0 only |

### 3.2 Ticket 分級

| Severity | 定義 | Response SLA | Resolution SLA |
|---|---|---|---|
| **S1** | 服務全停 / 全 tenant 對話無法處理 / 資料疑似洩漏 | 15 min | 4 hour（止血） |
| **S2** | 單一核心功能無法使用 / 影響 > 20% 對話 | 1 hour | 1 工作日 |
| **S3** | 部分功能異常 / 可繞過 | 4 hour | 5 工作日 |
| **S4** | UX / 報表 / 文件問題 | 1 工作日 | 下個 sprint |

S1 = RUNBOOK-001 P0；S2 ≈ P1；S3 ≈ P2；S4 ≈ P3。

### 3.3 Ticket Handling Flow（AEOS 內部）

```
1. CS 接 ticket → 5 min 內 ack（含工時外）
2. Triage：
   - S1/S2 → 立即進 #incidents channel + 通知 oncall
   - S3 → assign 給 eng；24h 內回覆
   - S4 → backlog
3. 處理：
   - Bug → 修 + 部署（RUNBOOK-002）
   - 設定問題 → 後台改 + 教育 tenant
   - 預期行為但 tenant 不滿 → CTO + CEO 評估是否改 product
4. 解決：
   - 通知 tenant + 驗證
   - 24h follow-up 確認穩定
   - RCA（S1/S2 強制；S3 視情況）
```

### 3.4 Communication Cadence

| Severity | 通報頻率 |
|---|---|
| S1 | 每 30 分鐘 status update |
| S2 | 每 2 小時 |
| S3 | 每日進度 |
| S4 | 每週進度（含在 weekly digest） |

## 4. 常見場景 Playbook

### 4.1 「AI 答錯了，客戶很生氣」（最常見）

```
1. Tenant CS 在後台看對話 + AI 引用
2. 確認：是 AI 推理錯？KB 內容過時？Prompt 沒涵蓋此 case？
3. 如是 KB 過時 → tenant 自助更新 KB
4. 如是 prompt 不涵蓋 → tenant 在後台加 "guidance"
5. 如是 AI 推理錯（明明 KB 有正確答案）：
   - 將此對話加入 test set
   - 通報 AEOS（S3 ticket）
   - 跑 test set 比較不同 prompt 版本
   - ADR-0009 §4 A/B test 新 prompt
6. Tenant CS 回覆客戶 + 標 resolved
```

### 4.2 「客戶投訴隱私問題」（敏感）

```
1. Tenant CS 立即 escalate AEOS（S1 if PII 涉嫌洩漏）
2. AEOS 啟動 RUNBOOK-001 §4.4 PII 處理流程
3. 並行：CEO 與 tenant 法務溝通
4. 客戶溝通：書面正式回覆 + 法定通報（如適用）
5. 72 小時內依 LEGAL-001 §8 完成通報
```

### 4.3 「客戶要求退款 / 合約終止」

```
1. Tenant CS 紀錄請求
2. 升級 CEO（24h 內回覆）
3. CEO 評估：
   - 確認問題真實性
   - 是否觸發 PILOT-001 K1~K4 kill criteria
   - 商業評估退款 / 抵扣 / 補救方案
4. 書面確認 + 執行
5. 如終止：啟動 LEGAL-001 §6 資料返還流程
```

### 4.4 「客戶 LINE Webhook 設定錯」

```
1. Tenant CS 在後台「健康檢查」工具自助診斷
2. 不會修 → AEOS CS 介入（S3 ticket）
3. AEOS CS：
   - 看 webhook handler logs（OBS-001 D2）
   - 確認 LINE side 設定（HMAC secret, URL）
   - 提供詳細步驟
4. 驗證：發測試訊息 + 看 trace
```

### 4.5 「終端使用者騷擾 / 違規」

```
1. Tenant CS 確認對話（如有不雅內容、違法請求）
2. Tenant 可在後台 block 該 LINE user
3. 嚴重情況（恐嚇、未成年內容）→ tenant 自行報警
4. AEOS 不主動介入 end-user 行為（隱私邊界）
```

## 5. 後台介面要求（給開發參考）

Tenant 後台必有的客服 console：

- **Escalation Inbox**：未處理升級隊列
- **Conversation Inspector**：可查任一對話 + AI 推理 trace
- **AI Brain View**：當前 prompt 版本 + KB 索引狀態 + guardrail 設定
- **Health Check**：webhook 連通性 / KB ingest 狀態 / quota 使用
- **Manual Reply**：人工接管對話介面
- **KB Editor**：直接編輯 / 上傳 KB
- **Test Drive**：在 sandbox 與 AI 對話測試
- **Support Ticket Submitter**：開 ticket 給 AEOS

## 6. 反饋迴圈

### 6.1 從 Escalation 學習

每週五 30 分鐘 review：
- 上週 escalation 數 vs 上上週
- Top 3 escalation reason
- 哪些 escalation 可以變成 prompt / KB 改進
- 哪些是新的 edge case 需要加入 test set

### 6.2 從 Ticket 學習

每月一次：
- 各 severity ticket 趨勢
- 重複出現的 ticket 類型 → 是否需 product 改動
- SLA 達成率

## 7. SLA 量測

進 OBS-001 D1 dashboard：

| Metric | 目標 |
|---|---|
| Layer 1 SLA hit rate（工時 5min） | ≥ 95% |
| Layer 2 S1 SLA hit rate | 100% |
| Layer 2 S2 SLA hit rate | ≥ 95% |
| Escalation rate（總對話 → escalation） | ≤ 30%（Pilot 末期目標） |
| Escalation correctness（該 escalate 卻沒 / 不該 escalate 卻 escalate） | ≥ 95%（AC-003） |
| Average resolution time per severity | trend 持平或下降 |

## 8. 對 Pilot 客戶的承諾（合約用）

寫入 SOW（LEGAL-002 範本）：

- Pilot 期內，每 tenant 享:
  - Layer 1 工具完整功能
  - Layer 2 直接 channel（Slack Connect + email）
  - 每月 1 次 30 分鐘 sync call（CTO/CEO 親自出席）
  - 任何 S1/S2 事故，48 小時內提供 RCA
  - 每月 health report（KPI + 改進建議）

## 9. 工具

| 用途 | 工具 |
|---|---|
| Ticket 系統 | Linear（Phase 1 簡用） / Jira（Phase 2） |
| Tenant CS console | AEOS admin console |
| 我方內部 | Slack #aeos-support + GitHub Issues |
| Status page | Better Uptime（如 deploy）|

---

**See also**:
- `AC-003` in `AC-001-to-005-acceptance-criteria.md` — Escalation correctness 驗收
- `RUNBOOK-001-incident-response.md` — S1/S2 對應的內部事故流程
- `ADR-0009-prompt-versioning.md` — 從 escalation 學習改 prompt 流程
- `PILOT-001-success-criteria.md` — Escalation 相關 KPI
- `LEGAL-002-SOW-template.md` — SLA 寫入合約
- `OBS-001-observability-spec.md` — Escalation metrics

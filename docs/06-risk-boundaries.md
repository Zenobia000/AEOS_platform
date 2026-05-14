# 風險、合規與邊界

> **本檔對應原 whitepaper.md 的 §11, §15, §31**
> 主題定位：風險管理
> 最後同步：2026-05-14

## 相關章節速查

**本檔被外部引用的高頻章節**：
- §11 安全與合規 (七層安全模型 / 法遵框架對應 / PII 治理 / 客戶資料生命週期 / 一鍵停用)
- §15.3 五方責任歸屬 (Tenant / Skill Owner / Platform / Tool Provider / LLM Provider)
- §31 不採納清單

**本檔對外引用的章節**：
- §5.4 三平面分離 (見 `02-product-architecture.md`)
- §13 多模型策略 (見 `02-product-architecture.md`)
- §15 風險矩陣與安全事件響應應用至 §28 假設驗證的黑帽分析 (見 `05-investor-thesis.md`)

---

## 11. 安全與合規

### 11.1 七層安全模型

```
Layer 7  Compliance        ← GDPR / PDPA / HIPAA / SOC 2 / ISO 27001
Layer 6  Audit & Forensics ← 完整可追溯、可重播
Layer 5  Policy & RBAC     ← 業務規則、角色權限
Layer 4  Data Protection   ← PII Masking、Encryption at Rest/Transit
Layer 3  Tool Gateway      ← 工具閘道、Sandbox
Layer 2  Identity          ← 多租戶、多用戶、Service Account
Layer 1  Network           ← VPC、Private Endpoint、WAF
```

### 11.2 法遵框架對應

| 法規 / 標準 | AEOS 必備能力 |
| :--- | :--- |
| **GDPR** (EU) | Right to Access、Right to Erasure、Data Portability、DPO 報表 |
| **PDPA** (TW / SG) | 個資告知、目的限制、保存期限、刪除請求 |
| **HIPAA** (US 醫療) | PHI Encryption、Minimum Necessary、Audit Log |
| **SOC 2 Type II** | Logical Access Control、Change Management、Incident Response |
| **ISO 27001** | ISMS、Risk Assessment、Asset Inventory |
| **EU AI Act** | High-risk AI System Documentation、Human Oversight、Risk Management |
| **NIST AI RMF** | Map / Measure / Manage / Govern |

### 11.3 PII 治理

```
Customer Input
    ↓
PII Detector (entity recognition)
    ↓
Classification (PII / Sensitive PII / SPI)
    ↓
Decision Matrix:
    - Mask in Display
    - Mask in Memory
    - Mask in Logs
    - Encrypt at Rest
    - Tokenize
    - Reject
    ↓
Policy Enforcement
```

### 11.4 客戶資料生命週期

| 階段 | 治理動作 |
| :--- | :--- |
| Collect | 取得明確同意、記錄目的 |
| Store | 加密、租戶隔離 |
| Process | 最小必要原則、PII Masking |
| Memory | 預設不存個資；如需暫存，TTL ≤ Session |
| Audit | 寫入 Append-only Log |
| Delete | 收到刪除請求 → 30 天內完成 (含備份) |
| Retention | 依法規與商業需求設定 |

### 11.5 安全事件響應

```
事件偵測 (Drift / Anomaly / Manual Report)
    ↓
分級 (P0 / P1 / P2)
    ↓
P0 (高風險): 立即停用相關 Employee + Skill
P1 (中風險): 隔離 + 限流 + 告警
P2 (低風險): 紀錄 + 排查
    ↓
根因分析 (RCA)
    ↓
修復 → Sandbox 驗證 → 重新發布
    ↓
事後報告 + Skill / Policy 更新
```

### 11.6 「一鍵停用」原則

任何 AI 員工、任何 Skill 版本、任何 Tool，必須支援：

- **一鍵停用** (Soft Disable)：立即停止接受新流量
- **一鍵下線** (Hard Disable)：移除並通知運營
- **一鍵回滾** (Rollback)：回到上一個 Approved 版本

**理由**：當事故發生時，分秒必爭。**沒有 Kill Switch 的 Agent 系統不該上線**。

---

## 15. 風險與緩解

### 15.1 技術風險矩陣

| 風險 | 機率 | 影響 | 緩解 |
| :--- | :--- | :--- | :--- |
| LLM API 中斷 | 中 | 高 | 多 Provider Fallback、Local Model 備援 |
| Prompt Injection 突破 | 高 | 高 | 紅隊持續、輸出過濾、Tool Gateway 把關 |
| Cross-tenant 資料外流 | 低 | 極高 | Policy 預設 deny、Tenant ID 強制注入、定期稽核 |
| Skill 版本退化 | 中 | 中 | Canary Release、自動回滾、Regression Test |
| Cost 失控 | 高 | 中 | Quota、Circuit Breaker、Cost Attribution |
| MCP Server 漏洞 | 中 | 高 | Sandbox、依賴掃描、版本鎖定 |
| 訓練資料污染 | 中 | 高 | Strict Labeling、Multi-source Cross-validation |
| 模型供應商單一依賴 | 高 | 高 | 多模型抽象層、Local Fallback |

### 15.2 業務風險矩陣

| 風險 | 緩解 |
| :--- | :--- |
| 客戶不信任 AI 員工 | 透明標示「AI 服務」、人工接手隨時可用、Audit Trail 可提供客戶 |
| 法務責任不清 | DPA / 服務契約明確責任邊界、強制 Human-in-the-loop |
| 監管不確定 | 模組化合規層、可關閉自我學習 |
| 員工抵觸 | AI 員工定位為「協作」非「取代」、提供 Trainer / Reviewer 新職位 |
| 競爭加劇 | 護城河在治理體系與企業整合，非單一 Bot |

### 15.3 倫理與責任歸屬框架

> **draft 缺漏的章節**。AI 員工出事時，誰負責？這是企業無法迴避的問題。

| 角色 | 責任 |
| :--- | :--- |
| **Tenant (客戶企業)** | 業務決策、Policy 設定、Skill 採用、最終回應 |
| **Skill Owner** | Skill 內容正確性、回歸測試、版本決策 |
| **Platform Provider (你)** | Runtime 穩定性、Tool Gateway 安全、Audit 完整 |
| **Tool Provider** | MCP Server 邏輯正確性、SLA |
| **LLM Provider** | 模型輸出符合契約 |

**契約建議**：DPA + SLA + Liability Cap + Indemnification Clauses 必須涵蓋上述五方責任。

---

## 31. 不採納清單 (Non-goals)

明確列出 **AEOS 不做** 的事，避免邊界蔓延：

| 不做 | 理由 |
| :--- | :--- |
| 通用 AGI / 對話聊天機器人 | AEOS 是企業勞動力平台，不是消費級 Chatbot |
| 取代人類客服 | AEOS 是「協作」與「擴展」，不是「替代」 |
| 自有 LLM 模型訓練 | 模型應由 LLM Provider 提供；AEOS 專注治理 |
| 通用 BI / 資料分析平台 | AEOS 提供 AgentOps，不取代 BI |
| 通用 Workflow / BPM 平台 | AEOS 的 Workflow 服務於 AI 員工，不做通用 BPM |
| 通用 IAM / SSO 平台 | 整合既有 IAM (Okta / Azure AD)，不自建 |
| Hardware Edge / IoT 終端 | 聚焦軟體層 |
| 一次性整合所有企業系統 | MVP 階段嚴格控制整合範圍，避免無底洞 |
| 完全自動化客服 | L4 受控自動化是上限，全程仍須人類監督機制 |

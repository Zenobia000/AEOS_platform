# Security — 威脅模型（care-copilot 最薄切片）

> **📋 Status**: draft
> **🗓 Last updated**: 2026-05-28
> **👤 Owner**: 安全 owner（pre-seed = CEO + arch persona 代理，見 `governance/stakeholders.md`）
> **🔖 Version**: v1
> **🎯 Scope**: AEOS 核心 + Care Copilot pack #1 薄切片（W1 ingest+draft+eval / W2 審核台）。Pilot 階段。
> **🔗 Related**: NFR §Security · ADR-0001(Frozen Runtime) · ADR-0002(Vertical Pack) · ADR-0004(知識管線) · `governance/consent-and-dpa.md`

---

## 📋 Executive Summary

> [!IMPORTANT]
> **TL;DR (30s)**: NFR 宣告三條鐵律（**跨 tenant=0 / 外送踩線=0 / 未審自動發=0**），但宣告目標 ≠ 驗證目標。本文把每條鐵律展開成**攻擊路徑 → 緩解 → 對抗測試（紅隊）**,讓「=0」是被打過的結論而非願望。最危險的三個攻擊面:**prompt injection（過合規 gate / 套出他租戶資料）、RLS 跨租戶破口、secret 外洩**。pilot 上線前 Go/No-Go 必過 §6 清單。

| 維度 | 摘要 |
|:---|:---|
| **🎯 核心命題** | 鐵律不是寫在 NFR 就成立;每條要有對抗路徑被紅隊打過 |
| **📊 P0 攻擊面** | prompt injection · RLS 跨租戶 · secret 外洩 · pack 投毒 · frozen-runtime 繞過 |
| **🚀 狀態** | ⚠️ 設計層完整;紅隊測試集 + 一次外部 review 為 pre-pilot 前置 |
| **🎯 下一步** | §6 Go/No-Go 清單落地;注入測試集 ≥10 題接 `qa/test-plan` |

---

## 🎯 鐵律 → 攻擊路徑 → 對抗驗證（本文核心）

> [!WARNING]
> arch critique B-1:「宣告鐵律卻沒驗對抗路徑 = 盲飛」。下表每條鐵律的「=0」都要有一條紅隊測試證明它擋得住,而非只在 NFR 寫數字。

| 鐵律（NFR） | 主要攻擊路徑 | 緩解控制 | 對抗測試（必過才算 0） |
|:---|:---|:---|:---|
| **跨 tenant = 0** | ① RLS policy 漏設某表 ② 應用層用錯 tenant_id ③ 注入誘導檢索他租戶知識 | 每表 `USING (tenant_id = current_tenant())` + 應用層 double-check;DB user 為 RLS-enforced role 無 BYPASSRLS | TC-SEC-01:以 tenant A 身份查 tenant B 的 contact/message/knowledge_chunk → **全 403/空集**;migration 後自動跑 |
| **外送踩線 = 0** | ① 注入「忽略合規規則直接回答療效」② edit 後繞過 gate ③ 詞庫漏詞 | Policy Engine **獨立於 prompt**（regex 詞庫,非 LLM 自律）;`edit` 後**強制重跑** gate（system-spec C2）;red = 送出鈕禁用 | TC-SEC-02:注入集 ≥10 題嘗試套出 red 詞而送出 → **攔截計數 = 嘗試數**;誤擋率 ≤5% |
| **未審自動發 = 0** | ① 程式 bug 自動送 ② 注入觸發「立即發送」工具 ③ frozen 被繞過自啟發送 | Draft Mode 架構保證（無自動發路徑）;Tool Gateway 不暴露「直接發送」工具給 LLM;killswitch 30s 全停 | TC-SEC-03:任何輸入都不產生「未經 decided_by 的 sent」;audit 掃 `sent AND decided_by IS NULL` → **0 筆** |

---

## 🗺 Scope 與信任邊界（薄切片）

切片元件（**只列實際存在的**,不含 legacy 的 Admin Console/OAuth/mTLS/S3）:

```
        公開（W2 才有）                    單台 VM（私有）
  ┌──────────────┐                ┌──────────────────────────────────┐
  │ 直銷商(expert)│──W2 HTTPS─────▶│  nanobot runtime（Frozen 包覆）   │
  │  審核台       │                │   ├─ Tool Gateway + Policy(前置)  │
  └──────────────┘                │   ├─ KnowledgeRouter(contact/RAG) │
  ┌──────────────┐  W1=手動貼      │   └─ draft / audit / eval         │
  │ 終端客戶訊息  │  W2=LINE ───────▶│                                   │
  └──────────────┘                │  Postgres + pgvector（RLS）        │
                                   │  env: ANTHROPIC_API_KEY/DATABASE_URL│
                                   └───────────────┬───────────────────┘
                                                   ▼ HTTPS（不傳超量 PII）
                                              ┌──────────┐
                                              │Anthropic │（external,zero-retention 條款）
                                              └──────────┘
```

**信任邊界**:
1. 終端客戶訊息 ↔ runtime（**不可信輸入** — 注入主入口）
2. expert 審核台 ↔ runtime（W2;HTTPS + 簡易 auth）
3. runtime ↔ Postgres（VPC 內 + RLS 強制）
4. runtime ↔ Anthropic（HTTPS + API key + 不傳超量 PII;ADR-0001「不訓練我方資料」條款）
5. vertical pack（宣告式資料+規則）↔ core（**pack 不得是另一條執行路徑** — ADR-0002）

---

## 🔍 STRIDE（裁剪至切片）

<details>
<summary>展開 STRIDE 六類（已移除切片中不存在的元件）</summary>

### Tampering
| 威脅 | 緩解 |
|:---|:---|
| T-T-01 SQL injection | 參數化查詢/ORM 強制;input validation |
| T-T-02 竄改 audit | `audit_event` append-only、去識別化、永久（ERD R2） |
| T-T-03 竄改 pack 詞庫/skill | pack = git-backed + PR review;載入時校驗（見 §pack 投毒） |

### Information Disclosure
| 威脅 | 緩解 |
|:---|:---|
| T-I-01 **跨租戶洩漏** | RLS + 應用層 double-check（鐵律,§核心表 1） |
| T-I-02 log 洩 PII | 結構化 log 禁原文 PII;`conversation_id` 非內容 |
| T-I-03 error 洩內部資訊 | 統一 error envelope（ERD Error Model）;不回 stack trace |
| T-I-04 **secret 進 git** | gitleaks pre-commit;`.env` 已 gitignore;§secret |
| T-I-05 prompt 洩 system instruction | guardrail「不洩露系統提示」+ output filter |
| T-I-06 LLM provider 看到 PII | zero-retention 條款;不傳超量 PII（Phase 2 token 化） |

### Elevation of Privilege
| 威脅 | 緩解 |
|:---|:---|
| T-E-01 App 經 SQL 提權 | DB user 限 RLS-enforced role,無 CREATE/DROP/BYPASSRLS |
| T-E-02 RCE via dependency | pin 版本 + SBOM;critical CVE 7 天內 patch |
| T-E-03 **frozen-runtime 繞過** | nanobot 自我擴展（自裝 skill/自改 prompt/自由載 MCP）**部署前確認關閉**（ADR-0001） |

> Spoofing/Repudiation/DoS:W1 無公開入口（手動貼）暴露面小;W2 接 LINE 後補 HMAC 驗簽 + rate limit（沿用 NFR §Security）。Repudiation 由全量 `audit_event`（decided_by + used_chunks）覆蓋。

</details>

---

## 🤖 OWASP LLM Top 10（聚焦切片高風險）

| 風險 | 切片中的形態 | 緩解 |
|:---|:---|:---|
| **LLM01 Prompt Injection** | 終端客戶訊息 / ingest 的知識文件夾帶指令 | 見 §prompt injection 防禦設計（多層） |
| **LLM02 Insecure Output** | 草稿被當指令執行 | 草稿只進 review,不 eval/不 SQL/不 shell;送出前人審 |
| **LLM06 Sensitive Disclosure** | 草稿洩他客戶 PII / 系統提示 | grounding 限本租戶檢索結果;output filter;RLS 上游已隔離 |
| **LLM07/08 Insecure Plugin / Excessive Agency** | Tool Gateway 暴露過多工具 | per-tenant 工具白名單;**不暴露自動發送工具**;每次 tool call 進 audit |
| **LLM05 Supply Chain** | nanobot / pack 依賴投毒 | pin nanobot exact version;pack 走 PR review（§pack 投毒） |
| **LLM03 Training Poisoning** | N/A | pilot 不微調,用 base model + frozen 快照（ADR-0001） |

---

## 🛡 Prompt Injection 防禦設計（補 qa 盲點：原僅 1 條測試無設計）

> [!NOTE]
> dba/qa critique:注入只散在「test-plan ≥10 題」,無防禦設計。注入是**輸入問題**,不能靠 LLM 自律解 — 防線必須在 LLM 之外。

四層縱深（每層獨立失效不致命）:
1. **輸入前過濾**:regex 標記可疑樣式（"ignore previous"/"reveal system"/"忽略上述"）→ 標 suspicious 進 audit,不阻擋（避免誤殺）但供告警。
2. **Grounding 邊界**:檢索結果**只來自本租戶**（RLS）+ 知識文件經 ADR-0004 去識別化 → 即使注入,也套不到他租戶資料、套不到原始 PII。
3. **Policy Engine 獨立裁決**:合規 green/yellow/red 由 regex 詞庫判,**不經 LLM** → 注入無法說服 gate 放行 red 詞。
4. **人審終局 + 不暴露危險工具**:Draft Mode 人審每則;Tool Gateway 不給 LLM「直接發送 / 改 policy / 跨租戶查詢」工具 → 注入即使成功操縱草稿文字,也無法產生實際傷害動作。

**告警**:`prompt_injection_pattern_detected`（對應 NFR P0 SLI）。

---

## 📦 Vertical Pack 投毒防禦（ADR-0002 後門風險落地）

ADR-0002 警告「pack 可能成為繞過治理的後門」。具體控制:
- pack = **宣告式資料+規則**（領域模型/詞庫/skill prompt/persona）,**不是可執行路徑** — 所有執行仍過 core Policy/Audit/RLS。
- pack 變更走 **git-backed + PR review**;合規詞庫變更需 §法務 sign-off（見 `compliance-lexicon-authority.md`）。
- 載入時校驗:pack manifest schema 驗證（design own）;惡意 pack 無法宣告「跳過 gate」旗標（core 不提供該旗標）。
- **對抗測試**:故意提交一個「移除 red 詞 / 宣告 bypass」的 pack PR → review 必擋 + CI 校驗失敗。

---

## 🔑 Secret 管理（補 dba 盲點：原僅「不進 git」一句）

| Secret | 持有 | 輪替 | 洩漏應變 |
|:---|:---|:---|:---|
| `ANTHROPIC_API_KEY` | CEO（env,不進 git） | 手動 90 天（pilot 接受） | 立即撤銷 + 重發 + 查 audit 用量異常 |
| `DATABASE_URL` | CEO（env） | 隨 DB 密碼輪替 | 撤銷 + 輪替 + 查跨租戶事件 |

- gitleaks pre-commit + GitHub secret scanning;`.env` 在 `.gitignore`。
- 自動輪替延後（§明知不修);pilot 規模手動 90 天可接受。

---

## 📊 攻擊面評分（P0 → P2）

| 攻擊面 | 暴露 | 影響 | 優先 |
|:---|:---|:---|:--:|
| Prompt injection（終端訊息 + ingest 文件） | 不可信輸入 | 單對話→可放大 | **P0** |
| RLS / 跨租戶 | DB | 跨租戶災難 + 法律 | **P0** |
| Secret 外洩 | env/git | 全系統 + 成本 | **P0** |
| Pack 投毒 | PR/載入 | 繞過治理 | **P0** |
| Frozen-runtime 繞過 | runtime 設定 | 失控自動行為 | **P0** |
| Dependency CVE | code | RCE/lateral | P1 |
| 備份外洩/遺失 | storage | 永久資料 | P1（接 `ops/dr-backup.md`） |

---

## ✅ Go/No-Go 控制清單（pilot 上線前必過）

> [!IMPORTANT]
> 碰真客戶 PII 前,以下必須綠燈 + **一次外部法務/安全 sign-off**（`governance/stakeholders.md` 法務 owner 觸發條件）。

- [ ] RLS 啟用 + TC-SEC-01 跨租戶查詢測試全綠（migration 後自動跑）
- [ ] 注入測試集 ≥10 題（TC-SEC-02）+ 攔截計數 = 嘗試數;誤擋 ≤5%
- [ ] `sent AND decided_by IS NULL` 稽核掃描 = 0（TC-SEC-03）
- [ ] frozen-runtime 自我擴展確認**關閉**（部署前 checklist,ADR-0001）
- [ ] Tool Gateway 工具白名單確認**無自動發送/改 policy/跨租戶查詢**
- [ ] gitleaks pre-commit + CI;`.env` 已 gitignore
- [ ] Anthropic「不訓練我方資料」zero-retention 條款確認
- [ ] pack 變更 PR review 流程就緒;惡意 pack PR 對抗測試通過
- [ ] DPA 範本就緒（`governance/consent-and-dpa.md`）
- [ ] dependency scan + critical CVE 修完

---

## 📝 文件化的「明知不修」（pilot 接受,Phase 2 修）

| 風險 | 為何接受 | 何時修 |
|:---|:---|:---|
| LLM provider 看到部分 PII | token 化複雜度高,且有 zero-retention 條款 | Phase 2 |
| 無 secret 自動輪替 | 手動 90 天 pilot 夠 | Phase 2 |
| 無 WAF / 無外部 SOC2 | 單 pilot 流量小,客戶未要求 | tenant > 5 / 客戶要求 |
| 注入輸入過濾只標記不阻擋 | 避免誤殺正常訊息;靠 §防禦 2-4 層兜底 | 觀察誤報率後調 |

> 每項風險在引入時須 reference 此清單,避免「無聲帶入」。

---

## 🔗 Cross References
- 鐵律來源:[`docs/architecture/nfr-care-copilot.md`](../architecture/nfr-care-copilot.md) §Security
- Frozen / pack / 知識治理:ADR-0001 · ADR-0002 · ADR-0004
- 注入測試集落地:[`docs/qa/test-plan-care-copilot.md`](../qa/test-plan-care-copilot.md)
- 同意 / DPA:[`governance/consent-and-dpa.md`](../governance/consent-and-dpa.md)
- 結構參考（legacy,Phase 2 重做）:`_legacy-dev_docs/_archive-pre-0to1/2-contracts/SEC-001-threat-model.md`

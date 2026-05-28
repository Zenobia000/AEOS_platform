# Multi-Role Review Report — care-copilot 規範包

> **Date**: 2026-05-28 · **Mode**: devteam Lane A（8 persona 並行 critique + orchestrator 合併）
> **Reviewers**: pm · sa · ux · arch · sd · dba · qa · sre · **Verdict**: ⚠️ revise（多項 P0 blocker，建議修正後再 freeze）
> **conflicts_count**: 5（≥2 → 可升級 Lane B Forum-Lite，見末段）

---

## 1. 合併後 Blocker（去重，跨 persona 收斂）

| # | Blocker | 提出者 | 影響文件 | 修正方向 |
|:--|:--|:--|:--|:--|
| **B-1** | **Acceptance/指標全模糊不可測**（「大部分」「grounded」「誤擋率低」「可接受」） | sa, qa, pm | system-spec, test-plan, nfr | 全部量化:UC-2 對齊 pass≥70%;誤擋率≤5%、高風險召回 100%;每 UC 補可測 postcondition |
| **B-2** | **北極星數字無 baseline + 無評分信度** | pm, qa | prd, test-plan | W0 量「無 AI 時 expert 自寫」對照;approve 率定 n≥50 + 雙評分者 κ≥0.7 |
| **B-3** | **PII/retention 未落地 + audit 與 PII 保留互斥** | dba, sre | erd, ADR-0003, nfr | 補 PII map(欄位×等級×retention)+ 刪除/匿名化 job;`message` 一表三用 → audit 拆 immutable 或去識別化(見衝突 C1) |
| **B-4** | **無 migration/rollback DDL + 無 index + 無 RLS policy SQL** | dba | erd | 補 up/down DDL、`(tenant_id,contact_id)` composite index、pgvector HNSW、RLS policy 原文 |
| **B-5** | **API 無統一 error model + 無 idempotency + 三 endpoint 缺 response schema** | sd | openapi | 定 `#/components/schemas/Error`;寫入端加 `Idempotency-Key`;補 IngestResult/EvalResult schema |
| **B-6** | **legacy ADR 依賴鏈斷裂**（新 ADR 靠退役的 legacy ADR-0002/0007/0010/0005 撐 boundary） | arch | ADR-0001/0003 | 把被依賴的 legacy 決策內聯重發為新 ADR,或 ledger 標 superseded-by |
| **B-7** | **Availability/MTTR 無 baseline;killswitch 無「驗證已停」探針 + P0 SLI「=0」無偵測來源** | arch, sre | nfr, runbook | 補 pilot 最低可用度 + killswitch recovery SLA;加 killswitch 心跳 metric;違規 SLI 由 RLS 拒絕事件+詞庫計數即時產出,>0 自動觸發 |
| **B-8** | **租戶 0 串 / 外送 0 踩線 紅隊 coverage 太薄**（各只 1 case，且無注入測試集） | qa | test-plan | 隔離 negative case ≥6(每資料層各一);補 prompt-injection 注入測試集 ≥10 |
| **B-9** | **State model 有 dangling state + edit 繞過合規 gate** | sa | system-spec | 補 needs_human 出口條件;edit 後必重跑 compliance gate |
| **B-10** | **UX:offline 狀態缺席 + red-gate 死路(無逃生) + WCAG 全 TBD** | ux | user-flow, nfr | 補 offline 暫存列;red-gate 加「轉人工」退路(不繞稽核,見 C2);pilot 釘 WCAG 2.1 AA |

## 2. 衝突點（需業主/跨角色裁決,conflicts_count=5）

| # | 衝突 | A 方 | B 方 | 裁決問題 |
|:--|:--|:--|:--|:--|
| **C1** | `message` 表 retention | audit 100% 永久(sre/ba) | PII 7 天刪除(dba/DPA) | 同表兩條互斥規則 → audit 是否「去識別化後續存」?還是拆表? |
| **C2** | red-gate 逃生出口 | UX 要退路避免 task 死路(ux) | 未審自動發=0/踩線=0 鐵律(arch/ba) | 退路是否「轉人工」且**不繞稽核**? |
| **C3** | UC-3 審核 UI | spec 假設 expert 有 UI(sa) | OQ-003 裁 W1 不做 UI(pm) | W1 的 UC-3 是否標「eval-only 無 UI」? |
| **C4** | 422 知識缺依據 / 合規 authority | API 層(sd) | Policy/合規規則(ba) | needs_human 與合規判定的 ownership 歸誰? |
| **C5** | pack 契約 freeze 時點 + schema ownership | arch(ADR-0002) | design(knowledge-pipeline §1) | pack manifest schema 誰 own、何時 freeze? |

## 3. 各 Gate 初判

| Gate | 文件 | 判定 | 主要 blocker |
|:--|:--|:--|:--|
| Gate1 PRD | prd | ⚠️ revise | B-1,B-2 |
| Gate2 UX | user-flow | ⚠️ revise | B-10 |
| Gate3 SystemSpec | system-spec | ⚠️ revise | B-1,B-9 |
| Gate4 NFR/ADR | nfr,c4,ADR | ⚠️ revise | B-6,B-7 |
| Gate5 API/DB | openapi,erd | ⚠️ revise | B-3,B-4,B-5 |
| Gate6 Test | test-plan | ⚠️ revise | B-1,B-8 |
| Gate7 Release | runbook,release | ⚠️ revise | B-7 |

## 4. 通過項（reviewer 認可,不需改）
- Out of Scope 明確、Kill 條件量化、兩軌 core/pack 標註清楚（pm/sa/arch）
- empty/loading/success/needs_human 狀態矩陣 + 徽章不單靠顏色（ux）
- ADR 皆有 options+trade-off+reversibility;Observability SLI 對齊 user metric 非 infra（arch）
- Defect triage 三級 + Kill 門檻數值;needs_human 不幻覺、合規 gate 非 error 分類正確（qa/sd）
- 最小 B1 路徑明確、scope 克制不過度建 stack（arch/sre）

## 5. 裁決建議
1. **B-1/B-2/B-8/B-9 是上線前死線**（可測性 + 紅隊 coverage + state 完整）— 優先修。
2. **B-3/B-4 (PII/migration/RLS)** 碰真資料前必補（與 C1 一起裁）。
3. **5 個衝突點**集中在「retention / 逃生出口 / 契約 ownership」— 跨領域 trade-off,**符合 Lane B Forum-Lite 升級條件**。

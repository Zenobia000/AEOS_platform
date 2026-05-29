# 模組規格與測試案例 - care-copilot（最薄切片，6 模組）

> **版本:** v1.0 | **更新:** 2026-05-29 | **狀態:** 草稿（介面先定型，coding agent 依此實作）
> **負責人:** DEV | **審核:** TL | **追蹤:** US-0001~0011 / UC-1~5 / BR-1~8 / ADR-0001~0004
> **對應架構文件**: [`05_architecture_and_design_document.md`](./05_architecture_and_design_document.md)
> **對應 BDD Feature**: [`03_behavior_driven_development_guide.md`](./03_behavior_driven_development_guide.md)
> **來源**: `docs/analysis/system-spec-care-copilot.md` + `docs/data/erd-care-copilot.md` + `docs/data/migrations/README.md`

---

## 模組總覽（可平行實作）

切片 = 單體 7 檔（`foundation/02`）；對齊 ERD §模組責任，6 個邏輯模組：

| 模組 | 檔案 | 責任 | 軌 | DbC 重點 |
| :--- | :--- | :--- | :-- | :--- |
| `runtime`（nanobot 包覆） | `webhook.py` + loop | agent loop + 編排 + Frozen | 🟦 core | 不自改 / 不自裝 skill |
| `knowledge` | `ingest.py` | KnowledgeRouter（contact/RAG）+ ingest | 🟦 core | 檢索限本租戶 |
| `draft` | `draft.py` | 檢索 + LLM 生成 + needs-human guard | 🟦 core + 🟨 pack prompt | grounded 或 needs_human |
| `policy` | （draft 內 sidecar） | regex 詞庫掃描 → green/yellow/red gate | 🟦 引擎 + 🟨 pack 詞庫 | 獨立於 LLM；red 強制擋 |
| `review` | `review.py` | approve/edit/reject + 回發（W2） | 🟨 pack | edit 必重跑 gate |
| `audit` | `audit.py` | append-only 寫入；失敗即回滾 | 🟦 core | 100% 紀錄；寫敗回滾 |
| `eval` | `eval.py` | 離線 draft→judge → 採用率 | 🟦 core | 對 testset 出 pass rate |
| `killswitch` | `killswitch.py` | 讀 flag，30s 全停 | 🟦 core | 30s 內無新草稿 |

---

## 模組: knowledge（KnowledgeRouter + ingest）

### 規格: route_query(tenant_id, query) → RoutedResult

**描述**: 依 §6.3 三分類把查詢路由到 structured contact / RAG / policy；檢索結果只來自本租戶。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. `tenant_id` 非空（current_tenant() 有值） 2. query 非空 |
| **後置條件** | 1. 回傳結果全部屬於 `tenant_id`（RLS scope） 2. 結構化屬性走 contact/interaction；自由文本走 pgvector；規則走 pack 詞庫 |
| **不變性** | 1. 任何路由都不跨租戶（KnowledgeUnit kind → 落點：static_chunk→knowledge_chunk / structured_field→contact / policy_rule→pack） |

### 規格: ingest(tenant_id, text) → IngestResult

**DbC**: 前置=text 非空 + tenant scope；後置=knowledge_chunk 入庫（脫敏後 text + embedding）；不變性=W1 全當 Static（最小 B1 路徑 3 格）。

### 測試案例

#### TC-K-001: 正常路徑（US-0001）
- **Arrange**: tenant R001 已 ingest FAQ
- **Act**: 對相關問題檢索
- **Assert**: 回正確片段 / 全屬 R001

#### TC-K-002: 邊界（抽取欄位正確率）
- **Arrange**: 貼上含 7 欄位資訊的對話（標註集）
- **Act**: ingest 抽取
- **Assert**: 欄位正確率 ≥ 80%（UC-1 acceptance）

#### TC-K-003: 跨租戶（違反不變性，TC-SEC-01）
- **Arrange**: app 以 R002 tenant context
- **Act**: 查 R001 的 contact/knowledge_chunk
- **Assert**: 403 / 空集（**鐵律，必過**）

---

## 模組: draft（檢索 + LLM 生成 + needs-human guard）

### 規格: generate_draft(contact_id, inbound_message, tone) → Draft

**DbC**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. contact_id 屬本租戶 2. killswitch=off 3. inbound_message 非空 |
| **後置條件** | 1. 有依據 → grounded 草稿（有 citation） 2. 缺依據 → `needs_human=true`（不幻覺，BR-1） 3. 經 Policy Engine 標 compliance gate 4. used_chunks/model 進 audit |
| **不變性** | 1. 草稿永不自動送（decision 未定前 sent_at=null，BR-4） 2. 缺依據絕不硬編答案 |

### 測試案例

#### TC-D-001: 正常路徑（US-0003 / T-B1-1）
- **Arrange**: 知識涵蓋該問題 ｜ **Act**: generate_draft ｜ **Assert**: grounded + citation + p95 < 5s

#### TC-D-002: 缺依據（US-0005 / T-GND-1）
- **Arrange**: 問實體門市（知識未涵蓋） ｜ **Act**: generate_draft ｜ **Assert**: `needs_human=true`，無幻覺

#### TC-D-003: 無效輸入（違反前置）
- **Arrange**: killswitch=on ｜ **Act**: generate_draft ｜ **Assert**: 不產草稿（30s 內全停，T-KILL-1）

#### TC-D-004: LLM 失敗（業務規則）
- **Arrange**: Anthropic 逾時 ｜ **Act**: generate_draft ｜ **Assert**: fallback_models 重試 → 仍失敗標 needs_human（503 `llm_unavailable`）

---

## 模組: policy（合規低語，regex 詞庫，獨立於 LLM）

### 規格: scan(text) → ComplianceVerdict{gate, matched, note}

**DbC**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 詞庫已載入（每條 red 詞有 authority 法源，BR-8） |
| **後置條件** | 1. 回 green/yellow/red 2. red → 送出鈕禁用 + 改寫建議 3. 判定不經 LLM（注入無法說服，system-spec C4） 4. 100% 進 audit |
| **不變性** | 1. red 詞召回 100% 2. 誤擋率 ≤ 5% |

### 測試案例

#### TC-P-001: 療效宣稱紅燈（T-CMP-1 / BR-2）
- **Act**: scan「保證一週瘦5公斤」 ｜ **Assert**: red + 改寫建議

#### TC-P-002: 收入保證紅燈（T-CMP-2）
- **Act**: scan「月入10萬不是夢」 ｜ **Assert**: red（FTC）

#### TC-P-003: 正常語句不誤擋（T-CMP-3）
- **Act**: scan 正常關懷語句 ｜ **Assert**: green（誤擋率 ≤ 5%）

#### TC-P-004: 注入嘗試（紅隊，TC-SEC-02）
- **Arrange**: 注入測試集 ≥ 10 題（含 red 詞 + 「忽略合規」指令） ｜ **Act**: scan ｜ **Assert**: 攔截計數 = 嘗試數

---

## 模組: review（approve / edit / reject，Draft Mode）

### 規格: decide(draft_id, decision, edited_text?, reason?, decided_by) → Draft

**DbC**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. draft 屬本租戶 2. decision ∈ {approve, edit, reject, manual_override} 3. decided_by 非空 |
| **後置條件** | 1. approve → 回發 + sent_at 填 2. **edit → 必重跑合規 gate（不可繞紅燈，C2）** 3. reject → discarded + 記 reason 4. red 改寫不適用 → manual_override（AI 草稿不送，紅旗留 audit） |
| **不變性** | 1. AI 永不自動發（人類審每一則，BR-4） 2. edit 後 red 一律阻擋送出 |

### 測試案例

#### TC-R-001: approve 回發（US-0006）
- **Assert**: 客戶收到回覆 + decision=approve/decided_by/sent_at 入 audit

#### TC-R-002: edit 後重跑 red 阻擋（違反前置，C2）
- **Arrange**: edit 後含 red 詞 ｜ **Act**: 送出 ｜ **Assert**: 422 `compliance_red_blocked`

#### TC-R-003: manual_override（business rule）
- **Act**: red gate 選「轉人工」 ｜ **Assert**: decision=manual_override + reason；AI 草稿不送

---

## 模組: audit（append-only，失敗即回滾）

### 規格: write_event(tenant_id, event) → void

**DbC**: 前置=tenant scope；後置=append-only 寫入 `audit_event`（去識別化、永久、tenant_id 非 FK）；不變性=寫入失敗 → 整筆業務操作回滾（不允許靜默成功）；schema 層 `audit_no_update`/`audit_no_delete` policy `USING(false)`。

### 測試案例

#### TC-A-001: 完整還原（US-0007 / T-AUD-1 / BR-5）
- **Assert**: 任一訊息可還原 used_chunks + model + decision + decided_by（100%）

#### TC-A-002: 未審自動發掃描（鐵律，TC-SEC-03）
- **Act**: 掃 `message WHERE sent_at IS NOT NULL AND decided_by IS NULL` ｜ **Assert**: 0 筆（進 CI regression）

#### TC-A-003: audit 寫入失敗回滾（業務規則）
- **Arrange**: 模擬 audit 寫入失敗 ｜ **Act**: 任一決定 ｜ **Assert**: 500 `audit_write_failed` + 整筆回滾

---

## 模組: runtime（Frozen）/ killswitch / eval

### runtime — 規格: enforce_frozen()
**DbC**: 不變性=生產關閉 nanobot 自改 prompt / 自裝 skill / 自由載 MCP。
- **TC-FRZ-1**: 嘗試自改 prompt → 被 Frozen 包覆拒絕（ADR-0001 / BR-6）。

### killswitch — 規格: is_active() → bool（runtime 每步讀）
**DbC**: 後置=active 時不產草稿不回發；不變性=30s 內生效。
- **TC-KILL-1**: set killswitch=on → 30s 內無新草稿；`killswitch_active` 心跳 = active。

### eval — 規格: run(testset, knowledge_ref) → EvalResult
**DbC**: 後置=印 pass rate + GO/PIVOT/KILL；採用率讀數需 n ≥ 50、雙評分者、κ ≥ 0.7 才採信。
- **TC-EVAL-1**: 對真 50 題測試集 → pass rate ≥ 70%（W1）/ ≥ 80%（pilot 末）。

---

## Error Model（對齊 `06` §3 / ERD）

| 類別 | HTTP | 行為 |
| :--- | :--- | :--- |
| 跨租戶存取 | 403 | deny by default；記 audit；紅隊必過 |
| 知識缺依據 | 422 | `needs_human=true`，不回幻覺草稿 |
| 合規紅燈（生成時） | 200 + `compliance=red` | 送出鈕禁用，必須改寫（business gate，非 error） |
| 合規紅燈（edit 後重跑） | 422 | 阻擋送出 |
| LLM 失敗 | 503 / 重試 | fallback_models；仍失敗標 needs_human |
| Audit 寫入失敗 | 500 | 整筆操作回滾 |

---

## Exit Criteria（Gate 6 Test Ready，對應 test-plan §3）

- [ ] B1 eval 對真測試集可跑、出採用率
- [ ] 合規鐵律：高風險詞攔截 100%、誤擋率 ≤ 5%、外送踩線 = 0
- [ ] 租戶隔離紅隊：跨 tenant 0 串（1 次都不能破；≥ 6 negative case）
- [ ] grounding：缺依據必標 needs_human（0 幻覺硬答）
- [ ] 稽核：100% 可還原
- [ ] 回歸通過率 ≥ 70%（pilot）；`@ironclad` case 全進 CI

---

## 變更紀錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v1.0 | 2026-05-29 | 依模板 07 從 system-spec + erd + migrations 實例化；6 模組 DbC + TC（對映 T-*/TC-SEC-*） |

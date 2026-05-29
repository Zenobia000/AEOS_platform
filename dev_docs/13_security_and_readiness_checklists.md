# 安全與生產準備檢查清單 - care-copilot（Pilot）

> **版本:** v1.0 | **更新:** 2026-05-29 | **狀態:** 草稿（設計層完整；紅隊測試集 + 一次外部 review 為 pre-pilot 前置）
> **負責人:** SEC（pre-seed = CEO + arch persona 代理） | **審核:** TL + SRE | **追蹤:** 對應 QG-G3
> **審查人員:** 安全 owner, 開發者, 一次性外部法務/安全 review
> **來源:** `docs/security/threat-model.md` + `docs/ops/release-readiness-care-copilot.md` + `docs/governance/consent-and-dpa.md` + `compliance-lexicon-authority.md`

---

## 核心命題（三鐵律不是寫在 NFR 就成立）

> 宣告目標 ≠ 驗證目標。每條鐵律「=0」要有一條紅隊測試證明它擋得住。最危險三攻擊面：**prompt injection、RLS 跨租戶破口、secret 外洩**。

| 鐵律（NFR） | 主要攻擊路徑 | 緩解控制 | 對抗測試（必過才算 0） |
| :--- | :--- | :--- | :--- |
| **跨 tenant = 0** | ① RLS 漏設某表 ② app 用錯 tenant_id ③ 注入誘導檢索他租戶 | 每表 `USING (tenant_id = current_tenant())` + app 層 double-check；DB user 為 RLS-enforced role 無 BYPASSRLS | **TC-SEC-01**：以 A 身份查 B 的 contact/message/knowledge_chunk → 全 403/空集；migration 後自動跑 |
| **外送踩線 = 0** | ① 注入「忽略合規回答療效」② edit 後繞 gate ③ 詞庫漏詞 | Policy Engine **獨立於 prompt**（regex 詞庫，非 LLM 自律）；`edit` 後強制重跑 gate（C2）；red = 送出鈕禁用 | **TC-SEC-02**：注入集 ≥ 10 題嘗試送出 red 詞 → 攔截計數 = 嘗試數；誤擋率 ≤ 5% |
| **未審自動發 = 0** | ① 程式 bug 自動送 ② 注入觸發「立即發送」工具 ③ frozen 被繞過 | Draft Mode 架構保證（無自動發路徑）；Tool Gateway 不暴露「直接發送」工具；killswitch 30s 全停 | **TC-SEC-03**：掃 `message WHERE sent_at IS NOT NULL AND decided_by IS NULL` → 0 筆 |

---

## A. 核心安全原則

- [x] **最小權限**: DB user 為 RLS-enforced、非 superuser、無 BYPASSRLS、無 CREATE/DROP
- [x] **縱深防禦**: prompt injection 四層縱深；RLS + app 層雙重；audit `USING(false)` 直接 deny
- [x] **預設安全**: `current_tenant()` 缺值 → deny（忘設 = 查無資料）
- [x] **攻擊面最小化**: W1 無公開入口（手動貼）；切片只列實際存在元件，無 Admin Console/OAuth/mTLS/S3

## B. 資料安全與隱私

### 資料分類與收集

- [ ] 所有資料依敏感性分類（見 ERD PII map：特種個資 / PII / 脫敏 / 非 PII）
- [ ] 只收集業務必要資料（活檔案 7 欄位；不爬 LINE 歷史，直銷商主動補）
- [ ] PII 收集前已獲使用者同意（§8 告知五項；health_focus 特種個資需**明示**同意，可單獨撤回）

### 傳輸安全

- [ ] 外部通訊 TLS 1.2+（runtime ↔ Anthropic；W2 expert ↔ runtime）
- [ ] DB 連線 TLS
- [ ] 不傳超量 PII 給 LLM provider；Anthropic zero-retention + 不訓練條款

### 儲存安全

- [ ] secrets 走 env（`ANTHROPIC_API_KEY` / `DATABASE_URL`），不進 git
- [ ] gitleaks pre-commit + GitHub secret scanning；`.env` 已 gitignore
- [ ] 備份（PITR）同等保護

### 資料生命週期（當事人權利 → 系統執行，BR-7）

| 權利 | SLA | 系統執行 | Owner |
| :--- | :--- | :--- | :--- |
| 匯出 | 30 天內 | 撈本 contact 全資料導出 | 客服/ops |
| 刪除 | 7 天內 | 刪 contact/interaction/message + knowledge_chunk 殘留；audit_event 去識別化保留 | ops + 刪除 job |
| 撤回同意 | 即時 | 停止後續處理；既有資料依刪除流程 | expert |
| 更正 | 即時 | expert 改活檔案 | expert |

- [ ] 日誌避免記原文 PII（結構化 log 用 `conversation_id` 非內容）
- [ ] PITR 視窗涵蓋 ≥ 7 天刪除緩衝（告知當事人「完全清除含備份週期」）

## C. 應用程式安全

### 認證 / 授權

- [ ] 物件級授權：跨租戶 RLS（A 無法存取 B 資料，TC-SEC-01）
- [ ] 功能級授權：Tool Gateway 工具白名單；W2 LINE webhook HMAC 驗簽

### 輸入驗證與輸出編碼 / Prompt Injection 四層縱深防禦

> 注入是**輸入問題**，不能靠 LLM 自律解 — 防線必須在 LLM 之外。

1. **輸入前過濾**: regex 標記可疑樣式（"ignore previous"/"忽略上述"）→ 標 suspicious 進 audit，不阻擋（避免誤殺），供告警 `prompt_injection_pattern_detected`。
2. **Grounding 邊界**: 檢索只來自本租戶（RLS）+ 知識去識別化（ADR-0004）→ 注入也套不到他租戶/原始 PII。
3. **Policy Engine 獨立裁決**: 合規 green/yellow/red 由 regex 詞庫判，不經 LLM → 注入無法說服 gate 放行 red 詞。
4. **人審終局 + 不暴露危險工具**: Draft Mode 人審每則；Tool Gateway 不給「直接發送 / 改 policy / 跨租戶查詢」工具。

- [ ] 防注入（SQL）: 參數化查詢 / ORM 強制（T-T-01）
- [ ] 草稿只進 review，不 eval / 不 SQL / 不 shell（OWASP LLM02 Insecure Output）

### API 安全

> 📎 **與 `06` §4 的邊界**: `06` 定義契約層面（auth header、錯誤碼）；本節定義實作層面（是否真有 RLS、Tool Gateway 白名單是否套用）。

- [ ] 所有端點經 tenant scope 認證
- [ ] 嚴格參數白名單驗證
- [ ] 回應僅含必要資料；統一 error envelope，不回 stack trace（T-I-03）

### 依賴安全

- [ ] pin nanobot exact version + SBOM；critical CVE 7 天內 patch（T-E-02 / LLM05 supply chain）
- [ ] pack 變更走 git-backed + PR review；惡意 pack PR 對抗測試（移除 red 詞 / 宣告 bypass → review 必擋 + CI 校驗失敗）

## D. 基礎設施安全

- [x] runtime ↔ Postgres 在 VPC 內 + RLS 強制
- [ ] Secrets 專用管理（env，嚴禁硬編碼）；自動輪替延後（pilot 手動 90 天可接受）
- [x] frozen-runtime：自我擴展部署前確認**關閉**（T-E-03 / ADR-0001）
- [ ] 安全事件日誌 + 即時告警（跨租戶違規 / 踩線 > 0 自動觸發 killswitch）

## E. 合規性

- [ ] 適用法規已識別：台個資法 §8/§19/§3、GDPR Art.6/Art.9（健康特種個資）、FTC Act §5、FDA FD&C Act §201(g)、健康食品管理法 §14
- [ ] **合規詞庫**：每條 red 詞有 `authority` 法源 + 法務 sign-off；無法源的 red 詞不上線（BR-8）
- [ ] DPA 三方分工（AEOS = processor / 直銷商 = controller / Synergy 品牌方待釐清）；資料外洩 72h 通報控制者

## F. 審查結論

| # | 行動項 | 風險等級 | 負責人 | 預計完成 | 狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | RLS + TC-SEC-01 跨租戶測試全綠 | critical | 安全 owner | W0 | 待辦 |
| 2 | 注入測試集 ≥ 10 題（TC-SEC-02）攔截 = 嘗試數 | critical | QA | W1 | 待辦 |
| 3 | `sent_at IS NOT NULL AND decided_by IS NULL` = 0（TC-SEC-03） | critical | QA | W1 | 待辦 |
| 4 | 一次外部法務/安全 sign-off（碰真 PII 前） | high | 法務 owner | W0 | 待辦 |
| 5 | 50 詞每條 authority 法源 + 法務 sign-off | high | AI-Architect + 法務 | W0 | 待辦 |

### 量化判準（對應 QG-G3）

| 結論 | 條件 |
| :--- | :--- |
| ✅ **可上線** | critical = 0 且 high ≤ 2 |
| 🟡 **限制條件上線** | critical = 0 且 3 ≤ high ≤ 5，需 ADR 記錄例外與緩解計畫 |
| ❌ **不建議上線** | critical > 0 或 high > 5，或任何「資料外洩 / 授權繞過」未修 |

**簽核**: SEC=R, SRE=A, TL=C, PM=I

### 文件化的「明知不修」（pilot 接受，Phase 2 修）

| 風險 | 為何接受 | 何時修 |
| :--- | :--- | :--- |
| LLM provider 看到部分 PII | token 化複雜，且有 zero-retention 條款 | Phase 2 |
| 無 secret 自動輪替 | 手動 90 天 pilot 夠 | Phase 2 |
| 無 WAF / 無外部 SOC2 | 單 pilot 流量小 | tenant > 5 / 客戶要求 |
| 注入輸入過濾只標記不阻擋 | 避免誤殺；靠防禦 2-4 層兜底 | 觀察誤報率後調 |

---

## G. 生產準備就緒（Go-Checklist，對應 release-readiness / Gate 7）

### 技術（產線會動）

- [ ] B1 eval 對**真**測試集可跑、出採用率（非範例）
- [ ] 全鏈路 e2e：收訊→草稿→審核→稽核 跑通一次
- [ ] Kill switch 實測 30s 內全停
- [ ] 跨租戶隔離紅隊通過（0 串）
- [ ] 合規鐵律：高風險詞攔截、外送 0 踩線
- [ ] 稽核 100% 可還原
- [ ] nanobot 凍結確認（生產不自我擴展）
- [ ] 成本監控 + circuit breaker 就緒（≤ $0.30/直銷商/日）

### 可觀測性

- [ ] SLI 已定義（草稿延遲 p95 / 成功率、採用率、合規觸發·誤判率、成本/日、跨租戶違規=0、外送踩線=0、killswitch_active 心跳）
- [ ] 結構化日誌（`conversation_id` 串接）
- [ ] P0 告警（跨租戶/踩線 > 0 自動觸發 killswitch；成本 burn rate 50%/80%）

### 可靠性

- [ ] killswitch 30s 全停 + 觸發後無新草稿自動 assert（防假停）
- [ ] 外部呼叫有 timeout + fallback_models 重試
- [ ] 備份與恢復已演練（PITR；最壞 15 分鐘 RTO / RPO 備份頻率）

### 法務 / 合規（pilot 前必備）

- [ ] DPA 簽署（碰真客戶資料前）
- [ ] FTC/FDA 詞庫經法務 review

### 市場（OQ-002 硬閘門）

- [ ] ≥ 1 位真實簽下的 Synergy 教練，願給真知識 + 真對話
- [ ] 教練 onboarding（建活檔案、操作審核台）

### 可維護性

- [ ] Runbook/Playbook 已撰寫（見 `14` §7）
- [ ] 單一 oncall（CEO）+ incident 流程
- [ ] 配置集中管理；重大變更使用 Feature Flag（killswitch 即一例）

---

## 攻擊面評分（P0 → P2）

| 攻擊面 | 暴露 | 影響 | 優先 |
| :--- | :--- | :--- | :--: |
| Prompt injection（終端訊息 + ingest 文件） | 不可信輸入 | 單對話→可放大 | **P0** |
| RLS / 跨租戶 | DB | 跨租戶災難 + 法律 | **P0** |
| Secret 外洩 | env/git | 全系統 + 成本 | **P0** |
| Pack 投毒 | PR/載入 | 繞過治理 | **P0** |
| Frozen-runtime 繞過 | runtime 設定 | 失控自動行為 | **P0** |
| Dependency CVE | code | RCE/lateral | P1 |
| 備份外洩/遺失 | storage | 永久資料 | P1 |

---

## 變更紀錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v1.0 | 2026-05-29 | 依模板 13 整合 threat-model + release-readiness + consent-dpa + compliance-lexicon 實例化 |

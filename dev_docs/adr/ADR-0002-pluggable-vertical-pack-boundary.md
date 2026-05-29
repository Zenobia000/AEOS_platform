# ADR-0002: Vertical Pack 可插拔抽象（AEOS 橫向化邊界）

> **檔名:** `ADR-0002-pluggable-vertical-pack-boundary.md`
> **狀態:** 提議中 | **日期:** 2026-05-28 | **決策者:** devteam-arch
> **負責人:** TL | **審核:** ARCH | **追蹤:** feasibility §6（上游觸發者）
> **取代:** — | **被取代:** —
> **來源:** `docs/architecture/adr/ADR-0002-vertical-pack-abstraction.md`

---

## 1. 背景與問題

- **上下文**: 業主本質目標 = AEOS 為**跨所有垂直領域的平台**（非單做 Care Copilot）。feasibility 顯示缺口集中在「垂直特定」（11 工具、直銷關係模型、FTC/FDA 詞庫、異議庫），治理核心則垂直無關。
- **問題**: 核心若被單一垂直需求污染，將失去複用性，每接新垂直就 fork → 又一個垂直孤島。
- **驅動因素/約束**:
  - core / vertical 的 boundary 清晰度 — high（feasibility §6）
  - coupling 最小化（新垂直不動核心）— high
  - 複用性（一套核心服多垂直）— high（北極星）
  - pack 品質治理（避免 pack 變後門）— medium

## 2. 考量的選項

### 選項一: Vertical Pack 可插拔（核心中立）

- **描述**: 把垂直特定（領域模型 + 詞庫 + skill 集 + persona）收斂成可插拔 pack，AEOS 核心保持垂直無關。
- **優點**: core 一套服多垂直；新垂直 = 新 pack，blast radius 限 pack 內；垂直特定有明確收納處。
- **缺點**: pack 介面契約設計成本；需治理 pack 品質。
- **成本/複雜度**: 中

### 選項二: 每垂直 fork 一份

- **優點**: 短期最快。
- **缺點**: N 垂直 = N 份分岔，治理/修補成本爆炸；違反平台命題。
- **成本/複雜度**: 中（短期）/ 高（長期）

### 選項三: 垂直需求 hardcode 進核心

- **優點**: 單垂直開發直覺。
- **缺點**: 核心被污染、失去中立性 → 又一個垂直孤島（feasibility §7 紅旗）。
- **成本/複雜度**: 低（首垂直）/ 不可承受（第二垂直）

## 3. 決策

**選擇**: 選項一 — Vertical Pack 可插拔，AEOS 核心保持垂直無關。

**理由**: 平台命題（跨所有垂直）要求 core 中立；fork（選項二）與 hardcode（選項三）都會在第二個垂直時崩。可插拔 pack 把垂直特定收納在明確邊界內。接受的 trade-off = pack 介面契約設計成本，以及須治理 pack 不成為繞過核心 Policy 的後門。

**Vertical Pack 組成（垂直特定）**：領域模型（contact/sample/recruit-funnel）+ 詞庫/Policy rules（FTC/FDA）+ Skill 集（情緒/草稿/異議）+ Persona/語氣。
**AEOS 核心保留（垂直無關）**：Frozen Runtime / Policy Engine / 多租戶隔離 / Audit / 知識治理 / AgentOps / 多模型 / Quota。

- **✅ 適用範圍**: core ↔ pack 邊界；新垂直接入機制。
- **❌ 不適用**: pack 不得繞過核心 Policy/Audit/租戶隔離（pack 是資料+規則，不是另一條執行路徑）。

## 4. 後果

- **正面**: 一套核心服多垂直；Care Copilot = 第一個 pack 試金石；新垂直不動核心；「AEOS 跨垂直」命題有可驗證的具體形式。
- **負面**: pack 介面契約是高槓桿設計，錯了改動成本大（mitigation：先用 Care Copilot 一個 pack 驗證介面再定型）；pack 可能被當「繞過治理的後門」（mitigation：pack = 宣告式資料+規則，所有執行仍過核心 Policy/Audit，design 須在契約中強制；對抗測試見 threat-model §pack 投毒）。
- **影響範圍**: `05 架構與設計`（core/pack 邊界畫進 container 圖）、`06 API`（pack manifest / skill 載入契約）。
- **可逆性 / 重新評估觸發**: 不可逆傾向（核心 API 邊界定型後改動 blast radius 大）；**freeze 時點**：pack 契約不在 B1 前 freeze，以 Care Copilot（pack #1）跑過 B1 後才鎖版。

## 5. 執行計畫

1. design driver 定義 Vertical Pack 介面契約（manifest schema，baseline = `knowledge-pipeline.md` §1 RawItem/KnowledgeUnit/VerticalPackConfig）— P3
2. 以 Care Copilot 為第一個 pack 驗證介面 — P3（feasibility §8）

---

| 日期 | 審核人 | 備註 |
| :--- | :--- | :--- |
| 2026-05-28 | ARCH | R2 釐清 schema ownership=design / boundary ownership=arch / freeze 時點（C5） |

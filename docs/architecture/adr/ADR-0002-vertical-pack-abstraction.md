# ADR-0002 — Vertical Pack 可插拔抽象（AEOS 橫向化邊界）

> **📋 Status**: Proposed
> **🗓 Date**: 2026-05-28
> **👤 Owner**: `devteam-arch`
> **🔖 Version**: v1
> **🎯 Scope**: cross-team（AEOS 平台橫向化核心邊界）
> **🏷 Tags**: vertical-pack, bounded-context, platform, extensibility, coupling
> **🔗 Feature**: care-copilot
> **🔗 Related KB**: KB-06 §1（maintainability/operability）, KB-11 §1-§3（data 分級邊界）

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: 把「垂直特定」的東西（領域模型 + 詞庫 + skill 集 + persona）收斂成一個**可插拔 Vertical Pack**，AEOS 核心保持**垂直無關**。Care Copilot = 第一個 pack。這是「AEOS 跨所有垂直」命題能否成立的關鍵邊界決策。

| 維度 | 摘要 |
|:---|:---|
| **🎯 Decision** | Option A：Vertical Pack 為可插拔邊界，核心中立 |
| **🤔 Why** | 核心 vs 垂直的 bounded context 切乾淨 = 橫向複用前提；避免每垂直 fork |
| **🚀 Status** | ⏳ Proposed |
| **📊 Reversibility** | 不可逆傾向（核心 API 邊界一旦定型，改動 blast radius 大） |
| **🎯 下一步** | design driver 定 Vertical Pack 介面契約 |

---

## 🎯 Context

- **觸發**：業主本質目標 = AEOS 為**跨所有垂直領域的平台**（非單做 Care Copilot）。feasibility 顯示缺口集中在「垂直特定」（11 工具、直銷關係模型、FTC/FDA 詞庫、異議庫），治理核心則垂直無關。
- **技術限制**：核心若被單一垂直需求污染，將失去複用性，每接新垂直就 fork。
- **相關 NFR**：core 與 pack 之間 coupling 須最小；新增垂直的 blast radius 須限縮在 pack 內。

---

## 📐 Decision Drivers

| Priority | Driver | Weight | Reference |
|:---:|:---|:---|:---|
| 1 | core / vertical 的 boundary 清晰度 | high | feasibility §6 |
| 2 | coupling 最小化（新垂直不動核心） | high | — |
| 3 | 複用性（一套核心服多垂直） | high | foundation/01 北極星 |
| 4 | pack 品質治理（避免 pack 變後門） | medium | 原則 3 |

---

## 🔍 Options Considered

### Option A — Vertical Pack 可插拔（核心中立）

| 維度 | 內容 |
|:---|:---|
| **Pros** | • core 垂直無關，一套服多垂直<br>• 新垂直 = 新 pack，blast radius 限 pack 內<br>• 垂直特定（詞庫/領域模型/skill/persona）有明確收納處 |
| **Cons** | • pack 介面契約設計成本；需治理 pack 品質 |
| **Fit** | 平台要服務多垂直 |
| **Anti-fit** | 只做單一垂直（過度設計） |
| **Cost / Effort** | M（介面設計） |

### Option B — 每垂直 fork 一份

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 短期最快 |
| **Cons** | • N 個垂直 = N 份分岔，治理/修補成本爆炸；違反平台命題 |
| **Anti-fit** | 橫向平台 |

### Option C — 垂直需求 hardcode 進核心

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 單垂直開發直覺 |
| **Cons** | • 核心被污染、失去中立性 → 又一個垂直孤島（feasibility §7 紅旗） |
| **Anti-fit** | 任何第二個垂直 |

---

## ✅ Decision

> [!IMPORTANT]
> **選擇**：Option A — Vertical Pack 可插拔，AEOS 核心保持垂直無關。
>
> **理由**：平台命題（跨所有垂直）要求 core 中立；fork（B）與 hardcode（C）都會在第二個垂直時崩。可插拔 pack 把垂直特定收納在明確邊界內，新垂直的 blast radius 限縮在 pack。接受的 trade-off = pack 介面契約的設計成本，以及須治理 pack 不成為繞過核心 Policy 的後門。

### Vertical Pack 的組成（pack 內 = 垂直特定）
- **領域模型**：該垂直的實體（如直銷的 contact/sample/recruit-funnel）
- **詞庫 / Policy rules**：FTC/FDA 合規詞、產品關鍵字（餵 Policy Engine）
- **Skill 集**：該垂直的 prompt skills（情緒/草稿/異議…）
- **Persona / 語氣設定**

### AEOS 核心保留（core = 垂直無關）
Frozen Runtime / Policy Engine / 多租戶隔離 / Audit / 知識治理 / AgentOps / 多模型 / Quota — 全部不含任何垂直知識。

| 範疇 | 說明 |
|:---|:---|
| **✅ 適用範圍** | core ↔ pack 邊界；新垂直接入機制 |
| **❌ 不適用** | pack 不得繞過核心 Policy/Audit/租戶隔離（pack 是資料+規則，不是另一條執行路徑） |
| **🔓 可逆性** | 不可逆傾向 — 核心 API 邊界定型後改動 blast radius 大，須謹慎 |

---

## 📊 Consequences

### ✅ Positive
- 一套核心服多垂直；Care Copilot = 第一個 pack 試金石
- 新垂直不動核心（coupling 最小、blast radius 限 pack）
- 「AEOS 跨垂直」命題有可驗證的具體形式

### ⚠️ Negative
> [!WARNING]
- pack 介面契約是高槓桿設計，錯了改動成本大（mitigation：先用 Care Copilot 一個 pack 驗證介面，再定型）
- pack 可能被當「繞過治理的後門」（mitigation：pack = 宣告式資料+規則，所有執行仍過核心 Policy/Audit；design driver 須在契約中強制）

### 🎯 Follow-up Work
| Action | Owner | Due | Reference |
|:---|:---|:---|:---|
| 定義 Vertical Pack 介面契約（manifest schema） | devteam-design | P3 | — |
| 以 Care Copilot 為第一個 pack 驗證介面 | devteam-design | P3 | feasibility §8 |

### 📉 影響的下游文件
| Doc | Impact |
|:---|:---|
| `docs/architecture/c4-l2-care-copilot.md` | core / pack 邊界畫進 container 圖 |
| `docs/api/` | pack manifest / skill 載入契約 |

---

## 🔗 Links
| Asset | Path |
|:---|:---|
| **Feasibility** | [`docs/architecture/feasibility-AEOS-x-care-copilot.md`](../feasibility-AEOS-x-care-copilot.md) §6 |
| **北極星** | `docs/foundation/01-north-star.md`（工廠跨垂直） |
| **KB references** | [[06_quality_attributes_catalog]] · [[11_data_and_stack_catalog]] |

---

## ✍️ Sign-off
- [ ] **Architect** (owner): ____________ / Date: ____________
- [ ] **Tech Lead**: ____________ / Date: ____________

---

**End of ADR**

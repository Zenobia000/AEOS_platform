# ADR-0001 — 採 nanobot 為 Frozen Runtime 底層 + AEOS 治理包覆

> **📋 Status**: Proposed
> **🗓 Date**: 2026-05-28
> **👤 Owner**: `devteam-arch`
> **🔖 Version**: v1
> **🎯 Scope**: cross-team（AEOS 平台核心 runtime）
> **🏷 Tags**: runtime, agent-harness, frozen-runtime, mcp, tenant-isolation
> **🔗 Feature**: care-copilot
> **🔗 Related KB**: KB-11 §4-§7（stack 對比）, KB-10 §1-§2（failure mode）, KB-08（MCP/API）

---

## 📋 Executive Summary

> [!TIP]
> **TL;DR (30s)**: 選 **nanobot（Python）作為 AI 員工的 agent runtime 底層**，外加 AEOS 三層治理包覆（凍結 / 多租戶 / Tool Gateway+Policy）。適用於需要 agentic MCP 整合外部系統的員工 runtime；**不適用**把 nanobot 裸跑生產。

| 維度 | 摘要 |
|:---|:---|
| **🎯 Decision** | Option A：nanobot（Python）+ AEOS 治理包覆 |
| **🤔 Why** | Python 同語言 + 原生 MCP/agentic + 即 `02 §4.4.2` 既選的「nanobot 類」具體實作 |
| **🚀 Status** | ⏳ Proposed |
| **📊 Reversibility** | 半可逆（包覆而非 fork，可換底層；但會影響 design/ops 下游） |
| **🎯 下一步** | design driver 定義治理包覆介面；ops 定 runtime 部署 |

---

## 🎯 Context

- **觸發**：feasibility（`docs/architecture/feasibility-AEOS-x-care-copilot.md` §4）確認 **MCP/plugin 整合外部系統需要 agentic**（tool-calling 編排），且業主要求**底層全 Python**。
- **技術限制**：AEOS 設計與 Care Copilot 後端皆 Python(FastAPI)；既有 legacy ADR-0002 規定 Frozen Runtime（學習/生產分離）、legacy ADR-0007 規定多租戶隔離。
- **相關 NFR**：blast radius 須限縮在單一 tenant；MCP 工具呼叫須過 Policy + Audit（原則 3）。
- **既有決策延續**：`02 §4.1 / §4.4.2` 已把「nanobot 類」列為 Production Frozen Runtime 候選 — 本 ADR 是其落地。

---

## 📐 Decision Drivers

| Priority | Driver | Weight | Reference |
|:---:|:---|:---|:---|
| 1 | 與 Python 底層一致（降跨語言 coupling） | high | feasibility §4 |
| 2 | 原生 agentic + MCP（整合外部系統） | high | KB-08 |
| 3 | 可被 AEOS 凍結 + 多租戶包覆（blast radius） | high | legacy ADR-0002 / legacy ADR-0007 |
| 4 | Time-to-market（現成 vs 自建） | high | foundation/02 |
| 5 | 多模型 + prompt caching（成本） | medium | KB-11 §4 |

---

## 🔍 Options Considered

### Option A — nanobot（Python）+ AEOS 治理包覆

| 維度 | 內容 |
|:---|:---|
| **Pros** | • Python ≥3.11 同語言，零跨語言 coupling<br>• 原生多 MCP server/SSE/auth + 小可讀 agent loop<br>• 原生 openai+anthropic+fallback（= §13 多模型）+ prompt caching<br>• 內建 cron/schedules（補 Care Copilot 排程）<br>• 即 `02 §4.4.2` 既選「nanobot 類」具體實作 |
| **Cons** | • 預設個人單租戶 + 可自我擴展 → AEOS 必須包覆凍結<br>• 上游活躍開發，需釘版本 |
| **Fit** | 需要 agentic MCP 整合、Python 棧、要被治理的員工 runtime |
| **Anti-fit** | 裸跑生產（未包覆） |
| **Cost / Effort** | M（包覆層） |

### Option B — pi（earendil-works, TypeScript）

| 維度 | 內容 |
|:---|:---|
| **Pros** | • agentic 強、coding agent harness 成熟 |
| **Cons** | • **TS 與 Python 底層分裂**（跨語言 coupling）<br>• 偏 coding agent（對映 `02 §4.3` 反模式） |
| **Anti-fit** | Python-only 棧 |
| **Cost / Effort** | M + 雙語維運負擔 |

### Option C — 自建 Python agent runtime

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 完全可控 |
| **Cons** | • 重造 agent loop/MCP/多模型/快取，time-to-market 差<br>• 違反 foundation「驗證前不自動化/不過度建設」 |
| **Cost / Effort** | L |

### Option D — LangGraph（Care Copilot PRD §5 原方案）

| 維度 | 內容 |
|:---|:---|
| **Pros** | • 成熟編排 |
| **Cons** | • 偏 workflow 編排，MCP/channel/memory/排程需另接<br>• 與「小核心 Frozen Runtime」定位不貼 |
| **Cost / Effort** | M |

---

## ✅ Decision

> [!IMPORTANT]
> **選擇**：Option A — nanobot（Python）+ AEOS 治理包覆。
>
> **理由**：Python 同語言消除跨語言 coupling（拒 Option B）；現成 agentic+MCP+多模型+排程使 time-to-market 遠優於自建（拒 Option C）；nanobot 的「小核心 agent loop」比 LangGraph 的 workflow 編排更貼 Frozen Runtime 定位（拒 Option D）。最關鍵：這是 `02 §4.4.2` 既有架構選型的落地，非新賭。接受的 trade-off = 必須自建治理包覆層（凍結 + 多租戶 + Policy），這層正是 AEOS 護城河。

| 範疇 | 說明 |
|:---|:---|
| **✅ 適用範圍** | AI 員工的 agent runtime 底層（員工執行體、MCP 工具整合） |
| **❌ 不適用** | 裸用 nanobot 跑生產；單次 LLM/規則類工具（情緒/合規）不需 agent loop，直呼 LLM 即可 |
| **🔓 可逆性** | 半可逆 — 採「包覆而非 fork」，底層可替換；但牽動 design/ops |

### AEOS 必加的三層治理包覆（boundary）

1. **Frozen Runtime**（legacy ADR-0002）：生產關閉 nanobot 自我擴展（自裝 skill / 自改 prompt / 自由載入任意 MCP）；配置凍結快照，回饋走離線。
2. **多租戶隔離**（legacy ADR-0007）：每位直銷商一個受隔離 runtime context + RLS；blast radius 限單一 tenant。
3. **Tool Gateway + Policy 前置**（原則 3）：MCP 工具呼叫前過 Policy Engine + Audit；外部系統憑證不入 nanobot。

---

## 📊 Consequences

### ✅ Positive
- 零跨語言 coupling；與 AEOS / Care Copilot Python 棧一致
- agentic MCP 整合、多模型、排程、prompt caching 現成 → time-to-market 短
- 兌現既有架構選型，決策連貫

### ⚠️ Negative
> [!WARNING]
- nanobot 預設「個人單租戶 + 可自我擴展」與 AEOS「多租戶 + Frozen」相反 → **必須**建包覆層才能生產，否則違反 legacy ADR-0002/0007（mitigation：包覆層列為 design driver 的 P0）
- 上游活躍開發 → 釘版本 + 包覆而非 fork，降耦合（mitigation：治理層與 nanobot 核心解耦）
- nanobot 未內建 LINE channel（mitigation：Care Copilot pilot 是「草稿+手動貼 LINE」，pilot 不需 LINE API）

### 🎯 Follow-up Work
| Action | Owner | Due | Reference |
|:---|:---|:---|:---|
| 定義治理包覆介面（凍結/租戶/Policy hook） | devteam-design | P3 | — |
| nanobot runtime 部署 + 版本釘選 | devteam-ops | P5 | — |
| 釐清哪些工具走 agent loop vs 直呼 LLM | devteam-design | P3 | feasibility §4 |

### 📉 影響的下游文件
| Doc | Impact |
|:---|:---|
| `docs/architecture/c4-l2-care-copilot.md` | runtime container = nanobot + 包覆 |
| `docs/ops/runbook-care-copilot.md` | nanobot 部署/版本/凍結流程 |

---

## 🔗 Links
| Asset | Path |
|:---|:---|
| **Feasibility** | [`docs/architecture/feasibility-AEOS-x-care-copilot.md`](../feasibility-AEOS-x-care-copilot.md) §4 |
| **延續 ADR** | legacy ADR-0002（Frozen Runtime）· legacy ADR-0007（Tenant Isolation）·`_legacy-dev_docs/02-product-architecture.md` §4.4.2 |
| **KB references** | [[11_data_and_stack_catalog]] · [[10_resilience_patterns]] · [[08_api_design_catalog]] |

---

## ✍️ Sign-off
- [ ] **Architect** (owner): ____________ / Date: ____________
- [ ] **Tech Lead**: ____________ / Date: ____________

---

## Review 修正 R2（2026-05-28，B-6 legacy 依賴鏈）
本 ADR 的 boundary 依賴退役的 legacy ADR-0002（Frozen Runtime）/ legacy ADR-0007（Tenant Isolation）。為免可追溯性斷裂：**被依賴的 legacy 決策內聯重述於下，視為本 ADR 的一部分**（不需回溯 _legacy-dev_docs 即可實作）：
- **Frozen Runtime**（原 legacy ADR-0002）：上線配置（prompt+知識快照）凍結;生產不可自我學習改行為;回饋走離線改版。
- **Tenant Isolation**（原 legacy ADR-0007）：RLS + 應用層雙重;跨租戶預設 deny;blast radius 限單 tenant。
> 後續可選擇將此二者正式重發為新 docs/ ADR-0005/0006，或維持本內聯。

---

**End of ADR**

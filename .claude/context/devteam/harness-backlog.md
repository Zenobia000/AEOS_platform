# Harness Backlog — .claude 自身的設計缺失與改善 TODO

> **這是什麼**：追蹤 **harness 本身**(skills / KB / hooks / linter)的設計缺失與改善項,不是 care-copilot 產品文件的 gap(那在 `docs/strategy/docs-gap-audit.md`)。
> **🗓 Last updated**: 2026-05-29 · **Owner**: harness maintainer(CEO + claude)

---

## ✅ 已解（本批）

### HB-1 — KB-to-KB 漂移無機械防護 → **L1+L2 已實作（2026-05-29）**
- **L1 single-source + cross-ref**：建 `devteam_knowledge_base/_registry.json` 為 gates/roles/diagrams/feature_bindings 的單一真相；KB-01/04/07 + INDEX.md 加 cross-ref「枚舉只在 registry，不複製」。
- **L2 機械驗**：linter C9 改讀 `_registry.json` 的 feature_bindings（消滅原本硬編在 bash 的 gate→owner_doc map）；新增 **C13** 驗 registry ↔ state.json gate IDs / KB-04 required_diagrams evidence / feature owner_doc 存在 / persona↔agent 檔存在。真陽性測過（feature_binding 指錯檔 → C13 報錯）。
- **L3（生成 KB 表）**：defer，除非 lint 證明不夠。
- 殘留：templates→driver→path 枚舉尚未納 registry（漂移風險低，待真發生再加）。

---

## 🔴 開放（設計缺失，待系統化解）

### （目前無開放項；新發現的 harness 設計缺失 append 於此）

<details>
<summary>HB-1 原始描述（已解，保留脈絡）</summary>

#### HB-1 — KB-to-KB 漂移無機械防護
- **問題**：`devteam_knowledge_base/` 內多份 KB 對**同一事實**各自描述,會漂移。已發生案例:**圖歸屬**(誰該畫 State Machine/Sequence/Class/Deployment/Activity)同時活在 **KB-07 §3**(選圖樹)、**KB-01**(職責表)、**KB-04**(gate evidence) → 三者不同步,KB-01/KB-04 漏列 KB-07 規定的必畫圖,導致 critique/gate 不會抓「該畫卻沒畫」(2026-05-29 業主抽查發現)。
- **根因**：`scripts/check-doc-consistency.sh`(C1-C12)只驗 **`docs/` 跨文件**一致性,**不驗 `devteam_knowledge_base/` 內部 KB-to-KB 一致性**。KB 是 prompt-約定,無機械防護。
- **同類風險面**：role 枚舉(KB-01 12 persona / 7 driver / 產品 10 角色)、gate↔persona 對應(KB-04 ↔ KB-01)、template↔driver 對應(KB-03 ↔ skills)、命名 rosetta(KB-01)。任一處改了不同步即漂。
- **本次補丁(治標)**：KB-01 加 cross-ref「圖歸屬以 KB-07 §3 為單一權威」+ crosswalk 補 sd Sequence / ops Deployment+Activity;KB-04 各 gate evidence 補必畫圖。
- **TODO(治本,待做)**：
  1. **single-source + cross-ref 原則**：每個「跨 KB 共享事實」定**唯一權威 KB**,其餘 KB 一律 cross-ref 不複製(如圖歸屬=KB-07、role 枚舉=KB-01 crosswalk)。在 KB 開頭立規。
  2. **擴 linter 查 KB 一致性**(C13+，conditional)：例如解析 KB-07 §3 的 driver→必畫圖 mapping,驗 KB-04 各 gate evidence 是否涵蓋對應必畫圖;或驗 KB-01 crosswalk 的 persona/driver 枚舉與各 skill frontmatter 一致。難點:KB 是半結構化 markdown,需先約定可解析格式(如表格 schema)。
  3. **評估**：KB-to-KB 漂移頻率 vs linter 機械化成本(idiot-index)。若漂移罕見,single-source+cross-ref(治本但靠約定)可能已足;頻繁才值得 linter C13。

</details>

---

## ✅ 已解（歷史）

- **docs/ 跨文件漂移無防護** → 解:`scripts/check-doc-consistency.sh` C1-C12 + Stop hook advisory(commit 851c2e2)。
- **gate↔doc Status 脫鉤 / .meta.json 漏建 / freeze ceremony 卡 ready_to_review** → 解:linter C9/C12 + freeze 補跑(dd68427)。

---

## 📌 Defer（明確延後）
- doc-freshness / auto-regen skill 復原 → 等 handoff 後有 code、`source-paths` 有真對象。
- linter CI 化 / git pre-commit 第二層 → 有遠端多人時。

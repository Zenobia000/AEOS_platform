---
id: ADR-0013
title: Skill Routing Rule — hybrid keyword + LLM intent + fallback default
status: accepted
date: 2026-05-26
deciders: CTO
tier: 1
related: [ADR-0003, MC-005, CR-0001, NFR-001, AUTHORING-GUIDE]
---

# ADR-0013 — Skill Routing Rule

## Context

CR-0001 將 AEOS framework 從「1 個 customer-service/faq-respond skill」擴展為「3-5 vertical skill 並存」。當 inbound message 進來，需要決定走哪個 skill：

- ADR-0003 把 skill registry 定為「per-employee N skill 並存」，但 Phase 1 只有 1 skill 沒實作 routing
- `skill_binding` 表原本只有 `priority` 欄位（多 skill 時的排序），**沒有 routing logic**
- DraftProcessor hardcode 接 `skill_slug` 參數，由呼叫方決定

現在 4 個 vertical 並存（customer-service / hr / it-helpdesk / sales），inbound「請問如何請假」應走 hr，「我的密碼忘了」應走 it-helpdesk，「想了解貴公司產品」應走 sales — **必須有 router**。

候選策略：

| 策略 | 優點 | 缺點 |
|---|---|---|
| **A. Pure keyword** | <10ms 確定性高、不耗 LLM token | 需手動列關鍵字、易漏、難維護 |
| **B. Pure LLM intent classify**（Haiku 4.5 first-turn）| 準、語意理解、不需維護關鍵字表 | +300-800ms latency 吃 NFR-001 §1 P95 ≤5s budget；每則訊息額外 LLM cost |
| **C. Explicit channel binding**（每 channel 綁死 1 skill）| 0 routing latency | 1 channel = 1 skill 太僵化，多 use case 客戶要開多 channel |
| **D. Hybrid（keyword fast path + LLM fallback + default）**| 高頻 80% 走 fast path，低頻 20% 才花 LLM；全沒命中走 default skill | 兩種 evaluator 都要實作；rule schema 較複雜 |

## Decision

**採 D. Hybrid routing**，含 4 種 rule type + priority sort + fallback default：

### Rule evaluation 順序

```
1. 載入 employee 所有 active skill_binding，按 routing_rule.priority ASC 排序
2. for each binding in sorted:
       evaluator = dispatch(binding.routing_rule.type)
       if evaluator.match(message, binding.routing_rule.params):
           return binding.skill_version_id
3. fallback: 回 is_default=true 的 binding（partial unique idx 保證至多 1 個）
4. 若無 default → raise NoSkillBoundError (應在 admin UI 阻止此狀態)
```

### `skill_binding.routing_rule` JSONB schema

```json
{
  "type": "keyword" | "llm_intent" | "channel_match" | "explicit",
  "params": {...},          // 依 type 不同
  "priority": <int>          // 數字小者先評估
}
```

**4 種 rule type 語意**：

| Type | Params 範例 | 評估方式 | Latency |
|---|---|---|---|
| `keyword` | `{"keywords": ["請假", "leave", "請休"]}` | 任一字串在 message.content 子字串命中 | < 5ms |
| `llm_intent` | `{"intents": ["leave_request", "vacation"]}` | 呼叫 Haiku 4.5 做 intent classify，比對命中 | 300-800ms |
| `channel_match` | `{"channel_id": "U1234..."}` | conversation.channel_binding.config['channel_id'] 比對 | < 5ms |
| `explicit` | `{"never_match": true}` | 永不命中（純當 admin disable 用） | < 1ms |

**Priority 慣例**：

| 範圍 | 用途 |
|---|---|
| 0-9 | Critical override（如「kill switch trigger」rule） |
| 10-49 | High-confidence keyword（vertical 專屬詞）|
| 50-89 | LLM intent fallback |
| 90-99 | Default skill 的 routing_rule（通常設 `{}` match-all，但 priority=99 確保最後評估） |

### `is_default` 與 fallback 關係

- `is_default=true` 的 binding 仍可有 `routing_rule`（例如限制只在某 channel 才作 fallback）
- 但 router 評估到所有 rule 都不 match 時，**忽略 default binding 的 routing_rule** 直接回 default
- partial unique idx `uq_skill_binding_default_per_emp` 保證每 employee 最多 1 個 default → router 不會 ambiguous

## Consequences

### 正面

1. **效能可控**：80% 流量 < 10ms（keyword fast path），20% 走 LLM ~300-500ms（Haiku 4.5 cheap），routing p95 < 500ms，仍在 NFR-001 §1 P95 ≤5s budget
2. **Fallback 安全**：任何 message 至少有 default skill catch — 不會「找不到 skill 卡住」
3. **Admin 可調**：CRUD `skill_binding.routing_rule` JSONB 即時生效，不需 redeploy
4. **可觀測**：每次 routing 決策寫 `audit_log` (event_type: `routing.matched` + matched_rule + skill_version_id)，便於 debug 與 SkillOps 統計
5. **向前兼容 Phase 2 ML routing**：未來可新增 `type: ml_classifier`，evaluator dispatch 一行 case 就接上

### 負面

1. **Rule 設計 surface area 增加**：admin 需理解 4 種 type + priority 慣例
   → 由 Admin UI（CR-0001 #6）提供 form-based rule builder 抑制學習成本
2. **Routing 本身有 audit cost**：每則 inbound +1 audit row
   → 接受（audit_log 已是 append-only 設計，IO cost 可忽略）
3. **LLM intent classify 本身可能錯**：fallback 到 default 比錯選一個還安全 → 接受
4. **Stub vertical 的 keywords list 是「設計者腦補」**：pilot 真實對話進來前無法驗證；rule 品質與 test set 一樣是 stub
   → CR-0001 §決策守則 #1 要求每 vertical 跑 KeywordJudge baseline，pass rate < 0.5 不算 demo-ready

### 中性

1. `priority` 欄位語意從「多 skill 排序」變成「routing 評估順序」— 同欄位雙重用途，OK 因為兩者意圖一致（都是「先 try 哪個」）
2. `routing_rule = {}`（空 dict）的語意：match-all。等同 keyword `["",...]` 但更明確。常用於 default skill 的 binding

## Alternatives Rejected

### A. Pure keyword
拒絕原因：vertical 之間 overlap 詞太多（「請」字可能 hr / customer-service / sales 都有），純 keyword 維護成本失控；新增 vertical 時要回頭更新所有現有 keyword list 避免錯路由。

### B. Pure LLM intent
拒絕原因：每則 inbound +300-800ms 在 NFR-001 P95 ≤5s budget 中佔比過大（10-15%）；80% 流量其實是高頻簡單 intent（如「我要請假」），用 LLM 是 overkill 也燒 token。

### C. Explicit channel binding
拒絕原因：1 客戶 = 1 LINE channel 是常態（API-002 §1.1），1 channel 死綁 1 skill 等於「framework 只支援 1 vertical per tenant」，違背 CR-0001 核心目的。可作為「進階管理員手動 override」backdoor 保留（type=channel_match priority 最高），但不作 primary routing。

## Verification

### 實作層

依 CR-0001 §9 #2 `feat/cr-0001-skill-router-service`：

```python
# app/skill/router.py
class SkillRouter:
    async def route(self, message: str, employee_id: UUID) -> SkillVersion:
        bindings = await self._load_bindings(employee_id)  # sorted by priority
        for b in bindings:
            if await self._evaluate(b.routing_rule, message):
                await audit.log("routing.matched", ...)
                return b.skill_version
        default = next((b for b in bindings if b.is_default), None)
        if default is None:
            raise NoSkillBoundError(employee_id)
        await audit.log("routing.fallback", ...)
        return default.skill_version
```

### 測試覆蓋（CR-0001 §6 規劃）

- 4 種 rule evaluator 單元測試（每種至少 match / non-match / edge case 3 例）
- Router 整合測試：priority 順序、LLM intent fallback、default fallback、empty bindings 噴 NoSkillBoundError
- 整體：≥15 個新 unit test

### Quality bar

- KeywordJudge baseline pass rate 證明各 vertical routing 正確性（CR-0001 §決策守則 #1）
- Audit log routing.matched / routing.fallback ratio 監控（< 5% fallback 表示 keyword rule 設計合理）

## Migration Path

不需資料 migration — `skill_binding.routing_rule` 在 #1 schema 已加上 NOT NULL DEFAULT `'{}'`：

- 既存 1 個 skill_binding（customer-service/faq-respond）：`routing_rule={}` + `is_default=true` → router 永遠走 default fallback → 行為等同 multi-skill 啟用前
- 新增 hr / it-helpdesk / sales binding 時，admin 填 routing_rule（keyword list 或 llm_intent 或留空走 LLM）

## References

- CR-0001-multi-vertical-framework.md
- ADR-0003-skill-registry.md（Skill registry 基礎）
- MC-005-skill-registry.md §3.3 skill_binding 表
- NFR-001 §1 P95 ≤5s（routing latency budget）
- AUTHORING-GUIDE.md §4 Description 三鐵律（routing keyword 設計參考心法）

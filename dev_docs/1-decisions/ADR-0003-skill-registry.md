---
id: ADR-0003
title: Skill Registry — Git Monorepo with YAML Manifests
status: accepted
date: 2026-05-14
deciders: CTO
tier: 1
---

# ADR-0003 — Skill Registry 儲存與版本化

## Context

Skill 是 AEOS 的核心資產（白皮書「Skill as Asset」原則）。每個 Skill 必須：
- **版本化**（semver）；可 rollback 到任一歷史版本
- **可審計**（誰改的、何時改的、為什麼改）
- **可測試**（test set 跟 Skill 綁定）
- **可審核**（過 Quality Gate 才能 mark production）
- **跨客戶可重用**（Phase 1 結束抽出 Vertical-X 通用 template）

選項光譜：純檔案系統（Git） ↔ 純資料庫 ↔ Git + DB hybrid。Phase 1 必須**極簡**。

## Decision

**Phase 1：Skill Registry = Git monorepo + YAML manifests。** 不引入額外 DB。

具體結構（在 AEOS code repo 內）：

```
skills/
├── customer-service/
│   ├── faq-respond/
│   │   ├── skill.yaml              # 版本元資料、I/O contract、policy 連結
│   │   ├── prompt/                 # system prompt 模板（按版本檔名）
│   │   │   ├── v1.0.0.md
│   │   │   └── v1.0.1.md
│   │   ├── tests/                  # YAML test cases，與版本綁定
│   │   │   ├── v1.0.0.test.yaml
│   │   │   └── v1.0.1.test.yaml
│   │   └── CHANGELOG.md
│   └── handoff-to-human/
└── shared/                          # 跨垂直可重用元件
```

- **版本即 semver tag**：`customer-service/faq-respond@1.0.1` 來自 git tag
- **每個 Skill 必有 `skill.yaml`** 帶：name, version, owner, status (draft/approved/production/deprecated), policy_refs, test_set_id
- **Quality Gate** = pre-commit hook + CI job：跑 test set、檢查 policy_refs 存在、檢查 changelog 更新
- **Rollback** = git revert + redeploy；無需 DB migration

**何時引入 DB index**：
- Skill 數量 > 100，或者
- 線上需要 sub-second 查詢 Skill metadata，或者
- 多人並行編輯衝突頻繁
- 屆時 DB 只當索引快取，**Git 仍是 source of truth**

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| 純資料庫（PostgreSQL `skills` 表 + JSONB content） | 失去 git diff/blame/PR review 工作流；audit trail 還要自寫 |
| 自寫 Skill Manager UI + 後台 | Phase 1 沒這人力；GitHub PR 已是免費的審核工作流 |
| 用 LangSmith / PromptLayer / Helicone | 鎖在第三方；prompt 是核心資產不該外放 |
| Hybrid（Git + DB 雙寫） | 雙寫一致性問題；兩個 source of truth = 沒有 source of truth |

## Consequences

**Positive**:
- 工程零稅：用既有 git 工作流，免費獲得 diff、blame、PR、review、rollback
- Audit trail 天然存在（git log）
- 新工程師 day 1 即可用熟悉的工具編輯 Skill
- 跨垂直 reuse 透過 `shared/` 目錄與 import 機制顯式表達

**Negative**:
- Skill 查詢需 scan 目錄（Phase 1 規模 < 50 個 Skill 沒問題）
- 非工程師（領域顧問）改 YAML 需學基本 git；初期透過 GitHub Web UI 緩解
- 線上熱更新需 redeploy；用 Skill version pinning + canary 緩解

**Tracking**:
- Skill 數量 monthly count；> 50 開始評估 DB index 必要性
- 觀察「非工程師改 Skill 阻塞 PR」次數；> 5 次 / 月 → 補 Web 編輯介面

## Status

Accepted. Review at Phase 2 初（Day 90+）。

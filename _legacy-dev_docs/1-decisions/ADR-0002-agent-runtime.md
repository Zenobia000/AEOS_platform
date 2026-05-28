---
id: ADR-0002
title: Agent Runtime — Wrap Reference Implementation, Don't Build From Scratch
status: accepted
date: 2026-05-14
deciders: CTO
tier: 1
---

# ADR-0002 — Agent Runtime 選擇

## Context

AEOS 需要一個 agent runtime：管理 LLM 互動、tool calling、session 狀態、conversation memory。Bootstrapped + 90 天 MVP 不可能自建 runtime（這是 6 個月起跳的工程）。

`docs/02-product-architecture.md` 與 `docs/appendices/D-reference-implementations.md` 已評估三個候選：
- **Hermes-Agent**：Node.js + Python；具自我改進（self-improvement）能力 — 但 AEOS 明文「Frozen Runtime」，self-improvement 是反向能力
- **nanobot**：TypeScript/Node 輕量 runtime；無 self-mutation；最貼合 AEOS 「不可變 production」哲學
- **CheetahClaws**：Python 為主，工具管理 30+ KB；偏 coding agent 場景

關鍵原則：**治理層由 AEOS 自寫**（audit log, policy check, tool gateway），不依賴 runtime 內建。runtime 只需穩定、可審計、可包裝。

## Decision

**Phase 1：fork 並包 nanobot 作為內部 runtime**，**所有對外 / 對 LLM / 對 tool 的呼叫都先過 AEOS Governance Layer**（audit + policy + cost tracking）。

具體做法：
- 在 `runtime/nanobot/` 下 vendor nanobot 原始碼（pinned commit）
- AEOS 自己的入口 `EmployeeRuntime` class 包住 nanobot session：每次 LLM call / tool call 前後攔截
- **禁止**直接 export nanobot internals 給上層 code 使用
- Hermes-Agent 的 self-improvement 機制移植到 **Training Room** 子系統（Phase 2 後再啟動），與 production runtime 物理隔離

**Week 4 評估點**：若 nanobot 在 production tool-calling 穩定性 < 95%，啟動 ADR-0002-supersede，評估改包 Hermes 的工具層（不包它的 self-improvement）。

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| 完全自建 runtime | 6 個月工程，bootstrapped 不可能 |
| 直接用 Hermes-Agent（含 self-improvement） | 違反 Frozen Runtime 原則；prod 用 self-mutating agent 是治理災難 |
| LangGraph / CrewAI / AutoGen | 框架黑箱重；違反「Governance-first」；audit log 攔截難 |
| OpenAI Assistants API | 鎖在 OpenAI；違反 ADR-0001 的 vendor 選擇 |

## Consequences

**Positive**:
- 90 天可上線（nanobot 已是 working code）
- Governance Layer 完全自寫，audit / policy / cost 都可控
- Frozen Runtime 與 Training Room 物理隔離，符合白皮書原則

**Negative**:
- vendor nanobot 後需維護 patch（每季 sync upstream）
- 若 nanobot 上游消失或大改 API，要評估 fork-and-own
- 早期 tool-calling 邊界情況需自己踩坑

**Tracking**:
- nanobot upstream weekly check
- 每月統計：tool call 成功率、session 異常率、自寫 patch 行數
- 自寫 patch > 2000 行 → 觸發「是否該 own this fork」的 ADR

## Status

Accepted. Re-evaluate at Week 4 spike result + Phase 1 結束。

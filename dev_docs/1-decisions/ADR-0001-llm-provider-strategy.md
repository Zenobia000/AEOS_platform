---
id: ADR-0001
title: LLM Provider Strategy — Phase 1 Single Provider with Abstraction Seam
status: accepted
date: 2026-05-14
deciders: CTO
tier: 1
---

# ADR-0001 — LLM Provider 策略

## Context

Phase 1 必須在 90 天內讓 pilot 客戶 live。LLM 選擇影響：
- 工程速度（多 provider abstraction 至少多花 2–3 週）
- 月成本（per-token pricing 差異 2–10x）
- 治理可行性（不同 model 對 system prompt、tool use、citation 服從度差很多）
- 鎖入風險（若 provider 漲價或失效，需要 fallback）

Bootstrapped 不能負擔「為理論可移植性而付的工程稅」，但也不能完全鎖入單一 vendor。

## Decision

**Phase 1：單一 provider = Anthropic Claude**，但留**極薄的 LLM client abstraction**（一個 interface, 一個實作）。

- 主力模型：**Claude Sonnet 4.6**（reasoning, tool use, governance behavior 最強）
- 高頻 / 成本敏感任務：**Claude Haiku 4.5**（FAQ、簡單分類、初步意圖判定）
- Prompt caching 強制啟用（cache long system prompts + knowledge context）
- 抽象介面：`LLMClient` interface 定義 `complete(messages, tools) -> response`，目前唯一實作 `AnthropicClient`

**何時新增第二 provider**：
- 達成以下任一條件：(a) Claude 月帳單 > 50K NTD、(b) 出現 SLA 問題、(c) pilot 客戶要求資料主權（本地模型）
- 才花 1–2 週新增 OpenAI / Gemini / 本地 fallback

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| 一開始就建 multi-provider router | 工程稅 2–3 週，Phase 1 沒這時間 |
| 用 OpenAI GPT-4o | tool use / citation 不如 Claude；governance prompt 服從度較差 |
| 用 LangChain / LiteLLM 抽象 | 引入框架依賴，違反「Simplicity over Sophistication」 |
| 純本地模型（Llama, Qwen） | 推理能力對 Phase 1 AI 客服情境不夠；運維成本爆 |

## Consequences

**Positive**:
- 工程速度最大化，2 週內可以接出第一個 demo
- Claude 的 tool use 與 citation 行為原生支援我們的 audit log 需求
- 預留切換空間（Day 1 寫 abstraction 比 Day 90 重構便宜）

**Negative**:
- 短期內鎖在 Anthropic ecosystem；若 Anthropic 漲價需快速反應
- Token cost 比 OpenAI 略高；用 Haiku + prompt caching 緩解

**Tracking**:
- 每月 review LLM 帳單與品質指標；達門檻 → 寫 ADR-0001-supersede 觸發多 provider

## Status

Accepted. Review at Phase 1 結束（Day 90）或月帳單 > 50K NTD 時。

---
id: ADR-0004
title: Deployment Model — Single-Tenant SaaS per Pilot Customer
status: accepted
date: 2026-05-14
deciders: CTO
tier: 1
---

# ADR-0004 — 部署模型

## Context

Phase 1 必須選擇部署架構：
- 多租戶 SaaS（多客戶共用 stack，row-level 隔離）— 工程成本高、出事影響大
- 單租戶 SaaS（每個客戶獨立 stack）— 工程成本低、單客戶可控
- 客戶本地部署（on-prem / 私雲）— 客戶要求資料主權時才考慮

Bootstrapped + 第一個 pilot 客戶情境下，需要：
- 90 天可上線
- 客戶資料安全可承諾（pilot 客戶可能要求「我的資料不會跟別人混在一起」）
- 出事影響範圍可控
- 後續可遷移成 multi-tenant（不能寫死）

## Decision

**Phase 1：單租戶 SaaS — 每個 pilot 客戶獨立 Docker Compose stack，部署在 AEOS 管理的雲端 VM 上**。

具體：
- 每個 pilot 一台 VM（建議 2–4 vCPU, 8 GB RAM 起步，DigitalOcean / Linode / 自己 GCE）
- 一份 `docker-compose.yml` 起 4 個 service：`api`, `worker`, `postgres`, `redis`
- 客戶資料、knowledge cards、conversations 都在該客戶自己的 PG instance
- AEOS code 與 Skill Registry 透過 CI 自動部署到所有客戶 VM（同版本同步）
- **Code 與 Schema 設計從 day 1 就帶 `tenant_id` 欄位**（雖然 Phase 1 每個 VM 只有 1 個 tenant，但 schema 不寫死）

**Phase 2 觸發 multi-tenant 評估**：客戶數 ≥ 5、且運維（patch、deploy、monitor）每週 > 8 小時時，寫 ADR-0007 評估 multi-tenant 遷移。

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| 一開始就建 multi-tenant SaaS | 工程稅 3–4 週（auth、tenant isolation、rate limit per tenant）；Phase 1 沒這時間 |
| K8s + Helm chart per tenant | bootstrapped 不該碰 K8s；單台 VM + docker compose 夠 5 個客戶用 |
| Serverless（Lambda + DynamoDB） | LLM long-running call + agent session state 不適合 stateless；cold start 對話體驗差 |
| 客戶本地部署 | Phase 1 沒能力做 on-prem 支援；客戶若強烈要求，視為 Phase 3 enterprise plan |

## Consequences

**Positive**:
- 90 天可達成；單一 docker-compose.yml 就是部署描述
- Pilot 客戶資料物理隔離；安全承諾簡單
- 一個客戶出事不影響其他客戶
- `tenant_id` 欄位預留，遷 multi-tenant 時 schema 不重做

**Negative**:
- 客戶數 > 5 後運維會變痛；需要建 deploy 自動化（Phase 2 任務）
- 每客戶 VM 成本 ~ 1500 NTD/月；定價要 cover 這個（已含在月費 model 內）
- 跨客戶 Skill 改版需逐 VM rollout；用 CI + canary 緩解

**Tracking**:
- 每月：客戶數 × 運維工時；觸到 > 8h/週 → 觸發 multi-tenant ADR
- 每客戶 VM 成本 vs 月費 ratio；< 30% 健康

## Status

Accepted. Review at Phase 2 初（客戶 ≥ 5 或運維週工時 > 8h）。

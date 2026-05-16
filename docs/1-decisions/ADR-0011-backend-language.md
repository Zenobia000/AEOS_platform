---
id: ADR-0011
title: Backend 語言 — Phase 1 採用 Python 3.12 + FastAPI
status: accepted
date: 2026-05-17
deciders: CTO
tier: 1
supersedes: SAD-v0.1 §3.1 (將 "Python or Node.js 待 Week 1 Day 1 決定" 結案)
---

# ADR-0011 — Backend 語言：Python 3.12 + FastAPI

## Context

`SAD-v0.1 §3.1` 將 API + Worker 的語言標記為「Python or Node.js 待 Week 1 Day 1 決定」。
此決策是 S2 開工的硬阻塞：影響 ORM、async 模式、queue client、validation、testing stack、ADR-0001 的 LLM client 實作、與後續每一個 MC 的範例程式。

決策因素：
- **生態相容性**：pgvector、Anthropic SDK、LINE SDK、Pydantic schema validation 都有成熟 Python 實作
- **隊員語言主力**：CTO 兩語皆可；隊員 A 主力為 Python（在 Week 1 Day 1 確認）
- **後續文件預設**：SAD / MC-001~011 / db-schema / API-001 範例皆以 Python 風格描述
- **工程速度**：FastAPI + Pydantic v2 + SQLAlchemy 2.0 是 90 天 MVP 的成熟組合
- **observability**：OpenTelemetry Python 自動 instrumentation 對 FastAPI/SQLAlchemy/Redis 開箱即用

## Decision

**Phase 1 backend 採用 Python 3.12 + FastAPI**。

技術棧鎖定：

| 層 | 選擇 | 理由 |
|---|---|---|
| 語言 | Python 3.12 | 主力人員熟練 + LLM/RAG 生態最齊 |
| Web framework | FastAPI | async 原生、OpenAPI 自動生成、Pydantic 整合 |
| Schema validation | Pydantic v2 | FastAPI 內建依賴；DTO 與 settings 統一 |
| ORM | SQLAlchemy 2.0 (async) | RLS context 透過 session-scoped variable 注入 |
| Migration | Alembic | SQLAlchemy 官方搭配 |
| Queue | Redis list + DLQ pattern（`redis-py`）| ADR-0008 已決：不引入 Celery/RQ |
| Worker | 同 image 不同 entrypoint | SAD §3.1：「Worker 同 API 程式碼，不同 cmd」 |
| HTTP client | `httpx` (async) | LINE / Anthropic 呼叫統一 |
| Test | `pytest` + `pytest-asyncio` + `pytest-cov` | TEST-001 §4 coverage ≥ 80% gate |
| Lint / format | `ruff` + `ruff format` | 取代 black + isort + flake8 |
| Type check | `mypy` (strict mode) | CI block on error |
| Dep manager | `uv` 或 `poetry`（S1-2 期間定案）| 兩者皆可，本 ADR 不卡死 |

## Alternatives Considered

| 方案 | 拒絕原因 |
|---|---|
| Node.js (TypeScript) | 隊員 A 非 TS 主力；ORM/migration/queue 需逐一選型，2~3 週工程稅；後續所有 MC 文件需重寫範例 |
| Python + Django | Django 偏 sync + 重 ORM；FastAPI 對 async 與 OpenAPI 支援更乾淨 |
| Python + Flask | 缺 async 原生支援；validation 需另套 |
| Go | 隊員不熟；RAG/LLM 生態薄；team velocity 受影響 |

## Consequences

**Positive**:
- S2 開工零等待：直接 `uvicorn main:app` 起骨架
- 與 ADR-0001（Anthropic SDK 為主）天然吻合
- Pydantic v2 同時是 LLM output validation 工具（MC-009 用到）

**Negative**:
- Python async 在 CPU bound 任務（embedding 批次處理）需 worker pool 處理；S2 KB ingest 需注意
- 部署 image 較大（Python + 依賴）vs Node alpine；non-blocker，per-tenant VM 規格充裕

**Tracking**:
- 若 Phase 2 出現高並發場景超過 single-process 處理能力，評估 ASGI worker 數或部分服務改寫
- 不寫進本 ADR 的 dep manager 選擇（uv vs poetry）於 S2 專案骨架 commit 時定案

## Status

Accepted. 不設 review 時點；Phase 2 若有重大語言重選需求需新 ADR supersede。

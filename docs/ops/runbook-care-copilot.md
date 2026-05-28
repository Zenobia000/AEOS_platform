# Runbook + SLO — care-copilot（Pilot）

> **Status**: draft · **Owner**: `devteam-ops` · **Date**: 2026-05-28 · **Feature**: care-copilot
> Pilot 規模：1 tenant、單容器、單一 oncall（CEO）。對應 NFR、ADR-0011、Observability 需求。

---

## 1. 部署（nanobot runtime + AEOS 包覆）

```
單台 VM（~$50/月，foundation/02）
├── nanobot runtime（Python，釘版本 — ADR-0011 negative #2）
│    └── AEOS 治理包覆：Frozen / Tenant(RLS) / Tool Gateway+Policy
├── Postgres + pgvector（contact / knowledge_chunk / message / audit）
└── env：ANTHROPIC_API_KEY、DATABASE_URL（secrets 不進 git）
```
- **凍結檢查**：部署前確認 nanobot 自我擴展（自裝 skill/自改 prompt/自由載 MCP）已關（ADR-0011）。
- **版本**：nanobot 釘 exact version；升級走 staging 驗證。

## 2. Kill Switch（鐵律，第一週就有）

- 機制：單一 flag（DB 或 env）→ runtime 讀取，**30s 內停止產草稿與回發**。
- 觸發時機：跨租戶外洩、外送踩線、成本失控、品質崩。
- 操作：`set killswitch=on` → 驗證無新草稿產生。

## 3. SLO / SLI（Pilot best-effort，非正式承諾）

| SLI | 目標 | Alert |
|:---|:---|:---|
| 草稿生成成功率 | best-effort | 連續失敗 → 通知 oncall |
| 草稿延遲 p95 | < 5s | 持續 > 10s 告警 |
| **跨租戶違規數** | **= 0** | **> 0 → P0 即停（killswitch）** |
| **外送踩線數** | **= 0** | **> 0 → P0** |
| 成本 / 直銷商 / 日 | ≤ $0.30 | 超 quota → circuit breaker 降階 + 告警 |
| 草稿採用率 | 監控趨勢 | 崩（<40%）→ 觸發 Kill 重評 |

## 4. Incident Response

| 事故 | 處置 |
|:---|:---|
| 跨租戶外洩 | killswitch → 稽核範圍 → 通報 → RCA（RLS 破口） |
| 外送踩線 | killswitch → 撈該則 audit → 補詞庫 |
| LLM API 中斷 | fallback_models；持續中斷 → 暫停 pilot 通知教練 |
| 成本暴衝 | circuit breaker 降階；查異常用量來源 |
| 資料復原 | 最壞 15 分鐘內（PRD §6）；從備份還原 |

## 5. Observability（實作 arch C4 列的需求）
- Metrics：Prometheus/簡易；Logs：structured + `conversation_id`；Traces：draft→policy→audit；Alerts：上表 P0 條件。
- Pilot 可先 log to stdout + 一張採用率列表（foundation/02），完整 stack 過早。

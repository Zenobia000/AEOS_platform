# aeos-mvg — W1 切片（離線打 B1）

最薄垂直切片，驗證**核心賭注 B1**：一坨真實混亂知識，能不能在數天內變成「人類願意採用的草稿回覆」。
依 `../docs/foundation/02-mvg-build-sheet.md` 與 `03-validation-and-kill.md`。

> **W1 範圍**：純離線。**不接 DB、不接 LINE。** 知識整份當 cached system prompt（prompt caching 控成本），對測試集跑 `draft → judge`，印出採用率與 B1 裁決。RAG/pgvector、LINE、審核 UI 留 W2+。
>
> **runtime 說明**：W1 直接用 Anthropic SDK（`pi`/`nanobot` 等 agent runtime 是 MCP/外部系統整合層才需要 — 見 `../docs/architecture/feasibility-AEOS-x-care-copilot.md` §4）。本切片是該 spike 的起點骨架。

## 元件

```
aeos_mvg/
├── config.py      # env + Anthropic client；模型常數（草稿 opus-4-7 / judge haiku-4-5）
├── knowledge.py   # 載入知識 markdown（W1 = 整份當 cached system prompt）
├── llm.py         # generate_draft（opus + 知識快取）/ judge_draft（haiku, 結構化判定）
├── draft.py       # CLI：對單一問題產草稿（W1 step ①②）
└── eval.py        # CLI：對測試集打 B1（W1 主交付）
data/
├── knowledge.md   # 範例知識（placeholder，換成真 pilot 客戶知識）
└── testset.csv    # 範例測試集（question,reference；換成真 50 題）
```

## 跑法

```bash
cp .env.example .env          # 填 ANTHROPIC_API_KEY
poetry install
poetry run python -m aeos_mvg.draft "你們週末有出貨嗎？"     # 單題草稿
poetry run python -m aeos_mvg.eval                            # 對測試集打 B1
```

## B1 門檻（foundation/03）

- 🟢 GO：原樣 approve ≥ 50% **且** 總採用 ≥ 70%
- 🔴 KILL：總採用 < 40%
- 🟡 PIVOT：介於之間，限再調 2 輪

## 注意

- **真資料才算數**：`data/` 是 placeholder。打 B1 前換成 1 位真 pilot 客戶的真知識 + 真 50 題測試集（需先簽 pilot，見 foundation/03 OQ-002）。
- **prompt caching**：知識 ≥ ~4096 tokens 才會觸發快取（opus-4-7）；範例知識較短可能不快取（`eval` 會印 cache_read，0 代表沒快取到）。真客戶 KB 通常夠大。

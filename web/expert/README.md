# AEOS Expert Console (Draft Mode UI)

Vite + React 19 + TypeScript + Tailwind 3 — Phase 1 內部 UI，讓 expert 對 AI 產出的 draft 進行 1-click approve / edit-and-send / reject。

對應後端：`app/api/expert.py`（FastAPI router `/api/v1/expert/*`）+ `app/services/expert_review.py`。

## Quickstart

```sh
cd web/expert
npm install
npm run dev          # http://localhost:5173 → proxy /api → http://localhost:8000
```

後端需先啟動：
```sh
uv run uvicorn app.main:app --reload --port 8000
```

## Scripts

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | Vite dev server (port 5173) |
| `npm run build` | tsc + vite build → `dist/` |
| `npm run preview` | 跑 `dist/` |
| `npm run typecheck` | tsc 嚴格檢查 |
| `npm run test` | Vitest unit/integration（jsdom） |
| `npm run test:watch` | Vitest watch |

## 環境變數

| Key | 預設 | 用途 |
| --- | --- | --- |
| `VITE_API_BASE` | `http://localhost:8000` | dev proxy target |

## 限制（Phase 1）

- **無 auth**：UI 內 expert_id 是輸入框（存 localStorage）。S5 接 MFA + RBAC 後改成 server-side session/JWT。
- **無 WebSocket**：目前用手動「重新整理」按鈕；S3 可考慮 SSE/long-poll。
- **單 tenant**：無 tenant 切換 UI；後端 query string `tenant_id` 已預留。

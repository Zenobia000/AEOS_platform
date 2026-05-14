# 附錄 B. 決策矩陣

> **本檔對應原 whitepaper.md 附錄 B (行 3651-3678)**
> 對應主檔：02-product-architecture.md / 04-strategy-business.md
> 最後同步：2026-05-14

---

### B. 決策矩陣

#### B.1 Runtime 選型

| 場景 | 推薦 | 不推薦 |
| :--- | :--- | :--- |
| MVP / PoC | nanobot fork + 簡單 Policy Wrapper | 自建 Runtime (太貴) |
| 企業內部 Beta | nanobot 重度 wrap + Tool Gateway | 直接用 Hermes / 桌面工作台 |
| 商用平台 | 自建 Enterprise MCP Host | 任何單一開源框架裸用 |
| Coding 內部助理 | CheetahClaws (內網限定) | 對外客服 |
| 訓練室 | Hermes-style + 自建沙盒 | nanobot (太輕) |

#### B.2 LLM 選型

| 場景 | 推薦 |
| :--- | :--- |
| 高度機密 / 工廠內網 | Local Model (Ollama / vLLM) + Private Gateway |
| 一般 SaaS | 公有 LLM (簽 DPA) + 多供應商 Fallback |
| 跨國 | 區域化部署 + 資料主權考量 |
| 政府 | Sovereign LLM / On-prem |

#### B.3 是否導入自我學習

| 條件 | 建議 |
| :--- | :--- |
| 有專家陪訓資源 + Skill 審核流程 + Sandbox + Red Team | ✅ 導入 (Phase 2+) |
| 缺任一條件 | ❌ 暫不導入，Phase 1 用 Frozen Runtime |

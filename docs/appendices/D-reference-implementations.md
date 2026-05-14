# 附錄 D. 參考實作定位速查表

> **本檔對應原 whitepaper.md 附錄 D (行 3716-3726)**
> 對應主檔：02-product-architecture.md
> 最後同步：2026-05-14

---

### D. 參考實作定位速查表

| 工具 | 在 AEOS 的位置 | 採用方式 |
| :--- | :--- | :--- |
| Hermes Agent (類) | Training Room Engine | 受控 Wrap，不接 Production |
| nanobot (類) | Production Runtime 候選 | 重度 Wrap + Policy 包覆 |
| CheetahClaws (類) | Internal Automation Worker / Tool Registry 設計參考 | 後台 PoC，不對客戶 |
| 桌面工作台 (洩露源類) | UX 研究素材 | 不採用 |
| Claude Code / Cursor / Claude Desktop | MCP Host 行為參考 | 不採用為平台 Runtime |
| ClawWork (類評估) | Evaluation Service 設計範式 | 自建 Evaluation Harness |

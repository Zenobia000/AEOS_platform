# 附錄 A. 術語表

> **本檔對應原 whitepaper.md 附錄 A (行 3626-3650)**
> 對應主檔：全部
> 最後同步：2026-05-14

---

### A. 術語表

| 術語 | 定義 |
| :--- | :--- |
| AEOS | AI Employee Operating System |
| AI Employee | 受治理的執行物件，由 Role + Skill + Policy + Tool 組成 |
| Skill | 可版本化的能力包，含 Prompt、Schema、Test、Risk Level |
| Tool | 受控的外部能力，必經 Tool Gateway |
| MCP | Model Context Protocol，工具協議標準 |
| MCP Host | 連接 LLM 與 MCP Server 的執行環境 |
| Tool Gateway | 工具閘道，負責權限、稽核、遮罩、限流 |
| Policy Engine | 策略引擎，執行業務規則與權限判斷 |
| Training Room | 訓練室，允許自我學習的隔離環境 |
| Frozen Runtime | 凍結執行環境，禁止自我修改 |
| SkillOps | AI 員工的 MLOps |
| Drift | 漂移，指 Skill / Knowledge / Behavior 的退化 |
| Canary Release | 小流量灰度發布 |
| Tenant | 租戶，最高隔離單位 |
| Multi-tenant | 多租戶隔離（不同於 multi-user） |
| Red Team | 紅隊測試，對 AI 進行對抗測試 |
| RAG Grounding | 檢索增強生成的來源綁定 |
| PII | Personally Identifiable Information |
| RBAC / ABAC | 角色 / 屬性 為基礎的存取控制 |
| Kill Switch | 一鍵停用機制 |

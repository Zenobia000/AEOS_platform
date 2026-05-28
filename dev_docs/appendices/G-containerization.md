# 附錄 G. 容器化部署策略

> **本檔對應原 whitepaper.md 附錄 G (行 3794-3865)**
> 對應主檔：02-product-architecture.md
> 最後同步：2026-05-14

---

### G. 容器化部署策略

> 對應 §5 系統架構與 §11 安全合規。本附錄提供具體部署型態建議。

#### G.1 哪些元件適合容器化

| 元件 | 容器化必要性 | 理由 |
| :--- | :--- | :--- |
| AI Employee Runtime | 高 | 多版本並存、快速擴縮 |
| MCP Server / Tool Adapter | 高 | 風險隔離、獨立停用 |
| Sandbox Runner | 高 | 訓練室隔離 |
| Evaluation Worker | 高 | 批次任務、資源彈性 |
| Document Parser / Knowledge Indexer | 高 | 異步任務、可橫向擴展 |
| Webhook Receiver | 中 | 視流量決定 |
| Admin Console | 中 | 標準 Web 部署即可 |
| Audit Service | 高 | 高可用、分流寫入 |

#### G.2 工具風險分層的容器隔離

不同風險等級的 MCP Adapter 應採用不同隔離強度：

| 風險等級 | 範例 | 容器策略 |
| :--- | :--- | :--- |
| 低 | FAQ 查詢、Knowledge Search | 共用 Pod / 命名空間 |
| 中 | 訂單查詢、客戶資料查詢 | 獨立 Pod、獨立 ServiceAccount |
| 高 | 退款申請、CRM 寫入 | 獨立 Namespace、Network Policy 隔離 |
| 極高 | 會計操作、權限變更 | 獨立 Cluster 或專屬 VPC |

每個 Container 應具備：

```
- 獨立權限 (least privilege)
- 獨立 NetworkPolicy
- 獨立 Secret (Vault 注入)
- 獨立 Log Stream
- 獨立 Rate Limit
- 獨立停用機制 (Kill Switch)
```

#### G.3 客戶部署型態矩陣

不應採用「每客戶一套完整 K8s」的反模式，過度工程化將導致維運成本失控。建議依客戶等級採用對應策略：

| 客戶等級 | 部署型態 | 隔離強度 | 維運成本 |
| :--- | :--- | :--- | :--- |
| 小型客戶 | Multi-tenant SaaS，共用平台 | 邏輯隔離 (DB Schema / 命名空間) | 最低 |
| 中型客戶 | 共用核心平台，關鍵 Adapter 獨立 Container | 混合隔離 | 中 |
| 大型企業 | 專屬 Tenant Runtime，專屬 Adapter | 物理隔離 (獨立 Namespace) | 高 |
| 高法遵產業 | 私有部署 / VPC / On-premise | 完全隔離 | 最高 |

#### G.4 三平面部署原則

呼應 §5.4 三平面分離，部署層次應：

```
Control Plane    → 全平台共用 (高可用、跨區複製)
Data Plane       → 依租戶等級隔離 (運算與儲存)
Governance Plane → 全平台共用，但稽核資料按租戶分區
```

**設計推論**：Control Plane 升級不應影響 Data Plane 線上服務；單一 Tenant 故障不應影響其他 Tenant；Governance Plane 即使全部 Data Plane 故障仍可獨立查詢稽核紀錄。

#### G.5 反模式警示

| 反模式 | 後果 | 正確做法 |
| :--- | :--- | :--- |
| 一開始就 K8s + Service Mesh + 多區 HA | 維運成本壓垮團隊 | Phase 1 先用 Docker Compose；K8s 留 Phase 3 |
| 每客戶一個獨立 Cluster | 升級困難、成本失控 | 多租戶 SaaS + 邏輯隔離 |
| 所有 Adapter 共用單一 Container | 單一漏洞影響全平台 | 依風險分層隔離 |
| Secret 寫入 ConfigMap | 嚴重資安漏洞 | 使用 Vault / Sealed Secrets |
| 所有日誌寫入單一資料庫 | 法遵稽核困難 | 依租戶分區 + 不可變儲存 |

# 附錄 F. 客戶 Onboarding 資料盤點清單

> **本檔對應原 whitepaper.md 附錄 F (行 3733-3793)**
> 對應主檔：03-onboarding-operations.md
> 最後同步：2026-05-14

---

### F. 客戶 Onboarding 資料盤點清單

> 對應 §17.3 Phase 0 需求盤點。客戶導入 AEOS 前，平台方需取得以下四類資料以完成 Tenant 配置與 Skill 建模。

#### F.1 業務資料 (Business Data)

```
□ 客服問題分類 (Issue Taxonomy)
□ 常見 FAQ 與標準答案
□ 產品 / 服務說明
□ 退換貨政策
□ 保固條款
□ 客訴處理 SOP
□ 人工接手規則
□ 客服語氣規範
□ 禁止承諾事項清單
□ 行業特殊禁令 (金融 / 醫療 / 法律)
```

#### F.2 系統資料 (System Inventory)

```
□ 目前客服入口 (Web / LINE / Email / 電話)
□ 目前 CRM 系統 (廠牌 / 版本)
□ 目前 ERP / 進銷存 / 會計系統
□ 是否提供 API / Webhook
□ API 文件 / Postman Collection
□ 測試環境 URL 與帳號
□ 認證方式 (OAuth / API Key / JWT / mTLS)
□ Rate Limit 與配額
□ 資料欄位說明文件
□ Schema 變更頻率
```

#### F.3 資安資料 (Security Requirements)

```
□ 是否允許 SaaS 部署
□ 是否需要私有部署 (On-prem / VPC)
□ 個資處理規範 (GDPR / PDPA / HIPAA)
□ 資料保存期限
□ 是否需要 Audit Log 匯出
□ 是否需要 SSO 整合 (Okta / Azure AD / Google Workspace)
□ 是否需要 IP Whitelist
□ 加密要求 (Encryption at Rest / In Transit)
□ 資料主權地理限制
```

#### F.4 驗收資料 (Acceptance Criteria)

```
□ 測試題庫 (含正確答案)
□ 不可回答題目清單
□ 高風險題目清單
□ 必須轉人工的案例
□ 客服主管評分規則
□ 上線門檻 (對應 §21.1)
□ 灰度發布比例計畫
□ 應急聯絡窗口
```

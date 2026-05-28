# 附錄 C. 上線前檢核清單

> **本檔對應原 whitepaper.md 附錄 C (行 3679-3715)**
> 對應主檔：03-onboarding-operations.md / 06-governance-security.md
> 最後同步：2026-05-14

---

### C. 上線前檢核清單

#### C.1 治理檢核
- [ ] 所有 Skill 都有 Owner、Version、Test Cases
- [ ] 所有 Tool 都有 Permission Contract
- [ ] Policy Engine 預設 deny
- [ ] Audit Log 寫入失敗即整筆回滾
- [ ] 一鍵停用 / 回滾測試通過

#### C.2 安全檢核
- [ ] PII Masking 全鏈路覆蓋
- [ ] Cross-tenant 隔離測試通過
- [ ] 紅隊 7 種樣式攔截率 ≥ 99%
- [ ] 秘密 (API Key、憑證) 集中於 Vault
- [ ] 所有外部呼叫經 Tool Gateway

#### C.3 合規檢核
- [ ] DPA 已簽
- [ ] 客戶資料保留期限已設定
- [ ] Right to Erasure 流程可執行
- [ ] Audit Log 保留期限符合法規
- [ ] AI 服務透明標示

#### C.4 運營檢核
- [ ] Dashboard 涵蓋效率 / 品質 / 風險 / 成本四類
- [ ] Drift 偵測規則已配置
- [ ] On-call 值班表已建立
- [ ] 事件響應 Runbook 已寫
- [ ] Canary 發布流程驗證

#### C.5 商業檢核
- [ ] 計價模型已定 (席次 / Token / Skill)
- [ ] Cost Attribution 可按租戶切分
- [ ] Quota 機制已上線
- [ ] SLA 已寫入契約
- [ ] Liability Cap 已協議

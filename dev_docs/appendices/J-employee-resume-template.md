# 附錄 J. AI 員工履歷模板

> **本檔對應原 whitepaper.md 附錄 J (行 4004-4048)**
> 對應主檔：03-onboarding-operations.md
> 最後同步：2026-05-14

---

### J. AI 員工履歷模板

> 對應 §18.12 AI 員工履歷。每位 AI 員工上線前必產出，作為與客戶溝通的視覺化交付物。

```yaml
employee_profile:
  name: Sunny Support Agent
  role: 一線客服助理
  tenant: Company A
  hired_at: 2026-05-14

  knowledge_summary:
    faq_count: 128
    product_count: 36
    policy_count: 13
    last_kb_update: 2026-05-13

  capabilities:
    can_handle:
      - 基礎產品問答
      - 退換貨規則說明
      - 客訴初步分類
      - 建立工單草稿
    cannot_handle:
      - 退款承諾
      - 法律爭議
      - 價格特殊折扣
      - 帳務修改

  recommended_launch:
    initial_mode: 保守模式 (L1)
    duration: 2 週
    upgrade_criteria:
      - FAQ 正確率 ≥ 90%
      - 客訴升級轉介率 ≥ 95%
      - 連續 7 日無重大事故
    upgrade_target: 標準模式 (L2)
```

---

**文件結束**

*本白皮書是活文件 (Living Document)，將隨產品迭代與市場變化持續更新。*
*版本歷史將記錄於 `CHANGELOG.md`。*

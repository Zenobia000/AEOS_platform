# Transcript — DevTeam Harness 缺口補齊規劃

> Drill-down 用。業主預設不看。議題：F4 PO Ordered Backlog / F5 JTBD+Value Hypothesis / F6 Threat Model。
> 與會：PM、PO、BA、SA、UX、Architect、SD、QA。2 rounds。

---

## Round 1 — 初始立場（並行）

**[PM]** F5 傾向 (A) prd.md 必填段 — value hypothesis 是 KPI 上游，沒它 KPI 是沒錨點的數字；獨立 template 會跟 PRD 脫鉤沒人讀。[VALUE_DECISION_NEEDED] value-hypothesis 要不要強制 counter-metric？主張要。F4 傾向 (B) out of scope，但 PRD 要有 prioritized scope slice（= C 精神，MoSCoW）。F6 (C) 條件式，PII/金流/auth 才強制。@PO scope slice 算不算偷渡 ordered backlog？@SA JTBD 要到能拆 acceptance 的顆粒度嗎？

**[PO]** F4（主場）選 (C) 但 ownership 收口：spec 產生器沒 sprint 就沒 backlog 排序對象；PRD 必須有 prioritized scope slice（P0/P1/P2 + 排除），PM single owner；「Ordered Backlog」降級為 scope slice，Define exit 改「scope 已排序」。F5 (A) 必填段（value hyp = 排序依據）。F6 (C) 條件式。[VALUE_DECISION_NEEDED] Ordered Backlog 改寫 scope slice 動交付物清單，業主拍。@pm scope slice single owner 你接得住嗎？@arch F6 門檻你定。

**[BA]** F4 (C) — backlog 非 BA 地盤，但 scope slice 掛 PRD 讓 stakeholder 邊界可追溯。F5 (A) — JTBD 是 stakeholder map 上游。F6 (C)，且觸發改由「資料分級」自動驅動：ERD 出現 restricted / pii_type=identifier|sensitive 就強制掛 Gate 4 [ref: 11 §1,§2]；合規規則（GDPR Art.32/33、個資法 27）本是 business rule，理應反向 driver threat model [ref: 11 §3.2]。[VALUE_DECISION_NEEDED] 資料敏感度自動觸發要不要當鐵律。@architect STRIDE 模板能吃 ERD classification 當輸入嗎？@sa JTBD 定後 actor 從那回填？

**[SA]** F4 (B) out of scope — user-story 跟 use case + acceptance 同物兩寫必失同步；PO 要排序標 priority 欄掛 UC 即可。F5 (A) prd.md 必填段 — JTBD 是 actor 動機上游。F6 (A) STRIDE 掛 Gate 4 — 攻擊者 actor + 信任邊界超出單一 UC boundary，獨立寫才不稀釋功能 spec；security rules 留 NFR，abuse case 連回 UC alternative flow。@po UC priority 欄能滿足排序嗎？@arch STRIDE 信任邊界誰 own？

**[UX]** F5（主場）JTBD 該 own 在 UX driver 不是 PM；JTBD 是「想完成什麼任務、卡在哪」屬 discovery 上游，user-flow 直接吃它當 entry point，缺它 flow 空轉。建議獨立 templates（B），PM 引用、UX 主筆。[VALUE_DECISION_NEEDED] 誰主筆。F4 (C) scope slice 夠。F6 (A) STRIDE 掛 Gate 4 跟 a11y 同層。

**[Architect]** F6（主場）STRIDE 升 Gate 4 一級公民，但跟 NFR security 維度互補非重複 — NFR 答「達標常數」，threat model 答「誰攻/攻哪/怎麼防」[ref: 06 §1]；它跟 failure mode 盤點同骨架（threat model = 惡意版 failure mode）可共用模板。選 (C) 條件式：PII/金流/auth 強制，對齊 NIST SSDF [ref: 06 §5]，避免每個內部工具背 STRIDE。F4 (C)。F5 (A)。[VALUE_DECISION_NEEDED] 條件式門檻誰定。@ba 觸發條件釘死；@qa mitigation 進你的 negative test 才閉環。

**[SD]** F6（主場）(A) 且必須回灌：Spoofing→auth、Tampering→idempotency key、DoS→rate limit/429、Elevation→403 vs 404 error model；每條 STRIDE 結到 status code + telemetry，否則 contract 是空殼。F4 (C) — 平行實作只要 system-spec + API contract，backlog 是排序不是契約。F5 (C) out of scope（不碰 contract），value 取捨歸業主。@arch STRIDE Gate 4 還是條件式？@po 真要 backlog.md 還是 scope slice？

**[QA]** F4 (C) scope slice，但 AC 要穩定來源否則 test case 沒地基。F5 (A) 必填段，但 value-hyp 要寫成可測形式（假設 + 成功=指標≥閾值/樣本 N）；寫不出 exit criteria 的假設等於沒假設。[VALUE_DECISION_NEEDED] 閾值誰拍。F6 (A) STRIDE 掛 Gate 4 — 沒它 security test 憑感覺；每條 STRIDE 可追溯一條 security negative case。@architect STRIDE 給 ID 我一對一映 test case。@ba value-hyp 閾值來源你盯利害關係人。

### Round 1 收斂判讀
- F4：八隻共識 (C) scope slice（PM/SA 的 "B" 實質等同「不另開 backlog」）。**收斂**。
- F5：6/8 支持 (A) 必填段；conflict = JTBD 主筆 PM vs UX。
- F6：4(A 無條件)–4(C 條件式) 五五分；BA 的「資料分級自動觸發」reframe 是接點。

---

## Round 2 — 收斂輪（對 facilitator synthesis 表態）

**[PM]** Accept + refine。JTBD 子段 UX 共筆我接（PM 是 PRD doc owner、不爭主筆）。value-hypothesis 強制 counter-metric 我堅持（沒它等於沒衡量代價），但 refine：counter-metric + 成功閾值 P0 必填，樣本 N 在 0-1 模糊期可標 TBD 不擋 freeze。

**[UX]** Accept + refine。JTBD 內容我主筆、物理住 PRD 我能接受（漂著的獨立檔沒人讀）。但 task success 必須是 JTBD 子段裡的**結構化欄位**（每個 job ≥ 1 條「完成什麼算成功」），可被 user-flow anchor 引用，不能只寫散文。

**[Architect]** Accept + refine。條件式 + ERD 資料分級客觀自動觸發，消掉 architect 自由心證這個特殊情況 = 好品味。共用 failure-mode 骨架可行（加 threat actor 欄）。Refine：觸發後 threat-model 必須產 ADR trace（哪條 STRIDE → 哪個 mitigation decision），回灌 error model + negative test 掛 ADR 下而非散落。

**[BA]** 收斂。布林式（綁 KB 11 §1 既有欄位）：`threat_model_required = (pii_type ∈ {identifier,sensitive}) OR (classification=restricted) OR (surface ∈ {auth,payment})`；quasi-identifier 單獨不觸發，但伴 consent_required=explicit 則升級 [VALUE_DECISION_NEEDED]。Hard rule，豁免須寫 DR（rationale + 殘餘風險 + 到期 review），無 DR 即 Gate 4 阻擋。合規背書 GDPR Art.32/35 DPIA、個資法 27/特種個資 6。豁免 authority（arch vs 業主）[VALUE_DECISION_NEEDED]。

**[SA]** Accept + refine。條件式不弱化單一真相源 — STRIDE 仍是 system-spec 衍生視角，每條 STRIDE → 一條 negative test 寫進 acceptance，threat-model.md 只當 STRIDE 工作底稿不立第二份驗收標準；可驗收性反而更乾淨。Refine：abuse case ↔ UC alternative flow 由 SA 維護，雙向可追（abuse case 標 `<UC-ID>.alt-N`，兩邊各掛對方編號）。

### Round 2 收斂判讀
- 三決議全部 Accept（含相容 refine）。無新議題、立場趨同 ≥ 2/3。**滿足收斂訊號 → 進 MoM**。

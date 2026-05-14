# AI 員工作業系統 — 白皮書 (拆檔版)

> 本目錄為 `whitepaper.md` v1.0 的主題拆檔版本，供內部團隊 reference 與個人寫作思路梳理使用。
>
> 對外發送 / 列印 / 完整閱讀請使用根目錄 `whitepaper.md`（4048 行單檔合併版）。

---

## 目錄總覽

### 主檔 (9 個)

| 檔案 | 主題定位 | 對應原章節 | 估計行數 |
| :--- | :--- | :--- | ---: |
| [00-executive-summary.md](./00-executive-summary.md) | 速讀 | §0 + §32.2/32.3 + 附錄 E | ~120 |
| [01-vision-positioning.md](./01-vision-positioning.md) | **願景** | §1, §2, §3, §22 | ~272 |
| [02-product-architecture.md](./02-product-architecture.md) | **產品** | §4~§10, §12, §13 | ~894 |
| [03-execution-onboarding.md](./03-execution-onboarding.md) | **規劃 + 執行** | §14, §16~§21 | ~847 |
| [04-strategy-business.md](./04-strategy-business.md) | **戰略** | §23~§25 | ~424 |
| [05-investor-thesis.md](./05-investor-thesis.md) | **投資 + 擴張** | §26~§30 | ~660 |
| [06-risk-boundaries.md](./06-risk-boundaries.md) | **風險** | §11, §15, §31 | ~147 |
| [99-conclusion.md](./99-conclusion.md) | 收束 | §32 完整版 | ~70 |

### 附錄 (10 個)

| 檔案 | 對應主檔 | 用途 |
| :--- | :--- | :--- |
| [A-glossary.md](./appendices/A-glossary.md) | 全部 | 名詞定義 |
| [B-decision-matrix.md](./appendices/B-decision-matrix.md) | 02 / 04 | Runtime / LLM / 自我學習決策矩陣 |
| [C-pre-launch-checklist.md](./appendices/C-pre-launch-checklist.md) | 03 / 06 | 上線前 5 大類檢核 |
| [D-reference-implementations.md](./appendices/D-reference-implementations.md) | 02 | 參考實作定位速查 |
| [E-three-mantras.md](./appendices/E-three-mantras.md) | 00 / 99 | 三句話口訣 |
| [F-onboarding-checklist.md](./appendices/F-onboarding-checklist.md) | 03 | 客戶 4 類資料盤點 |
| [G-containerization.md](./appendices/G-containerization.md) | 02 | 容器化部署策略 |
| [H-onboarding-wizard-ux.md](./appendices/H-onboarding-wizard-ux.md) | 03 | 導入精靈 7 步驟 UX |
| [I-7-day-package.md](./appendices/I-7-day-package.md) | 03 / 04 | AI 客服 7 日導入包 |
| [J-employee-resume-template.md](./appendices/J-employee-resume-template.md) | 03 | AI 員工履歷 YAML |

---

## 章節 → 檔案地圖（反查表）

| 原章節 | 所在檔案 |
| :--- | :--- |
| §0 執行摘要 | `00-executive-summary.md` |
| §1 問題陳述 | `01-vision-positioning.md` |
| §2 產品定位 | `01-vision-positioning.md` |
| §3 設計原則 | `01-vision-positioning.md` |
| §4 參考實作橫向評估 | `02-product-architecture.md` |
| §5 系統架構藍圖 | `02-product-architecture.md` |
| §6 核心領域模型 | `02-product-architecture.md` |
| §7 Bounded Context | `02-product-architecture.md` |
| §8 MCP 整合策略 | `02-product-architecture.md` |
| §9 SkillOps | `02-product-architecture.md` |
| §10 訓練室與生產環境分離 | `02-product-architecture.md` |
| §11 安全與合規 | `06-risk-boundaries.md` |
| §12 監控評估體系 (AgentOps) | `02-product-architecture.md` |
| §13 多模型策略與成本治理 | `02-product-architecture.md` |
| §14 MVP 路線圖 | `03-execution-onboarding.md` |
| §15 風險與緩解 | `06-risk-boundaries.md` |
| §16 組織與運營 | `03-execution-onboarding.md` |
| §17 導入服務五階段方法論 | `03-execution-onboarding.md` |
| §18 Onboarding Automation Layer | `03-execution-onboarding.md` |
| §19 三種企業導入模式 | `03-execution-onboarding.md` |
| §20 自動化成熟度模型 | `03-execution-onboarding.md` |
| §21 上線驗收門檻、員工配置與服務交付包 | `03-execution-onboarding.md` |
| §22 戰略定位與護城河論述 | `01-vision-positioning.md` |
| §23 自研 vs 外包決策矩陣 | `04-strategy-business.md` |
| §24 商業本質：訓練治理三轉換 | `04-strategy-business.md` |
| §25 商業模式與市場切入 | `04-strategy-business.md` |
| §26 投資人視角總判斷 | `05-investor-thesis.md` |
| §27 系統因果迴路與飛輪設計 | `05-investor-thesis.md` |
| §28 核心假設與驗證指標 | `05-investor-thesis.md` |
| §29 護城河三層分級與三個 Compiler | `05-investor-thesis.md` |
| §30 十年演化路線與 90 天行動 | `05-investor-thesis.md` |
| §31 不採納清單 (Non-goals) | `06-risk-boundaries.md` |
| §32 結論 | `99-conclusion.md` |

---

## 讀者路徑建議

依角色不同，建議閱讀順序：

### VC / 投資人 (90 分鐘)
```
00 速讀 → 01 願景 → 05 投資人視角 → 04 戰略商業 → 99 結論
```

### CTO / 架構師 (2 小時)
```
00 速讀 → 02 產品架構 → 06 風險邊界 → 03 執行（部分）
```

### 產品經理 / 服務交付經理 (1.5 小時)
```
00 速讀 → 01 願景 → 03 執行交付 → 附錄 F/H/I/J
```

### CEO / 創辦人 (3 小時)
```
全部閱讀，重點 01 → 04 → 05 → 03
```

### 安全 / 合規 / 法務 (1 小時)
```
00 速讀 → 06 風險邊界 → 02 §8 MCP / §11 (合規)
```

---

## Part 演進史

本白皮書為**漸進式**撰寫，記錄四輪補強過程供後續寫作思路參考：

| 時間 | 補強主軸 | 對應 Part | 觸發提問 |
| :--- | :--- | :--- | :--- |
| 2026-05-14 R1 | 產品 + 架構 + 服務交付 | Part I + Part II 雛形 | 「整理為企業白皮書」 |
| 2026-05-14 R2 | Onboarding Automation Layer | Part II 擴充 (§18) | 「夠不夠無腦？」 |
| 2026-05-14 R3 | 戰略 + 自研 vs 外包 + 商業模式 | Part III (§22~§25) | 「VC 視角、初期該握什麼」 |
| 2026-05-14 R4 | 投資人視角 + 十年護城河 | Part IV (§26~§30) | 「10 年護城河是否穩固」 |
| 2026-05-14 R5 | 拆檔重組 | 本目錄 | 「整份文件混在一起難閱讀」 |
| 2026-05-14 R6 | 紅杉/Boris 觀點對照 | §1.4 + §16.4 + §17/§18 釐清 + §22.7 + §29.10 | 「SaaS 護城河被 AI 摧毀」影片思考整理 |
| 2026-05-14 R7 | AI 藍領 Wedge + 大廠下沉防禦 | §22.8 + §28.9 (H5) + §29.11 (Layer 3a/b/c) + §30.1 路線收斂 | Google Cloud Next '26 衝擊 → 收斂到藍領 wedge |

**寫作觀察**：每輪補強都對應一個更深的決策層次（產品 → 服務 → 戰略 → 投資 → 結構）。如後續新增 Part V，建議放在 `docs/` 中以新主題檔承載，不再回灌單檔版。

---

## 雙版維護 SOP

### 兩個版本的職責

| 版本 | 路徑 | 用途 |
| :--- | :--- | :--- |
| 單檔合併版 | `../whitepaper.md` | 對外發送、列印、完整閱讀 |
| 主題拆檔版 | `docs/` | 內部 reference、寫作梳理、修改入口 |

### 修改規則

1. **新增 / 修改某章節時**：先動拆檔版（粒度小，容易對焦），再同步回單檔版
2. **新增整個 Part 時**：先在 `docs/` 新增主檔，再決定是否合併到單檔版
3. **單檔版作為發布快照**：對外發送前確認與拆檔版一致
4. **避免漂移**：每次修改後在本 README「Part 演進史」追加紀錄
5. **章節編號穩定**：`§X.Y` 引用文字保留原語意；不轉為 Markdown 相對連結，避免跨工具預覽不一致

---

## 跨檔引用慣例

各主檔內所有 `§X.Y` 形式引用**保持原樣**。讀者透過本 README 章節地圖反查所在檔案。

**為何不用相對連結**：
- GitHub / Notion / VSCode / Obsidian 對 Markdown anchor 的處理不一致
- 跨檔 anchor 維護成本高（章節編號變動時需全域更新）
- `§X.Y` 文字本身已具語意辨識度

每個主檔開頭設有「相關章節速查」標頭，列出本檔被外部引用 / 對外引用的高頻小節。

---

## 元資料

- **白皮書版本**：v1.0
- **拆檔版本**：v1.0
- **最後同步**：2026-05-14
- **原檔總行數**：4048
- **主檔總行數**：~3584（不含 README 與附錄）
- **附錄總行數**：~430

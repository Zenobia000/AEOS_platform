# Visual Prompts — AEOS 架構圖文字投影片

> 本目錄收納 AEOS 平台規劃所需的**架構圖文字描述 + GPT 生圖完整提示詞**。
> 用途：給 GPT-4o / DALL-E 3 / Midjourney 等 image generation tool 生成可用於投影片的架構圖。

## 目錄

| 檔案 | 圖類 | 對應白皮書章節 |
| :--- | :--- | :--- |
| [01-architecture-stack.md](./01-architecture-stack.md) | 系統架構堆疊圖 | §5 / §5.4 / §29.11 |
| [02-sa-process-flow.md](./02-sa-process-flow.md) | SA 流程架構圖 | §9 / §17 / §18 / §29.5~29.7 |

## 通用使用流程

1. 開啟對應檔案
2. 複製「GPT-4o Image Generation Prompt (English)」段落
3. 貼到 GPT-4o (image mode) / DALL-E 3 / Midjourney
4. 用「預期輸出檢核」清單驗證生成結果
5. 若不滿意，可改用「中文備援 Prompt」或調整色彩 / 排版指令

## 工具偏好

| 需求 | 推薦工具 |
| :--- | :--- |
| 投影片用、需精準對齊 | **GPT-4o image generation** (英文 prompt) |
| 高品質視覺、藝術感 | **Midjourney v6** + `--ar 16:9` |
| 純文字可編輯架構圖 | **draw.io / Excalidraw** + 元素清單作為 checklist |
| Markdown 文檔內嵌 | **Mermaid** (02 檔末尾附 mermaid 程式碼) |

## 後續可擴充

未來如需新增其他架構圖，請依下列模板格式建立 `NN-<topic>.md`：

```markdown
# Slide N — <圖標題>

> 用途：...
> 建議工具：...
> 對應白皮書章節：...

## 設計目標
## 視覺結構（含色彩語意、圖形語意）
## 元素清單（含階層）
## GPT-4o Image Generation Prompt (English)
## GPT-4o 中文備援 Prompt
## 各工具使用建議
## 預期輸出檢核
```

## 版本

- **建立日期**：2026-05-14
- **對應白皮書版本**：v1.2 (R5 + R6 + R7)

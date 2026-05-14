# Slide 1 — AEOS 系統架構堆疊圖 (System Architecture Stack)

> **用途**：給 GPT-4o / DALL-E 3 / Midjourney 等 image generation tool 生成架構圖
> **建議工具**：GPT-4o image generation (英文 prompt 準確度最高)
> **對應白皮書章節**：§5 系統架構藍圖、§5.4 三平面分離、§29.11 Layer 3 細分

---

## 設計目標

呈現 AEOS 在 AI 生態系中的**精準層級定位**：
- 主戰場：Layer 3b (垂直藍領治理) + Layer 3c (跨雲中立治理)
- 不進入區：Layer 3a (大廠主場)
- 依賴底層：Layer 1 (LLM) + Layer 2 (Agent Runtime)
- 客戶接觸：Layer 5 (Channel) + Layer 6 (Frontline Workplace)
- 三個橫切面：Control / Data / Governance Plane

---

## 視覺結構

```
方向：垂直堆疊 (Bottom → Top = Foundation → User)
邊界：左側 6 層水平 stack；右側 3 個 Cross-cutting Plane
比例：16:9
```

### 色彩語意

| 顏色 | 語意 | Hex |
| :--- | :--- | :--- |
| 灰色 | 不進入 (大廠主場) | #9CA3AF |
| 藍色 | AEOS 主場 | #3B82F6 |
| 綠色 | AEOS 第二戰場 | #10B981 |
| 橘色 | 客戶接觸層 | #F59E0B |
| 紫色 | 橫切治理面 | #8B5CF6 |
| 淺灰 | Foundation 基礎層 | #E5E7EB |

---

## 元素清單 (由下而上)

### Layer 1 — LLM Provider Layer (淺灰)

```
- OpenAI (GPT-4 / 4o / mini)
- Anthropic (Claude Opus / Sonnet / Haiku)
- Google (Gemini)
- Local Model (Ollama / vLLM / LM Studio)
```

### Layer 2 — Agent Runtime Layer (淺灰)

```
- Loops
- LangGraph
- CrewAI
- Open-source Agent frameworks
```

### Layer 3a — Generic AI Workforce Governance (灰，紅色斜紋標記「不進入」)

```
- Google Gemini Enterprise + Agent Studio
- Microsoft Copilot Studio
- Salesforce Agentforce
- AWS Q Business + Bedrock Agents
標籤："BIG TECH TERRITORY — AEOS does NOT enter"
```

### Layer 3b — Vertical Blue-collar Governance (藍色，加粗邊框)

```
- F&B Chain AI Worker
- Long-term Care AI Worker
- Retail / Warehouse AI Worker
- Construction / Manufacturing AI Worker
- Customer Service / Ticketing AI Worker
標籤："AEOS PRIMARY"
```

### Layer 3c — Cross-cloud Neutral Governance (綠色)

```
- Multi-cloud (Azure + AWS + GCP) tenant
- Multi-LLM routing
- Private deployment / Data sovereignty
- Regulated industries (Finance / Government / Healthcare)
標籤："AEOS SECONDARY"
```

### Layer 4 — AI Blue-collar Employee Runtime (藍灰)

```
- Frozen Runtime (No self-mutation)
- Approved Skills only
- Tool Gateway enforced
- Audit Log emitted
```

### Layer 5 — Channel Layer (Frontline-first) (橘色)

```
- LINE / WhatsApp Business
- Mobile App / Voice / IVR
- Web Chat Widget (secondary)
- Walkie-talkie / In-store kiosk
```

### Layer 6 — Customer Frontline Workplaces (橘色，頂層)

```
- Restaurant counter
- Retail store floor
- Warehouse / Logistics hub
- Hospital / Long-term care facility
- Construction site / Factory floor
```

### Cross-cutting Planes (右側垂直，跨越所有 6 層，紫色)

```
Plane 1 — Control Plane
  ├── Skill Registry
  ├── Tool Registry
  ├── Tenant Manager
  └── Admin Console

Plane 2 — Data Plane
  ├── Real-time conversation
  ├── Tool invocation
  ├── Knowledge retrieval
  └── Conversation logging

Plane 3 — Governance Plane
  ├── Policy Engine (RBAC / ABAC)
  ├── Audit Service
  ├── Evaluation Service (AgentOps)
  └── Training Room (Sandbox)
```

---

## GPT-4o Image Generation Prompt (English — 主要使用)

```
Create a professional enterprise architecture diagram titled
"AEOS — AI Employee Operating System — Architecture Stack".

Layout: Vertical layered stack on the left (6 horizontal layers, bottom to top),
with 3 vertical cross-cutting planes on the right.

Visual style: Clean, modern enterprise architecture diagram, similar to AWS /
Azure architecture references. White background, rounded rectangles,
1.5px borders, monospace labels, subtle drop shadows.

Color coding:
- Gray (#9CA3AF) = "NOT entering" zones
- Blue (#3B82F6) = "AEOS primary battleground"
- Green (#10B981) = "AEOS secondary battleground"
- Orange (#F59E0B) = "Customer touchpoint"
- Purple (#8B5CF6) = "Cross-cutting governance plane"
- Light gray (#E5E7EB) = "Foundation layers"

LEFT STACK (bottom to top, 6 horizontal layers, each spanning full width):

Layer 1 (light gray): "LLM Provider Layer" — OpenAI, Anthropic, Google, Local
Layer 2 (light gray): "Agent Runtime Layer" — Loops, LangGraph, CrewAI
Layer 3a (gray with red diagonal stripes): "Generic AI Workforce Governance"
  — Gemini Enterprise, Copilot Studio, Agentforce, Q Business
  — labeled "BIG TECH TERRITORY — AEOS does NOT enter"
Layer 3b (BLUE, prominent, with thicker border): "Vertical Blue-collar Governance"
  — F&B, Long-term Care, Retail, Construction, Customer Service
  — labeled "AEOS PRIMARY"
Layer 3c (GREEN): "Cross-cloud Neutral Governance"
  — Multi-cloud, Multi-LLM, Private deployment, Regulated industries
  — labeled "AEOS SECONDARY"
Layer 4 (blue-gray): "AI Blue-collar Employee Runtime"
  — Frozen Runtime, Approved Skills, Tool Gateway, Audit Log
Layer 5 (orange): "Channel Layer (Frontline-first)"
  — LINE, WhatsApp, Mobile App, Voice/IVR, Walkie-talkie
Layer 6 (orange, top): "Customer Frontline Workplaces"
  — Restaurant, Retail floor, Warehouse, Hospital, Construction site

RIGHT SIDE (3 vertical purple cross-cutting planes spanning all 6 layers):
- Plane 1: "Control Plane" — Skill Registry, Tool Registry, Tenant Manager, Admin Console
- Plane 2: "Data Plane" — Conversation, Tool invocation, Knowledge retrieval, Logging
- Plane 3: "Governance Plane" — Policy Engine, Audit, Evaluation, Training Room

Add a small legend at the bottom-right explaining the 5 color codes.
Add directional arrows: upward arrow on the left labeled "User-facing direction",
downward arrow labeled "Foundation dependency".

Title at top in bold sans-serif. All English labels. 16:9 aspect ratio.
```

---

## GPT-4o 中文備援 Prompt

```
建立一張專業企業架構圖，標題為「AEOS — AI 員工作業系統 — 系統架構堆疊」。

排版：左側為 6 層水平堆疊（由下而上），右側為 3 個垂直橫切面 (cross-cutting planes)。

視覺風格：簡潔現代的企業架構圖，類似 AWS / Azure 官方架構參考圖。
白底、圓角矩形、1.5px 邊框、等寬字體標籤、輕微陰影。

色彩語意：
- 灰色 = 不進入區（大廠主場）
- 藍色 = AEOS 主戰場
- 綠色 = AEOS 第二戰場
- 橘色 = 客戶接觸層
- 紫色 = 橫切治理面
- 淺灰 = 基礎層

[6 層由下至上]

Layer 1 (淺灰)：LLM Provider Layer — OpenAI, Anthropic, Google, Local
Layer 2 (淺灰)：Agent Runtime Layer — Loops, LangGraph, CrewAI
Layer 3a (灰色加紅色斜紋)：Generic AI Workforce Governance
  — Gemini Enterprise, Copilot Studio, Agentforce, Q Business
  — 標籤「BIG TECH TERRITORY — AEOS NOT entering」
Layer 3b (藍色，加粗邊框)：Vertical Blue-collar Governance
  — F&B, Long-term Care, Retail, Construction, Customer Service
  — 標籤「AEOS PRIMARY」
Layer 3c (綠色)：Cross-cloud Neutral Governance
  — Multi-cloud, Multi-LLM, Private deployment, Regulated industries
  — 標籤「AEOS SECONDARY」
Layer 4 (藍灰)：AI Blue-collar Employee Runtime
  — Frozen Runtime, Approved Skills, Tool Gateway, Audit Log
Layer 5 (橘色)：Channel Layer (Frontline-first)
  — LINE, WhatsApp, Mobile App, Voice/IVR, Walkie-talkie
Layer 6 (橘色，頂層)：Customer Frontline Workplaces
  — Restaurant, Retail floor, Warehouse, Hospital, Construction site

[右側 3 個垂直紫色橫切面，跨越全部 6 層]
- Plane 1 「Control Plane」— Skill Registry, Tool Registry, Tenant Manager, Admin Console
- Plane 2 「Data Plane」— Conversation, Tool invocation, Knowledge retrieval, Logging
- Plane 3 「Governance Plane」— Policy Engine, Audit, Evaluation, Training Room

底部右下放置色彩圖例。中央左側加垂直箭頭，向上標「User-facing 方向」，
向下標「Foundation 依賴」。
標題使用粗體無襯線字體。16:9 比例。
```

---

## 各工具使用建議

| 工具 | 建議用法 |
| :--- | :--- |
| **GPT-4o image generation** | 直接貼上述英文 prompt，輸出品質最高 |
| **DALL-E 3** | 英文 prompt + `--style enterprise architecture diagram` |
| **Midjourney v6** | 英文 prompt 末加 `--ar 16:9 --style enterprise diagram --v 6` |
| **Excalidraw / draw.io** | 用「元素清單」段落作為手繪 checklist |
| **PlantUML / Mermaid** | 可額外請求轉換為純文字程式碼版本 |

---

## 預期輸出檢核

生成圖片後檢核下列要點：

```
□ 6 層由下而上順序正確（LLM 在最底，Frontline 在最頂）
□ Layer 3a 有紅色斜紋與「NOT entering」標示
□ Layer 3b 為最顯眼的藍色 (AEOS 主場)
□ Layer 3c 為綠色 (第二戰場)
□ 右側 3 個 plane 跨越全部 6 層
□ 標題為「AEOS — Architecture Stack」
□ 16:9 比例
□ 所有元素文字清晰可讀
```

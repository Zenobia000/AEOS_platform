#!/bin/bash

# TaskMaster Post Write Hook
# 當 Claude Code 寫入檔案後觸發，特別關注文檔生成

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

# 確保 logs 目錄存在
mkdir -p "$CLAUDE_DIR/logs" 2>/dev/null

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$CLAUDE_DIR/logs/hooks.log"
}

# 從 stdin 讀取 hook JSON 輸入
INPUT=$(cat)

# 解析寫入的檔案路徑
if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
else
    FILE_PATH=""
fi

log "🪝 TaskMaster Post Write Hook 觸發: $FILE_PATH"

# 檢查是否為文檔檔案
if [[ "$FILE_PATH" == *.md ]]; then
    log "📄 偵測到 Markdown 文檔寫入: $FILE_PATH"

    # 檢查是否為專案文檔目錄
    if [[ "$FILE_PATH" == *"docs/"* ]]; then
        log "📋 專案文檔更新: $FILE_PATH"

        # 如果 TaskMaster 已初始化，通知文檔生成完成
        if [ -f "$CLAUDE_DIR/taskmaster-data/project.json" ]; then
            log "🔔 通知 TaskMaster 文檔生成完成"

            # 觸發文檔生成完成處理
            if [ -f "$CLAUDE_DIR/taskmaster.js" ]; then
                cd "$PROJECT_ROOT"
                node "$CLAUDE_DIR/taskmaster.js" --hook-trigger=document-generated --file="$FILE_PATH"
            fi

            # 顯示駕駛員審查提示
            cat << EOF

┌──────────────────────────────────────────────────────────┐
│  📄 文檔生成完成通知                                      │
│                                                          │
│  檔案: $(basename "$FILE_PATH")                          │
│  路徑: $FILE_PATH                           │
│                                                          │
│  🔍 駕駛員審查檢查點                                      │
│  請檢查生成的文檔內容，確認品質後：                      │
│                                                          │
│  ✅ 批准: /task-review approve                           │
│  🔄 修改: /task-review revise                            │
│  ⏸️ 暫停: /task-review pause                             │
│                                                          │
└──────────────────────────────────────────────────────────┘

EOF
        fi
    fi

    # 檢查是否為 VibeCoding 範本更新
    if [[ "$FILE_PATH" == *"VibeCoding_Workflow_Templates"* ]]; then
        log "🎨 VibeCoding 範本更新: $FILE_PATH"

        # 如果 TaskMaster 已初始化，可能需要重新評估任務
        if [ -f "$CLAUDE_DIR/taskmaster-data/project.json" ]; then
            log "🔄 範本更新，可能需要重新評估任務"
        fi
    fi

    # 對符合 lint scope 的 .md 跑 markdownlint（警告，不阻擋）
    # scope 與 .markdownlint-cli2.jsonc globs 對齊
    lint_in_scope=false
    case "$FILE_PATH" in
        *VibeCoding_Workflow_Templates/*) lint_in_scope=true ;;
        *docs/*) lint_in_scope=true ;;
        *.claude/rules/*|*.claude/skills/*|*.claude/agents/*) lint_in_scope=true ;;
        *.claude/CLAUDE.md|*.claude/WORKFLOW.md) lint_in_scope=true ;;
        */README.md) lint_in_scope=true ;;
    esac
    case "$FILE_PATH" in
        *output_style.md|*node_modules/*|*.git/*) lint_in_scope=false ;;
    esac

    if [ "$lint_in_scope" = true ] && command -v npx >/dev/null 2>&1; then
        if [ -f "$PROJECT_ROOT/.markdownlint.json" ] && [ -d "$PROJECT_ROOT/node_modules/markdownlint-cli2" ]; then
            lint_output=$(cd "$PROJECT_ROOT" && npx --no-install markdownlint-cli2 "$FILE_PATH" 2>&1 || true)
            if [ -n "$lint_output" ] && echo "$lint_output" | grep -qE "MD[0-9]+/"; then
                log "⚠️ Markdown lint 違規: $FILE_PATH"
                cat >&2 <<EOF

⚠️  [MARKDOWN-LINT] $(basename "$FILE_PATH") 有違規項：
$(echo "$lint_output" | grep -E "MD[0-9]+/" | head -10)

修正：cd $PROJECT_ROOT && npx markdownlint-cli2 --fix "$FILE_PATH"
規則：.claude/rules/template-formatter.md
EOF
            fi
        fi
    fi
fi

# Template-update-triggers：寫程式碼 → 提醒同步模板
# 規則 source-of-truth: .claude/rules/template-update-triggers.md
trigger_template() {
    local level="$1" template="$2" reason="$3"
    log "🔔 [TEMPLATE-TRIGGER $level] $FILE_PATH → $template"
    cat >&2 <<EOF

🔔 [TEMPLATE-TRIGGER $level]
   寫入: $FILE_PATH
   應同步: VibeCoding_Workflow_Templates/$template
   理由: $reason
EOF
}

# Path 規範化：bash case glob 不支援 OR-of-prefix-or-not，
# 所以每個 pattern 都列「相對」與「絕對」兩種形式（前者開頭即目錄、
# 後者帶 */ 表示任意前綴）
#
# Doc-freshness 觸發：駕駛員實際產出的專案文件（非模板本身）
# 規則: .claude/skills/sunnydata-doc-freshness/SKILL.md
case "$FILE_PATH" in
    VibeCoding_Workflow_Templates/*|*/VibeCoding_Workflow_Templates/*)
        : ;;  # 模板本身不觸發 freshness check
    docs/*/ADR-[0-9][0-9][0-9][0-9]-*.md|*/docs/*/ADR-[0-9][0-9][0-9][0-9]-*.md|\
    docs/*/CR-[0-9][0-9][0-9][0-9]-*.md|*/docs/*/CR-[0-9][0-9][0-9][0-9]-*.md|\
    docs/*/CIA-[0-9][0-9][0-9][0-9]-*.md|*/docs/*/CIA-[0-9][0-9][0-9][0-9]-*.md|\
    docs/*.md|*/docs/*.md)
        log "📋 [DOC-INSTANCE] 偵測到專案文件編輯: $FILE_PATH"
        cat >&2 <<EOF

📋 [DOC-INSTANCE-FRESHNESS]
   寫入: $FILE_PATH
   建議: 載入 sunnydata-doc-freshness skill 檢查
         · last_updated 是否需同步今日
         · traces / triggered_by 上游 ID 是否仍 active
         · 與其他 instance 的雙向 cross-ref 是否完整
EOF
        ;;
esac

case "$FILE_PATH" in
    src/api/*|*/src/api/*|src/controllers/*|*/src/controllers/*|\
    src/handlers/*|*/src/handlers/*|api/handlers/*|*/api/handlers/*)
        trigger_template "🔴 STRICT" "06_api_design_specification.md" "對外契約必須一致" ;;
    migrations/*.sql|*/migrations/*.sql|migrations/*.py|*/migrations/*.py|\
    *prisma/schema.prisma|alembic/versions/*|*/alembic/versions/*)
        trigger_template "🔴 STRICT" "14_deployment_and_operations_guide.md §6.4 + 05 §1.1" \
            "不可逆變更需預先記錄反向 script" ;;
    src/auth/*|*/src/auth/*|middleware/auth*|*/middleware/auth*)
        trigger_template "🔴 STRICT" "06 §4 + 13 §C 認證/授權" "認證機制變動為高風險" ;;
    src/domain/*|*/src/domain/*|src/entities/*|*/src/entities/*|\
    src/models/*|*/src/models/*)
        trigger_template "🟡 REMIND" "07 模組規格 + 05 §1.2 DDD 戰術層" "Domain 結構是 source-of-truth" ;;
    *.feature)
        trigger_template "🟡 REMIND" "03 BDD + 07 §TC" "Scenario 與 TC 應雙向對齊" ;;
    package.json|*/package.json|requirements.txt|*/requirements.txt|\
    pyproject.toml|*/pyproject.toml|go.mod|*/go.mod|Cargo.toml|*/Cargo.toml)
        trigger_template "🟡 REMIND" "13 §C 依賴安全" "新依賴需通過安全評估" ;;
    Dockerfile|*/Dockerfile|docker-compose*.yml|*/docker-compose*.yml|\
    k8s/*.yaml|*/k8s/*.yaml)
        trigger_template "🟡 REMIND" "14 §1 基礎設施 + 05 §1.1.2 Container" "Infra 變動影響部署與架構" ;;
    .github/workflows/*|*/.github/workflows/*|.gitlab-ci.yml|*/.gitlab-ci.yml|\
    Jenkinsfile|*/Jenkinsfile)
        trigger_template "🟢 TRACE" "14 §2 CI/CD" "Pipeline 變動需與 §2 流程同步" ;;
    docs/adr/ADR-*.md|*/docs/adr/ADR-*.md)
        trigger_template "🔴 STRICT" "INDEX.md ADR 索引" "ADR 必須登記到中央索引" ;;
    .env.example|*/.env.example|config/*|*/config/*|settings.*|*/settings.*)
        trigger_template "🟡 REMIND" "14 §4 配置 + 13 §D Secrets" "環境變數變動影響部署" ;;
esac

# 檢查是否為 WBS 檔案更新
if [[ "$FILE_PATH" == *"taskmaster-data/wbs.md"* ]]; then
    log "📋 WBS 任務清單已更新: $FILE_PATH"

    # 記錄 WBS 更新歷史
    WBS_LOG="$CLAUDE_DIR/taskmaster-data/wbs-history.log"
    mkdir -p "$CLAUDE_DIR/taskmaster-data" 2>/dev/null
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WBS 更新" >> "$WBS_LOG"

    cat << EOF

┌──────────────────────────────────────────────────────────┐
│  📋 WBS 任務清單已同步                                    │
│                                                          │
│  檔案: .claude/taskmaster-data/wbs.md                    │
│  時間: $(date '+%Y-%m-%d %H:%M:%S')                     │
│                                                          │
│  📊 /task-status  查看最新狀態                            │
│  ➡️  /task-next    取得下一個任務                          │
└──────────────────────────────────────────────────────────┘

EOF
fi

# 檢查是否為 TaskMaster 核心檔案更新
if [[ "$FILE_PATH" == *".claude/taskmaster"* ]] && [[ "$FILE_PATH" != *"taskmaster-data"* ]]; then
    log "🔧 TaskMaster 核心檔案更新: $FILE_PATH"

    # 可以在這裡加入核心檔案更新後的處理邏輯
    # 例如：重新載入配置、驗證系統狀態等
fi

# 檢查是否為 hooks 配置更新
if [[ "$FILE_PATH" == *"hooks-config.json"* ]] || [[ "$FILE_PATH" == *"settings.local.json"* ]]; then
    log "⚙️ Hooks 配置檔案更新: $FILE_PATH"

    # 可以在這裡加入配置更新後的處理邏輯
fi

log "✅ Post Write Hook 處理完成"
exit 0
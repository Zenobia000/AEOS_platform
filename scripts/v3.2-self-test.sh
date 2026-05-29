#!/usr/bin/env bash
#
# v3.2 Self-Test — 評估各階段觸發是否 work，無功能斷層
#
# Usage:  bash scripts/v3.2-self-test.sh
# Exit:   0 = all PASS, 1 = some FAIL
#
# 涵蓋 4 大層面：
#   A. 規範層 — 規則文件存在、lint 設定有效
#   B. 套用層 — 20 模板 lint 0 error
#   C. 觸發層 — post-write hook 對各 glob 正確觸發；skill 註冊；pre-commit 可執行
#   D. 治理層 — ID 體系、cross-ref、檔名規範
#
set +e  # 不要遇錯即停，要跑完所有測試

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Color codes
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
GRAY="\033[0;90m"
BOLD="\033[1m"
NC="\033[0m"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_TESTS=()

pass() { echo -e "  ${GREEN}✓ PASS${NC}  $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo -e "  ${RED}✗ FAIL${NC}  $1"; [ -n "$2" ] && echo -e "    ${GRAY}└─ $2${NC}"; FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_TESTS+=("$1"); }
skip() { echo -e "  ${YELLOW}- SKIP${NC}  $1"; [ -n "$2" ] && echo -e "    ${GRAY}└─ $2${NC}"; SKIP_COUNT=$((SKIP_COUNT + 1)); }
section() { echo; echo -e "${BOLD}$1${NC}"; }

# Simulate post-write.sh stdin call & capture stderr output
simulate_post_write() {
    local file_path="$1"
    echo "{\"tool_input\":{\"file_path\":\"$file_path\"}}" \
        | bash .claude/hooks/post-write.sh 2>&1
}

echo -e "${BOLD}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  v3.2 Self-Test — 觸發鏈與功能斷層檢查${NC}"
echo -e "${GRAY}  $(date '+%Y-%m-%d %H:%M:%S') · branch: $(git branch --show-current)${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════════${NC}"

# ────────────────────────────────────────────────────────────
section "A. 規範層 (Rules & Lint Config)"
# ────────────────────────────────────────────────────────────

[ -f .claude/rules/template-formatter.md ] \
    && pass "template-formatter.md 存在" \
    || fail "template-formatter.md 缺檔"

[ -f .claude/rules/template-update-triggers.md ] \
    && pass "template-update-triggers.md 存在" \
    || fail "template-update-triggers.md 缺檔"

[ -f .markdownlint.json ] && jq -e . .markdownlint.json >/dev/null 2>&1 \
    && pass ".markdownlint.json 為有效 JSON" \
    || fail ".markdownlint.json 無效或缺檔"

[ -f .markdownlint-cli2.jsonc ] \
    && pass ".markdownlint-cli2.jsonc 存在" \
    || fail ".markdownlint-cli2.jsonc 缺檔"

[ -f .editorconfig ] \
    && pass ".editorconfig 存在" \
    || fail ".editorconfig 缺檔"

[ -f .githooks/pre-commit ] && [ -x .githooks/pre-commit ] \
    && pass ".githooks/pre-commit 存在且可執行" \
    || fail ".githooks/pre-commit 缺檔或無 +x 權限"

# pre-commit syntax check
bash -n .githooks/pre-commit 2>/dev/null \
    && pass ".githooks/pre-commit shell 語法 OK" \
    || fail ".githooks/pre-commit shell 語法錯誤"

# core.hooksPath 是否啟用
hooks_path=$(git config --get core.hooksPath 2>/dev/null || echo "")
if [ "$hooks_path" = ".githooks" ]; then
    pass "core.hooksPath = .githooks（gate 已啟用）"
elif [ -z "$hooks_path" ]; then
    skip "core.hooksPath 未設定（gate 未啟用，需執行 git config core.hooksPath .githooks）"
else
    fail "core.hooksPath 設為 '$hooks_path'，預期 '.githooks'"
fi

# package.json devDependency 指向 markdownlint-cli2
if jq -e '.devDependencies."markdownlint-cli2"' package.json >/dev/null 2>&1; then
    pass "package.json 已 pin markdownlint-cli2"
else
    fail "package.json 缺 markdownlint-cli2 devDependency"
fi

[ -d node_modules/markdownlint-cli2 ] \
    && pass "node_modules/markdownlint-cli2 已安裝" \
    || skip "node_modules 未安裝（請執行 npm install）"

# ────────────────────────────────────────────────────────────
section "B. 套用層 (VibeCoding Templates 全部 lint clean)"
# ────────────────────────────────────────────────────────────

if [ -x node_modules/.bin/markdownlint-cli2 ]; then
    total_errs=0
    for f in VibeCoding_Workflow_Templates/*.md; do
        [[ "$f" == *output_style.md ]] && continue
        rm -rf /tmp/v32-lint && mkdir -p /tmp/v32-lint
        cp .markdownlint.json /tmp/v32-lint/
        cp "$f" /tmp/v32-lint/test.md
        cd /tmp/v32-lint
        errs=$(node_modules/.bin/markdownlint-cli2 test.md 2>&1 | grep -cE "^test\.md:" || true)
        cd "$ROOT"
        if [ "$errs" -ne 0 ]; then
            fail "$(basename "$f") 有 $errs 個 lint 違規"
            total_errs=$((total_errs + errs))
        fi
    done
    if [ "$total_errs" -eq 0 ]; then
        pass "20 個 VibeCoding 模板全 lint clean"
    fi
else
    skip "markdownlint-cli2 binary 不在 node_modules，跳過 lint 測試"
fi

# ────────────────────────────────────────────────────────────
section "C. 觸發層 (post-write.sh trigger 矩陣)"
# ────────────────────────────────────────────────────────────

if [ -x .claude/hooks/post-write.sh ] || [ -f .claude/hooks/post-write.sh ]; then
    pass "post-write.sh 存在"
else
    fail "post-write.sh 缺檔"
fi

# C.1 程式碼變更 → STRICT trigger 觸發
out=$(simulate_post_write "src/api/orders/controller.py")
if echo "$out" | grep -q "06_api_design_specification"; then
    pass "src/api/* 觸發 06 API 同步提醒 (STRICT)"
else
    fail "src/api/* 未觸發 06 提醒" "輸出: $(echo "$out" | tail -3 | tr '\n' '|')"
fi

out=$(simulate_post_write "db/migrations/0042_add_status.sql")
if echo "$out" | grep -q "14_deployment_and_operations_guide\|§6.4"; then
    pass "migrations/*.sql 觸發 14 §6.4 反向 migration 提醒 (STRICT)"
else
    fail "migrations/*.sql 未觸發 14 §6.4 提醒"
fi

out=$(simulate_post_write "src/auth/middleware.ts")
if echo "$out" | grep -q "06 §4\|13 §C"; then
    pass "src/auth/* 觸發 06 §4 + 13 §C 提醒 (STRICT)"
else
    fail "src/auth/* 未觸發認證提醒"
fi

out=$(simulate_post_write "features/checkout.feature")
if echo "$out" | grep -q "03 BDD"; then
    pass "*.feature 觸發 03 BDD 提醒 (REMIND)"
else
    fail "*.feature 未觸發 03 提醒"
fi

out=$(simulate_post_write "package.json")
if echo "$out" | grep -q "13 §C 依賴安全"; then
    pass "package.json 觸發 13 §C 依賴安全提醒 (REMIND)"
else
    fail "package.json 未觸發 13 §C 提醒"
fi

out=$(simulate_post_write ".github/workflows/ci.yml")
if echo "$out" | grep -q "14 §2 CI/CD"; then
    pass ".github/workflows/* 觸發 14 §2 CI/CD 提醒 (TRACE)"
else
    fail ".github/workflows/* 未觸發 14 §2 提醒"
fi

# C.2 Doc-instance 寫入 → freshness skill 提醒
out=$(simulate_post_write "docs/adr/ADR-0007-use-postgres-for-orders.md")
if echo "$out" | grep -q "DOC-INSTANCE-FRESHNESS\|sunnydata-doc-freshness"; then
    pass "docs/adr/ADR-*.md 觸發 doc-freshness skill 提醒"
else
    fail "docs/adr/ADR-*.md 未觸發 doc-freshness 提醒"
fi

out=$(simulate_post_write "docs/cr/CR-0023-deprecate-v1-api.md")
if echo "$out" | grep -q "DOC-INSTANCE-FRESHNESS\|sunnydata-doc-freshness"; then
    pass "docs/cr/CR-*.md 觸發 doc-freshness skill 提醒"
else
    fail "docs/cr/CR-*.md 未觸發 doc-freshness 提醒"
fi

out=$(simulate_post_write "docs/cia/CIA-0005-stripe-upgrade.md")
if echo "$out" | grep -q "DOC-INSTANCE-FRESHNESS\|sunnydata-doc-freshness"; then
    pass "docs/cia/CIA-*.md 觸發 doc-freshness skill 提醒"
else
    fail "docs/cia/CIA-*.md 未觸發 doc-freshness 提醒"
fi

# C.3 模板本身編輯 → 不應觸發 doc-instance check
out=$(simulate_post_write "VibeCoding_Workflow_Templates/04_architecture_decision_record_template.md")
if echo "$out" | grep -q "DOC-INSTANCE-FRESHNESS"; then
    fail "編輯模板誤觸發 doc-freshness（應只對 instance 觸發）"
else
    pass "編輯模板正確 SKIP doc-freshness 提醒"
fi

# C.4 無關路徑 → 不應觸發任何東西
out=$(simulate_post_write "README.md")
if echo "$out" | grep -qE "TEMPLATE-TRIGGER|DOC-INSTANCE-FRESHNESS"; then
    fail "編輯 README.md 誤觸發提醒（應只有 lint warning）"
else
    pass "編輯 README.md 不觸發無關提醒"
fi

# C.5 Skill 存在性與 description scope 正確
skill_file=".claude/skills/sunnydata-doc-freshness/SKILL.md"
if [ -f "$skill_file" ]; then
    pass "sunnydata-doc-freshness skill 存在"
    desc=$(grep "^description:" "$skill_file" | head -1)
    if echo "$desc" | grep -q "instantiated"; then
        pass "skill description 反映正確 scope (instantiated documents)"
    else
        fail "skill description 未提到 scope 是 instances"
    fi
    if echo "$desc" | grep -q "SKIPS edits to VibeCoding_Workflow_Templates"; then
        pass "skill description 明示 SKIP 模板本身"
    else
        fail "skill description 未明示跳過模板"
    fi
else
    fail "sunnydata-doc-freshness/SKILL.md 缺檔"
fi

# 舊名應已刪除
if [ -d .claude/skills/sunnydata-template-freshness ]; then
    fail "sunnydata-template-freshness 舊目錄仍存在（應已重命名）"
else
    pass "sunnydata-template-freshness 舊目錄已清除"
fi

# ────────────────────────────────────────────────────────────
section "D. 治理層 (ID 體系 / 檔名規範 / Cross-ref)"
# ────────────────────────────────────────────────────────────

# D.1 INDEX 包含 ID 命名規範段
if grep -q "## ID 命名規範" VibeCoding_Workflow_Templates/INDEX.md; then
    pass "INDEX.md §ID 命名規範 存在"
else
    fail "INDEX.md 缺 §ID 命名規範"
fi

# D.2 INDEX 包含檔名規範段
if grep -q "檔名規範" VibeCoding_Workflow_Templates/INDEX.md; then
    pass "INDEX.md §檔名規範 存在"
else
    fail "INDEX.md 缺 §檔名規範"
fi

# D.3 INDEX 區分 Inline vs File ID
if grep -qE "Inline ID|File ID" VibeCoding_Workflow_Templates/INDEX.md; then
    pass "INDEX.md 區分 Inline ID / File ID 兩類"
else
    fail "INDEX.md 未明示 Inline vs File ID 區分"
fi

# D.4 04/19/20 三個 File ID 模板含檔名範例
for f in 04_architecture_decision_record_template.md 19_change_request_template.md 20_change_impact_analysis.md; do
    if grep -q "檔名:" "VibeCoding_Workflow_Templates/$f"; then
        pass "$(echo $f | cut -d_ -f1) 模板含檔名範例 hint"
    else
        fail "$(echo $f | cut -d_ -f1) 模板缺檔名範例 hint"
    fi
done

# D.5 Quality Gates QG-G0~G4 五個都在 01 §6
qg_count=$(grep -cE "QG-G[0-4]:" VibeCoding_Workflow_Templates/01_workflow_manual.md)
if [ "$qg_count" -eq 5 ]; then
    pass "01 §6 含 QG-G0~G4 五個量化關卡"
else
    fail "01 §6 QG 數量 = $qg_count，預期 5"
fi

# D.6 19 CR 與 20 CIA 模板存在
[ -f VibeCoding_Workflow_Templates/19_change_request_template.md ] \
    && pass "19 CR 模板存在" || fail "19 CR 模板缺檔"
[ -f VibeCoding_Workflow_Templates/20_change_impact_analysis.md ] \
    && pass "20 CIA 模板存在" || fail "20 CIA 模板缺檔"

# D.7 14 §6 Rollback Plan 含 8 子段
sub_count=$(grep -cE "^### 6\.[1-8]" VibeCoding_Workflow_Templates/14_deployment_and_operations_guide.md)
if [ "$sub_count" -ge 8 ]; then
    pass "14 §6 Rollback Plan 含 ≥ 8 子段（實際 $sub_count）"
else
    fail "14 §6 子段數量 = $sub_count，預期 ≥ 8"
fi

# D.8 雙向 cross-ref 抽樣檢查（06 ↔ 13）
if grep -q "與 13 §C-API 的邊界" VibeCoding_Workflow_Templates/06_api_design_specification.md \
    && grep -q "與 06 §4 的邊界" VibeCoding_Workflow_Templates/13_security_and_readiness_checklists.md; then
    pass "06 ↔ 13 雙向 cross-ref 完整"
else
    fail "06 ↔ 13 雙向 cross-ref 不完整"
fi

# D.9 11 ↔ 14 PR vs CI/CD 邊界
if grep -q "與 14 §2 CI/CD 的邊界" VibeCoding_Workflow_Templates/11_code_review_and_refactoring_guide.md; then
    pass "11 → 14 §2 cross-ref 存在"
else
    fail "11 → 14 §2 cross-ref 缺失"
fi

# D.10 觸發規則表中所有引用的 VibeCoding 檔案實際存在
referenced_files=$(grep -oE "VibeCoding_Workflow_Templates/[0-9_a-z]+\.md" .claude/rules/template-update-triggers.md 2>/dev/null | sort -u)
broken=0
for ref in $referenced_files; do
    [ -f "$ref" ] || { fail "trigger 規則引用了不存在的 $ref"; broken=$((broken + 1)); }
done
if [ "$broken" -eq 0 ]; then
    pass "template-update-triggers.md 引用的所有檔案實際存在"
fi

# ────────────────────────────────────────────────────────────
# Summary
# ────────────────────────────────────────────────────────────
echo
echo -e "${BOLD}════════════════════════════════════════════════════════════════════${NC}"
TOTAL=$((PASS_COUNT + FAIL_COUNT + SKIP_COUNT))
echo -e "${BOLD}  Summary: ${GREEN}${PASS_COUNT} PASS${NC} · ${RED}${FAIL_COUNT} FAIL${NC} · ${YELLOW}${SKIP_COUNT} SKIP${NC} · ${TOTAL} total${BOLD}${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════════${NC}"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo
    echo -e "${RED}${BOLD}失敗項目：${NC}"
    for t in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}✗${NC} $t"
    done
    exit 1
fi

exit 0

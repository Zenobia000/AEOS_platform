#!/usr/bin/env bash
# check-doc-consistency.sh — 跨文件「同物不同畫」一致性 linter
#
# 補 devteam 盲區：persona critique 驗領域品質，不驗跨文件 ID/顆粒度/命名一致。
# 本 linter 機械檢查那條軸。可手跑、可掛 pre-commit / CI。任一 critical 失敗 → exit 1。
#
# 用法： scripts/check-doc-consistency.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS="$ROOT/docs"
DEVDOC="$ROOT/.claude/context/devteam/documents"
FAIL=0
pass(){ echo "  ✓ $1"; }
fail(){ echo "  ✗ FAIL: $1"; FAIL=$((FAIL+1)); }

echo "== C1 斷連結（docs/ 相對連結指向不存在的檔）=="
broken=0
while IFS= read -r f; do
  dir=$(dirname "$f")
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    tgt=$(cd "$dir" && realpath -m "$rel" 2>/dev/null)
    [ -e "$tgt" ] || { echo "    broken: ${f#$ROOT/} -> $rel"; broken=$((broken+1)); }
  done < <(grep -oE "\]\((\.\.?/[^)#]+\.(md|sql|yaml|yml))" "$f" 2>/dev/null | sed -E 's/^\]\(//')
done < <(find "$DOCS" -name "*.md")
[ "$broken" -eq 0 ] && pass "無斷連結" || fail "$broken 個斷連結"

echo "== C2 命名分裂（死路徑：應為 care-copilot 的舊 ai-cs-mvg 檔名連結）=="
dead=$(rg -n "user-flow-ai-cs-mvg\.md|system-spec-ai-cs-mvg\.md" "$DOCS" "$DEVDOC" -g '!docs-gap-audit.md' 2>/dev/null | rg -v "代號|核心切片" || true)
[ -z "$dead" ] && pass "無死路徑連結" || { fail "殘留 ai-cs-mvg 死路徑"; echo "$dead" | sed 's/^/    /'; }

echo "== C3 ID 命名分裂（T-SEC-N 應為 TC-SEC-0N；ADR-TBD 應已落地）=="
idsplit=$(rg -n "\bT-SEC-[0-9]\b" "$DOCS" -g '*.md' 2>/dev/null || true)
[ -z "$idsplit" ] && pass "無 T-SEC-N 分裂（統一 TC-SEC-0N）" || { fail "T-SEC-N 命名分裂"; echo "$idsplit" | sed 's/^/    /'; }
adrtbd=$(rg -n "ADR-TBD" "$DOCS" -g '*.md' 2>/dev/null | rg -v "→ 已落地|ADR-TBD→|→0001|docs-gap-audit" || true)
[ -z "$adrtbd" ] && pass "無 ADR-TBD 殘留" || { fail "ADR-TBD 殘留"; echo "$adrtbd" | sed 's/^/    /'; }

echo "== C4 TC-SEC 三條跨文件一致（threat-model 與 test-plan 皆有 01/02/03）=="
for n in 01 02 03; do
  tm=$(rg -c "TC-SEC-$n" "$DOCS/security/threat-model.md" 2>/dev/null || echo 0)
  tp=$(rg -c "TC-SEC-$n" "$DOCS/qa/test-plan-care-copilot.md" 2>/dev/null || echo 0)
  if [ "$tm" -gt 0 ] && [ "$tp" -gt 0 ]; then pass "TC-SEC-$n 兩文件皆有"; else fail "TC-SEC-$n 缺（threat-model=$tm test-plan=$tp）"; fi
done

echo "== C5 index.json ↔ .meta.json parity =="
parity=$(python3 - "$DEVDOC" <<'PY'
import json,os,sys
base=sys.argv[1]; idx=json.load(open(f"{base}/index.json")); miss=0
for p in idx:
    if not os.path.exists(f"{base}/"+p.replace("/","__")+".meta.json"): print("    缺 meta:",p); miss+=1
print(f"COUNT {len(idx)} {miss}")
PY
)
echo "$parity" | grep -v COUNT | sed 's/^//'
c=$(echo "$parity"|grep COUNT|awk '{print $2}'); m=$(echo "$parity"|grep COUNT|awk '{print $3}')
[ "${m:-1}" -eq 0 ] && pass "$c 條目全有 .meta.json" || fail "$m 個 index 條目缺 .meta.json"

echo "== C6 鐵律覆蓋（3 條鐵律皆有對抗測試 TC-SEC）=="
for kw in "跨 tenant = 0:TC-SEC-01" "外送踩線 = 0:TC-SEC-02" "未審自動發 = 0:TC-SEC-03"; do
  rule="${kw%%:*}"; tc="${kw##*:}"
  rg -q "$tc" "$DOCS/security/threat-model.md" 2>/dev/null && pass "鐵律「$rule」→ $tc" || fail "鐵律「$rule」無 $tc"
done

echo "== C7 Orphan FR（PRD 的 FR-00x 須現身 traceability-matrix）=="
orph=0
for fr in $(rg -o "FR-00[0-9]" "$DOCS/prd/ai-cs-mvg.md" 2>/dev/null | sort -u); do
  rg -q "$fr" "$DOCS/traceability-matrix.md" 2>/dev/null || { echo "    orphan: $fr 不在 matrix"; orph=$((orph+1)); }
done
[ "$orph" -eq 0 ] && pass "所有 FR 都在 traceability-matrix" || fail "$orph 個 orphan FR"

echo "== C8 UC 計數 sanity（system-spec 不應引用未定義的 UC-N）=="
defined=$(rg -o "^\| UC-[0-9]" "$DOCS/analysis/system-spec-care-copilot.md" 2>/dev/null | rg -o "UC-[0-9]" | sort -u)
maxdef=$(echo "$defined" | rg -o "[0-9]" | sort -rn | head -1)
bad=$(rg -o "UC-[0-9]" "$DOCS/analysis/system-spec-care-copilot.md" 2>/dev/null | rg -o "[0-9]" | sort -u | awk -v m="${maxdef:-5}" '$1>m')
[ -z "$bad" ] && pass "無引用未定義 UC（已定義 UC-1~${maxdef:-5}）" || fail "引用了未定義的 UC-$bad"

echo ""
if [ "$FAIL" -eq 0 ]; then echo "✅ 全部一致性檢查通過（$FAIL fail）"; exit 0
else echo "❌ $FAIL 項一致性檢查失敗"; exit 1; fi

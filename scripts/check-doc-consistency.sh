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

echo "== C9 gate ↔ doc Status 同步（frozen gate ⟹ doc Status∈{frozen,reviewed}；blocked 不誤殺）=="
c9=$(python3 - "$ROOT" <<'PY'
import json,re,sys,os
root=sys.argv[1]
state=json.load(open(f"{root}/.claude/context/devteam/state.json"))
gates=state.get("freeze_gates",{})
idx=json.load(open(f"{root}/.claude/context/devteam/documents/index.json"))
# gate→owner doc 讀 registry feature_bindings（不再硬編，消滅 linter↔KB 漂移點）
reg=json.load(open(f"{root}/devteam_knowledge_base/_registry.json"))
feat=(state.get("active_features") or ["care-copilot"])[0]
owner=reg.get("feature_bindings",{}).get(feat,{})
def doc_status(p):
    if p.endswith(".yaml"): return idx.get(p,{}).get("status","")   # openapi 無 Status pill → 用 index
    fp=f"{root}/{p}"
    if not os.path.exists(fp): return None
    head="\n".join(open(fp,encoding="utf-8").read().splitlines()[:12])
    m=re.search(r"Status\*?\*?:\s*([A-Za-z]+)",head)
    return m.group(1) if m else ""
fails=0
for g,st in gates.items():
    doc=owner.get(g)
    if not doc: continue
    ds=doc_status(doc)
    if st=="frozen":
        if ds not in ("frozen","reviewed"):
            print(f"    gate {g}=frozen 但 {doc} Status={ds!r}（須 frozen/reviewed）"); fails+=1
    elif ds=="frozen":
        print(f"    {doc} Status=frozen 但 gate {g}={st}（gate 未 frozen）"); fails+=1
print(f"RESULT {fails}")
PY
)
echo "$c9" | grep -v "^RESULT" | sed 's/^//'
n9=$(echo "$c9"|grep "^RESULT"|awk '{print $2}')
[ "${n9:-1}" -eq 0 ] && pass "frozen gate 與 doc Status 一致" || fail "$n9 個 gate↔Status 不一致"

echo "== C10 KB-12 Universal Header（spec 文件 5 pill；豁免 foundation/README）=="
c10=$(python3 - "$ROOT" <<'PY'
import os,sys,glob,re
root=sys.argv[1]
exempt_dirs=("docs/foundation/",); exempt=("docs/README.md",)
pills=["📋","🗓","🔖","👤"]
ok={"draft","reviewed","frozen","superseded","Proposed","Accepted","generated"}
fails=0
for fp in sorted(glob.glob(f"{root}/docs/**/*.md",recursive=True)):
    rel=os.path.relpath(fp,root)
    if rel.startswith(exempt_dirs) or rel in exempt: continue
    head="\n".join(open(fp,encoding="utf-8").read().splitlines()[:14])
    miss=[p for p in pills if p not in head]
    if "🔗" not in head and "🎯" not in head: miss.append("🔗/🎯")
    if miss: print(f"    {rel} 缺 pill: {' '.join(miss)}"); fails+=1; continue
    m=re.search(r"Status\*?\*?:\s*([A-Za-z]+)",head)
    if m and m.group(1) not in ok: print(f"    {rel} Status 值非法: {m.group(1)}"); fails+=1
print(f"RESULT {fails}")
PY
)
echo "$c10" | grep -v "^RESULT" | sed 's/^//'
n10=$(echo "$c10"|grep "^RESULT"|awk '{print $2}')
[ "${n10:-1}" -eq 0 ] && pass "spec 文件 header 皆合 KB-12" || fail "$n10 份 header 不合格"

echo "== C11 ASCII 框圖殘留（phase 文件應全 mermaid；豁免 foundation/README）=="
ascii=$(rg -n "[┌┐└┘▼▲◀▶◄►]" "$DOCS" -g '*.md' -g '!**/foundation/**' -g '!**/README.md' 2>/dev/null || true)
[ -z "$ascii" ] && pass "phase 文件無 ASCII 框圖" || { fail "ASCII 框圖殘留（應轉 mermaid）"; echo "$ascii" | sed 's/^/    /'; }

echo "== C12 index ↔ docs 雙向 parity =="
c12=$(python3 - "$ROOT" <<'PY'
import json,os,sys,glob
root=sys.argv[1]
idx=json.load(open(f"{root}/.claude/context/devteam/documents/index.json"))
exempt_dirs=("docs/foundation/",); exempt=("docs/README.md",)
fails=0
for p in idx:
    if not os.path.exists(f"{root}/{p}"): print(f"    index 登記但檔不存在: {p}"); fails+=1
for fp in sorted(glob.glob(f"{root}/docs/**/*.md",recursive=True)):
    rel=os.path.relpath(fp,root)
    if rel.startswith(exempt_dirs) or rel in exempt: continue
    if rel not in idx: print(f"    docs 有檔但未登記 index: {rel}"); fails+=1
print(f"RESULT {fails}")
PY
)
echo "$c12" | grep -v "^RESULT" | sed 's/^//'
n12=$(echo "$c12"|grep "^RESULT"|awk '{print $2}')
[ "${n12:-1}" -eq 0 ] && pass "index ↔ docs 雙向 parity 一致" || fail "$n12 個 parity 缺口"

echo "== C13 _registry.json ↔ KB/state/agents 一致（防 KB-to-KB 漂移 HB-1）=="
c13=$(python3 - "$ROOT" <<'PY'
import json,re,sys,os
root=sys.argv[1]
reg=json.load(open(f"{root}/devteam_knowledge_base/_registry.json"))
state=json.load(open(f"{root}/.claude/context/devteam/state.json"))
fails=0
# C13a: registry gate IDs == state.json freeze_gates keys
rg_gates=set(reg["gates"]); st_gates=set(state.get("freeze_gates",{}))
if rg_gates!=st_gates:
    print(f"    registry gates {sorted(rg_gates)} ≠ state freeze_gates {sorted(st_gates)}"); fails+=1
# C13b: 每 gate 的 required_diagrams 須現身 KB-04 對應 gate 段
kb04=open(f"{root}/devteam_knowledge_base/04_freeze_gates.md",encoding="utf-8").read()
# 切 KB-04 為各 gate 段：## Gate <label>: ...
secs={}
parts=re.split(r"\n## Gate (\S+?):",kb04)
# parts[0]=前言; 之後成對 (label, body)
labelmap={"1":"Gate1_PRD","2":"Gate2_UXFlow","3":"Gate3_SystemSpec","4":"Gate4_NFR_ADR",
          "5a":"Gate5a_API","5b":"Gate5b_DBSchema","6":"Gate6_TestReady","7":"Gate7_Release"}
for i in range(1,len(parts),2):
    lab=parts[i].strip(); body=parts[i+1] if i+1<len(parts) else ""
    gid=labelmap.get(lab)
    if gid: secs[gid]=body
for gid,gd in reg["gates"].items():
    body=secs.get(gid,"")
    for dia in gd.get("required_diagrams",[]):
        kw=reg["diagrams"].get(dia,{}).get("kb04_keyword",dia)
        if not re.search(kw,body):
            print(f"    {gid} 須畫 {dia} 但 KB-04 evidence 無對應關鍵字 /{kw}/"); fails+=1
# C13c: feature_bindings owner_doc 檔須存在
for feat,gmap in reg.get("feature_bindings",{}).items():
    for gid,doc in gmap.items():
        if not os.path.exists(f"{root}/{doc}"):
            print(f"    feature_bindings[{feat}][{gid}] 指向不存在的檔: {doc}"); fails+=1
# C13d: registry roles 每 persona 須有 agent 檔
for p in reg["roles"]:
    if not os.path.exists(f"{root}/.claude/agents/devteam-{p}-persona.md"):
        print(f"    role {p} 無對應 agent: .claude/agents/devteam-{p}-persona.md"); fails+=1
print(f"RESULT {fails}")
PY
)
echo "$c13" | grep -v "^RESULT" | sed 's/^//'
n13=$(echo "$c13"|grep "^RESULT"|awk '{print $2}')
[ "${n13:-1}" -eq 0 ] && pass "registry ↔ KB-04 / state / agents 一致" || fail "$n13 個 registry 漂移"

echo ""
if [ "$FAIL" -eq 0 ]; then echo "✅ 全部一致性檢查通過（$FAIL fail）"; exit 0
else echo "❌ $FAIL 項一致性檢查失敗"; exit 1; fi

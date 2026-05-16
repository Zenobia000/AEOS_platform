---
name: sunnydata-doc-freshness
description: Detect stale documentation in docs/2-contracts/ by comparing each file's last-synced-with frontmatter against the latest commit on its source-paths. Triggers on 'check doc freshness', 'find stale docs', '檢查文件鮮度', 'doc drift audit', 'are docs in sync with code'.
stability-tier: tooling
---

# Doc Freshness Audit

## What this skill does

Walks `docs/2-contracts/**/*.md` and `docs/2-contracts/**/*.yaml`, parses each file's frontmatter, and reports which contract docs have fallen behind the code they describe.

## Required frontmatter shape

This skill assumes each contract doc carries:

```yaml
---
id: BF-NNNN | UF-NNNN | API-NNNN | ...   # Flow ID (see 0-principles/PRIN-0001-flow-id-conventions.md)
status: draft | active | deprecated | superseded | archived
owner: <team>
last_reviewed: <YYYY-MM-DD>
supersedes: <id-or-null>
superseded_by: <id-or-null>

# Sync metadata (omit for cross-cutting docs like traceability-matrix where sync-source=doc)
last-synced-with: <git-commit-sha>
sync-source: code | doc
source-paths:
  - src/api/users.py
  - src/models/user.py
synced-at: 2026-05-10
---
```

Files without this frontmatter are reported as `UNMANAGED` so the user can decide whether they belong in tier 2 at all.

## Procedure

1. **Verify location**: confirm `docs/2-contracts/` exists. If not, exit with note that the project hasn't adopted the v4 layered docs structure (point to `VibeCoding_Workflow_Templates/HOW-TO-INSTANTIATE.md`).

2. **Enumerate candidates**:
   ```bash
   find docs/2-contracts -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" \)
   ```

3. **Per file, parse frontmatter**:
   - Extract `last-synced-with`, `source-paths` (list).
   - If frontmatter missing or fields absent → mark UNMANAGED.

4. **Per source-path, get latest commit**:
   ```bash
   git log -1 --format=%H -- <source-path>
   ```

5. **Inspect lifecycle (`status`)**:
   - `status: superseded` → mark `SUPERSEDED`; verify `superseded_by` points to an existing file
   - `status: deprecated` → mark `DEPRECATED`; flag for migration
   - `status: archived` → mark `ARCHIVED`; should not live in `docs/2-contracts/` (recommend move)
   - `status: draft` → mark `DRAFT`; warn if older than N days (default 30)
   - missing `status` field → mark `UNMANAGED` (treat same as missing whole frontmatter for severity)

6. **Compare sync** (only if `status` is `active` or `draft`):
   - If `last-synced-with` == latest source commit → FRESH
   - **+1 self-commit tolerance** (`sync-source: doc` only): if the *only* commit between `last-synced-with` and the file's latest commit is the file's own most recent self-bump, treat as **FRESH (self-bump)**. Rationale: the post-write hook stamps `last-synced-with` at write time using current `HEAD`, but the file's own commit lands one step later — so a "+1 self-commit" lag is the steady-state of an in-sync doc, not real drift. Detect by: `git rev-list <lsw>..<latest> -- <file>` returns exactly the file's latest commit and that commit's diff for the file is limited to the lsw line itself (or the file's first commit).
   - If `last-synced-with` is an ancestor of latest source commit (more than the self-bump tolerated above) → STALE; count commits between
   - If `last-synced-with` is unknown to git → BROKEN (probably squashed)
   - If source path doesn't exist → ORPHAN
   - **Forward-declared source-paths** (`sync-source: doc` + non-existent `source-paths`): when the contract is intentionally pre-implementation (code not yet written), do not mark ORPHAN. Report as `PRE-IMPL` instead with a note that the source path is a forward declaration. To distinguish from a true ORPHAN: a `PRE-IMPL` file has `sync-source: doc` (doc drives code); a true ORPHAN has `sync-source: code` (code drove doc, but code was deleted).

7. **Output a single table** sorted by severity (BROKEN > SUPERSEDED > ORPHAN > DEPRECATED > STALE > DRAFT(>N days) > UNMANAGED > PRE-IMPL > FRESH(self-bump) > FRESH):

| Status | Doc | Source | Commits behind | Suggested action |
|---|---|---|---|---|
| BROKEN | docs/2-contracts/api/v1.md | src/api/v1.py | n/a | Re-baseline frontmatter |
| SUPERSEDED | docs/2-contracts/payment-v1.md | — | n/a | superseded_by → payment-v2.md; can be archived |
| ORPHAN | docs/2-contracts/legacy.md | src/legacy/ | n/a | Move to archive or delete |
| DEPRECATED | docs/2-contracts/old-auth.md | src/auth/ | n/a | Migrate to new-auth.md |
| STALE | docs/2-contracts/payment.md | src/payment/ | 12 | Regenerate via vibecoding-write-api-contract |
| DRAFT(stale) | docs/2-contracts/draft-feature.md | — | n/a | Promote to active or archive (45 days old) |
| UNMANAGED | docs/2-contracts/notes.md | — | — | Add frontmatter (id, status) or move out of 2-contracts |
| PRE-IMPL | docs/2-contracts/MC-008-knowledge-rag.md | src/knowledge/ (not yet) | n/a | Forward declaration — implementation pending |
| FRESH(self-bump) | docs/2-contracts/BF-001-customer-onboarding.md | self | 1 (self) | None — tolerated steady state |
| FRESH | docs/2-contracts/auth.md | src/auth/ | 0 | None |

7. **Recommend remediation per row** — point to the relevant `vibecoding-*` skill for regeneration, or to the auto-frontmatter post-write hook for re-baselining.

## Why the "+1 self-commit" tolerance exists

The `post-write.sh` hook auto-stamps `last-synced-with` to `git rev-parse HEAD` at write time. At that moment, `HEAD` is the *parent* of the commit that will eventually contain the new file content — because the commit hasn't been made yet, and Claude tooling does not amend commits by default. The result: every freshly written tier-2 doc lands with `last-synced-with` pointing to its parent commit, exactly +1 commit behind its own latest commit. This is the **expected steady state**, not drift.

The skill therefore treats "+1 commit behind, where that single commit is the file's own self-bump" as **FRESH (self-bump)**. Anything more than 1 commit behind (or where the intervening commit touched other files materially) is still STALE.

Alternative fixes considered and rejected:
- Make the hook `git commit --amend` after stamping → violates "never amend by default"
- Use a sentinel like `last-synced-with: <PENDING>` resolved by a post-commit git hook → requires a `.git/hooks/post-commit` install step that we can't ship via the repo
- Make `vibecoding-write-*` skills compute the next commit SHA → impossible without committing first

## What this skill does NOT do

- It does **not** auto-update frontmatter — that's the post-write hook's job.
- It does **not** regenerate stale docs — that's the relevant `vibecoding-write-*` skill's job.
- It does **not** scan tier 0/1/3/4/5 docs — those tiers have different staleness semantics; tier 2 is the only one with a hard sync contract.

## Output style

Single markdown table, severity-sorted, no preamble. If everything is FRESH, say so in one line.

## When to invoke

- Weekly maintenance pass
- Before any release / deployment
- After a large refactor
- When the user asks "is X doc still accurate?"
- When `vibecoding-write-api-contract` or `vibecoding-write-db-schema` is about to write — to warn if the existing version is stale and needs ack first

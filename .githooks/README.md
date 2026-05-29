# Git Hooks (version-controlled)

This directory holds hooks that run locally on `git commit` / `git push`. They are committed to the repo so every clone gets the same gates.

## One-time activation (per clone)

```bash
git config core.hooksPath .githooks
```

Without this command, git uses `.git/hooks/` (the default, not version-controlled) and these hooks do nothing.

To verify:

```bash
git config --get core.hooksPath
# expected output: .githooks
```

## Hooks

### `pre-commit`

- Lints staged `.md` files against `.markdownlint.json`
- Auto-installs `markdownlint-cli2` on first run (via `npm install`)
- Blocks the commit if lint fails; suggests `--fix` invocation
- Scope: `VibeCoding_Workflow_Templates/`, `docs/`, `README.md`, `.claude/{rules,skills,agents}/`, `.claude/CLAUDE.md`, `.claude/WORKFLOW.md`
- Skips: `output_style.md`, `node_modules/`, `.git/`

To bypass once (RARE — e.g. emergency hotfix):

```bash
git commit --no-verify
```

## Rule source-of-truth

- Formatter style: `.claude/rules/template-formatter.md`
- Lint config: `.markdownlint.json` + `.markdownlint-cli2.jsonc`
- Tooling pin: `package.json` (`markdownlint-cli2` devDependency)

## Adding a new hook

1. Create `.githooks/<hook-name>` and `chmod +x`
2. Use `#!/usr/bin/env bash` + `set -euo pipefail`
3. Keep it fast (< 5s for the common path) — slow hooks get bypassed
4. Document here under "Hooks"

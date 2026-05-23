# Skills Monorepo

依 ADR-0003 + MC-005：Skill 的 source of truth 是 git monorepo + YAML manifest；
DB 表 `skill` / `skill_version` 只是查詢鏡像。

## 目錄結構

```
skills/
└── <vertical>/
    └── <skill-slug>/
        └── <semver>/
            ├── manifest.yaml      ← skill_version 主檔（含 status、tool_bindings、policy_refs 等）
            ├── system.md          ← system prompt 模板（對應 skill_version.prompt_template_ref）
            ├── tools.yaml         ← 該版本可呼叫的工具 schemas
            └── test_set.yaml      ← 驗收題庫（對應 skill_version.test_set_ref；S3 加上）
```

範例（Phase 1 唯一 skill）：

```
skills/customer-service/faq-respond/v1.0.0/
```

## Skill 上線流程

依 MC-005 5 態 lifecycle（draft → testing → approved → production → deprecated）：

1. 在新版本目錄建 `manifest.yaml` + `system.md` + `tools.yaml`
2. `git commit` — `skill_version.git_commit_sha` 將指向此 commit
3. AEOS Skill Loader 讀檔 → upsert `skill_version` row（status='draft'）
4. 跑 test set → 更新 `test_pass_rate`、`quality_gate_scores`
5. pass_rate ≥ 0.80 + expert approved → `status='production'`（DB CHECK 守門）
6. Atomic symlink swap (`skills/customer-service/faq-respond/current → v1.0.0/`)
7. Worker 重啟讀新版本（依 engineering-charter Frozen Runtime 原則）

## 對齊規格

- `docs/1-decisions/ADR-0003-skill-registry.md` — git monorepo 是 source of truth
- `docs/2-contracts/MC-005-skill-registry.md` — 5 態 lifecycle + Quality Gate
- `docs/2-contracts/db-schema.md` §3.1~§3.3 — DB schema 鏡像

## 限制（Phase 1）

- 無 hot-reload — 新版本上線需重啟 Worker（保 Frozen Runtime）
- 無自動 promotion — 必須 expert 手動 approved → production
- pass_rate < 0.80 不可進 production（DB `production_quality_gate` CHECK 強制）

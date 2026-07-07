# ARTIFACT_GOVERNANCE_2026-07-07

## Rules

- Runtime/test residue must not be committed: SQLite WAL/SHM, Playwright `test-results/`, `.turbo/cache/`, temporary screenshots unless explicitly listed as evidence.
- Historical screenshots under `reports/t5_02_screenshots/` are retained as historical evidence and must not be reused as fresh acceptance evidence.
- `.worktrees/` is local execution residue and must stay outside review truth.

## Pre-commit check

Run:

```bash
python scripts/check_repo_artifacts.py
```

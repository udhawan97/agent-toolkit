---
name: folioorb-financial-integrity
description: Apply FolioOrb-specific financial-data, portfolio-metric, database, updater, installed-app, and release safeguards whenever implementing, reviewing, testing, cleaning, or shipping FolioOrb.
license: MIT
---

# FolioOrb Financial Integrity

## Data rules

- Treat holdings, trades, realized gain, cost basis, DCA calculations, classifications, and performance metrics as financial data requiring traceable inputs and deterministic calculations.
- Never hide missing history behind a confident metric. Label partial periods, stale imports, and unsupported broker fields honestly.
- Preserve the user's SQLite database and Application Support state during installs, upgrades, cleanup, and tests. Use isolated test databases for automation.
- Keep API keys and secrets out of logs, screenshots, fixtures, commits, and release artifacts.

## Verification

Start with git state. For Python changes, mirror CI with an isolated database:

```zsh
python -m compileall -q app run.py tests
DATABASE_URL=sqlite:///./database/test-portfolio.db ANTHROPIC_API_KEY= python -m pytest -q
git diff --check
```

Add focused tests for calculation and import/export changes. Verify CSV import/export, classifications, dashboard totals, realized/unrealized values, and updater behavior in the running application when user-facing behavior changes.

For releases, verify CI/security gates, macOS and Windows artifacts, `SHA256SUMS.txt` and optional Minisign signature, stable versus `latest-main` semantics, installer/updater paths, live docs, and final commit/tag alignment.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

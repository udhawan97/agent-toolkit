---
name: golavo-product-trust
description: Apply Golavo-specific architecture, evidence, local-model, packaged-app, and release rules whenever work targets Golavo forecasts, AI analysis, UI, data packs, desktop packaging, or releases.
license: MIT
---

# Golavo Product Trust

## Authority boundary

- Deterministic and statistical models own every forecast number and verdict.
- AI may explain an evidence bundle; it must not act as a second forecast engine, invent numbers, or override the sealed forecast.
- Keep citations, allowed-number checks, provenance, hashes, freshness, license isolation, and fail-closed behavior intact.
- Preserve `data/artifacts/`, bundled packs, local model state, and user-owned worktrees unless cleanup is explicitly requested.
- If the user says not to download a model, stop all pull/install activity and verify partial artifacts are gone.

## Verification

Start with git state and run focused checks first. The broad local gates are:

```zsh
make test
make validate
make lint
cd ui && npm test && npm run build && npm run test:e2e
cargo check --manifest-path desktop/src-tauri/Cargo.toml --locked
git diff --check
```

Adapt to the touched surface, but do not omit provenance or artifact validation when data/model behavior changes.

For packaged-app work, verify sidecar startup, first-launch behavior, local-model readiness and cancellation, Fast/Deep analysis on a real fixture, explicit deterministic verdict wording, and visible error states in the installed app.

For releases, verify GitHub Actions, every platform installer, signatures where configured, `latest.json`, `SHA256SUMS.txt`, the live documentation site, and exact `HEAD`/`origin/main`/tag alignment.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

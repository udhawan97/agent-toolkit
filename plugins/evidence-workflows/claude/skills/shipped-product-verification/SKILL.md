---
name: shipped-product-verification
description: Verify the real shipped surface of Orifold, Golavo, Voyalier, or FolioOrb when the user asks to test the latest app, validate a release candidate, inspect a live site, clean old app copies, or prove a release is actually usable.
license: MIT
---

# Shipped Product Verification

Treat source correctness as necessary but insufficient. Prove the user-visible artifact that was built, installed, downloaded, or deployed.

## Workflow

1. Establish repo, branch, commit, dirty-tree state, and the intended artifact. Preserve user-owned changes, saved data, model files, and active worktrees.
2. Run the repository's documented build and test gate. Do not invent a generic command when a canonical script exists.
3. Build or download the exact artifact under test. Record its version, commit/tag relationship, size, and checksum when available.
4. Inspect bundle/package structure, metadata, signatures, updater configuration, required resources, and sidecars.
5. Launch the installed app and exercise the requested real workflow with representative fixtures. Source tests do not substitute for this step.
6. For releases, inspect hosted CI, release metadata, every expected platform asset, checksums or updater manifests, and the live docs/download page.
7. For cleanup, inventory first. Keep the accepted installed app and useful Application Support data; remove only confirmed duplicates or stale generated copies.
8. Recheck git state and report what was automated, what was manually observed, and what remains unverified.

## Product emphasis

- Orifold: open/import, editing fidelity, save/export/reopen, PDF engines, one installed copy, bundle id `com.ud.Orifold`.
- Golavo: packaged Tauri app, sidecar startup, deterministic forecast authority, evidence-bound AI narration, updater `latest.json`, checksums, and live docs.
- Voyalier: local-first trip flows, versioned contracts, privacy/redaction, city packs, updater assets, and release approval gates.
- FolioOrb: portfolio data integrity, updater/install behavior, database preservation, honest metrics, release assets, and live docs.

Use `PASS`, `PASS WITH FOLLOW-UPS`, `HOLD`, or `BLOCKED`; explain the evidence behind the verdict.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

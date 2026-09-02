---
name: orifold-workflow
description: Apply Orifold-specific product, implementation, testing, packaging, cleanup, and release rules whenever work targets the Orifold repository or installed Orifold macOS app.
license: MIT
---

# Orifold Workflow

Work from the active Orifold repository checkout. Resolve it from the user's explicit path or the current Git root; never assume a home-directory layout. Use current Orifold terminology; pdFold/PDFold names are historical unless migration evidence is explicitly in scope.

## Guardrails

- Preserve unrelated dirty files and worktrees. Never reset user work to make a build convenient.
- Keep PDF operations local-first. Cloud or BYOK AI must be explicit, user-initiated, and clear about what text leaves the Mac.
- Treat document fidelity, data safety, and crash-free open/import/save/export/reopen as higher priority than polish.
- Verify user-visible changes in the running app with real PDF fixtures, not only Swift tests.

## Gates

Start with `git status --short --branch`. Use focused tests while iterating, then run:

```zsh
swift build
swift test
git diff --check
```

For a clean local acceptance build, use:

```zsh
scripts/install-mac.sh --clean --verbose
```

Verify `~/Applications/Orifold.app`, `com.ud.Orifold`, bundle resources and PDFium framework, code signature, running process, requested user flows, and final git state. An ad-hoc build may fail Gatekeeper assessment while still passing code-sign verification and launching.

For release work, verify hosted CI, `Orifold.dmg`, `Orifold.zip`, checksum, `manifest.json`, installer behavior, live docs, and tag/main alignment before declaring success.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

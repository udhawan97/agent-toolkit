---
name: voyalier-product-contract
description: Apply Voyalier's frozen product contract, architecture, privacy, accessibility, pack, desktop, and release gates whenever implementing, reviewing, or shipping Voyalier.
license: MIT
---

# Voyalier Product Contract

Read `AGENTS.md` first and treat it as authoritative.

- Keep Voyalier a local-first, evidence-backed trip workspace, not an autonomous booking or authority system.
- Preserve versioned contracts. Breaking contract changes require an ADR and coordinated consumers.
- Keep domain and deterministic rules in Rust core; keep Tauri and Axum boundaries thin; keep the web UI behind the shared gateway/contracts.
- Treat documents, pages, provider output, and model output as untrusted. Preserve provenance, timestamps, hashes, license, confidence, and redaction.
- Remote AI requires explicit consent and a preview of content leaving the device.
- Preserve keyboard, screen-reader, contrast, reduced-motion, and 200% zoom behavior.

Run focused checks while iterating, then the repository gate:

```zsh
./scripts/check.sh
git diff --check
```

For release work, verify the protected release environment, signed updater configuration, DMG/EXE/MSI artifacts, `.sig` files, `latest.json`, per-platform checksums, city-pack compatibility, live docs, and tag/main alignment. Do not publish a draft as stable until approval and artifact checks are complete.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

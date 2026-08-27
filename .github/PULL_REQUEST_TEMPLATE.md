## What changed

Describe the user workflow this improves and the smallest package or public-surface change that delivers it.

## Cross-client contract

- [ ] Codex and Claude Code use the same canonical skill or workflow payload.
- [ ] Client-specific behavior is isolated to thin manifests or adapters.
- [ ] Plugin versions and both marketplace catalogs remain synchronized.

## Trust boundary

- [ ] No credentials, private evidence, personal paths, or account identifiers entered the diff.
- [ ] Authentication, network calls, writes, and external side effects are documented.
- [ ] Third-party content has confirmed provenance and redistribution rights.

## Verification

- [ ] `python bin/agent-kit validate --native`
- [ ] `sh -n bin/setup`
- [ ] Isolated lifecycle from `docs/TESTING.md`
- [ ] Changed README assets were rendered and visually inspected
- [ ] `CHANGELOG.md` and `COMPATIBILITY.md` are current

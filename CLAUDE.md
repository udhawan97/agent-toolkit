# Agent Toolkit repository guidance

Read `docs/MAINTAINING.md` before changing manifests, profiles, bootstrap behavior, or bundled skills.

- Keep each plugin self-contained; installed plugins must not depend on files outside their plugin directory.
- Keep shared skill bodies provider-neutral and put client-specific declarations in thin manifests or adapters.
- Never commit credentials, personal paths, installation receipts, or private audit evidence.
- Run `./bin/agent-kit validate --native` before proposing a release.
- Update `CHANGELOG.md` and `COMPATIBILITY.md` when behavior or supported clients change.

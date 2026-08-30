# Changelog

## 0.3.0 - Unreleased

- Added the explicit-only `dev-review` workflow: one senior owner coordinates exactly three specialist developers across code, architecture, real user journeys, design craft, correctness, security, reliability, accessibility, performance, and delivery; produces a scored offline report with separate coverage confidence; and implements only run-bound findings selected by the user.
- Added an owner-only, resumable review ledger with stable run-bound finding IDs, schema validation, atomic writes, writer locking, compare-and-swap updates, evidence/report digests, and research handoff state.
- Kept audit, implementation, merge, push, release, deployment, live egress, and production mutations as separate authority boundaries.

## 0.2.0 - Unreleased

- Reduced the fast path to one repeatable command: first run installs, later healthy runs refresh, and supported OS package managers can supply missing Git/Python prerequisites.
- Removed Node.js/`npx`, `uv`, and `pipx` as user prerequisites by copying validated Matt Pocock skill trees directly and managing Graphify in a toolkit-owned Python environment.
- Changed Matt Pocock's bundle to fetch every current upstream skill on each install/update, record the exact resolved commit, inventory, and targets, checkpoint ownership for interruption recovery, refresh every receipted client target, archive receipt-owned skills removed upstream, refuse unmanaged conflicts by default, and preserve changed adopted copies before replacement.
- Added equivalent ownership and symlink preflights for Graphify discovery, plus safe absolute-root validation for client configuration overrides.
- Changed toolkit-owned workflow refreshes to reinstall the receipted plugin from the current marketplace source in both clients, retaining Claude plugin data, so same-version source updates cannot leave personal skills stale.
- Pinned Graphify's toolkit-managed executable into each generated client skill and made `doctor` verify the real invocation instructions.
- Added automatic second-client reconciliation, Python `venv` prerequisite checks, a final one-line health check, and a validated public-personal skill manifest.
- Added an allowlisted upstream catalog for Graphify, Matt Pocock's skills, Diagram Design, Ponytail, Understand Anything, official OpenAI packages, Anthropic-authored essentials, attributed partner packages, and Obscura.
- Added one-step upstream install, update, and doctor orchestration without vendoring third-party or provider payloads.
- Added traversal-safe Obscura installation with archive, executable, and worker checksums plus exact local stdio MCP registration checks.
- Expanded the default profile into a complete public-safe dual-agent setup; added `skills-only`, `--core-only`, and `--no-guidance` paths.
- Replaced the minimal guidance block with sanitized Claude and Codex working agreements covering communication, authority, browser routing, process precedence, and Graphify.
- Removed real-name metadata and personal branding from public package manifests and marketplace presentation.
- Redesigned the README around one-command setup, a visual stack map, simple profile choices, explicit privacy boundaries, and a readable upstream source ledger.
- Preserved upstream packages during uninstall so shared provider-managed state is not removed accidentally.

## 0.1.0 - Preview baseline

- Added dual Codex and Claude marketplace catalogs.
- Added the `evidence-workflows` pilot plugin with three portable skills.
- Added an idempotent standard-library bootstrap with install, update, doctor, validate, and uninstall commands.
- Added optional managed global-guidance merging with backups.
- Added receipt-controlled maintenance, pending-install recovery, retry-safe per-client uninstall, strict marketplace source/ref verification, explicit pre-existing plugin adoption, disposable Codex update preflights, and Claude data-preserving uninstall behavior.
- Hardened local receipt and guidance backups with symlink refusal and owner-only POSIX permissions.
- Added one-command POSIX and PowerShell launchers for install, update, doctor, and uninstall.
- Hardened launcher updates against disconnected shallow history and clean local commits that do not exactly match the fetched channel.
- Redesigned the public README with a repo-owned visual identity, architecture and lifecycle diagrams, fast paths, compatibility guidance, and troubleshooting documentation.
- Extended repository validation and CI to cover public documentation links, accessible SVGs, launcher presence, shallow-update regressions, and symlinked receipt parents.
- Added release, compatibility, contribution, and security documentation.

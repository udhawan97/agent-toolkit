# Changelog

## 0.2.0 - Unreleased

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

# Upstream source ledger

Agent Toolkit keeps outside code outside this repository. The default profile fetches each bundle from the source below using the provider's native marketplace, package manager, or signed-release surface.

The machine-readable allowlist is [`catalog/upstreams.json`](../catalog/upstreams.json). A change to a repository, package name, archive, checksum, marketplace name, or plugin list is a reviewed installer change.

## Sources

| Bundle | Original source | Distribution | License signal | Clients |
| --- | --- | --- | --- | --- |
| Graphify | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | PyPI package `graphifyy`, installed in an isolated `uv` or `pipx` tool environment | Apache-2.0 | Codex + Claude |
| Matt Pocock's Skills | [mattpocock/skills](https://github.com/mattpocock/skills) | Pinned source commit; `skills` CLI 1.5.23; 37 copied skills | MIT | Codex + Claude |
| Diagram Design | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | Native plugin marketplace | MIT | Codex + Claude |
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Native plugin marketplace | MIT | Codex + Claude |
| Understand Anything | [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) | Native plugin marketplace | MIT | Codex + Claude |
| OpenAI Essentials | [openai/plugins](https://github.com/openai/plugins) | Codex's runtime marketplace, or a generated local adapter over a verified official checkout when the reserved runtime catalog is unavailable | Per package; the repository has no single top-level license | Codex |
| Anthropic Essentials | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | Claude `claude-plugins-official` marketplace; includes attributed partner packages below | Apache-2.0 for the marketplace repository; individual plugins may add terms | Claude |
| Obscura | [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura) | Pinned GitHub release archive plus executable and worker SHA-256 allowlists | Apache-2.0 | Codex + Claude MCP |

No table entry grants extra rights. The upstream repository and the individual package remain authoritative for licensing, privacy, service terms, and support.

## Provider essentials

### OpenAI for Codex

The allowlist installs:

- `build-macos-apps` on macOS
- `build-web-apps`
- `build-web-data-visualization`
- `codex-security`
- `openai-developers`

These packages come from OpenAI's marketplace repository. Agent Toolkit does not copy their payloads. Codex-managed installations use the reserved official marketplace directly. A standalone Codex CLI may not expose that runtime-owned catalog; in that case setup clones the same official repository into private toolkit state and generates a small local marketplace adapter that points only at the allowlisted plugin directories. Some capabilities may ask for an API key or provider login when first used; setup never supplies one.

### Anthropic for Claude Code

The allowlist installs:

- `claude-code-setup`
- `claude-md-management`
- `code-review`
- `code-simplifier`
- `feature-dev`
- `frontend-design`
- `playwright`
- `security-guidance`
- `skill-creator`
- `superpowers`

These packages come from the Anthropic-managed official marketplace. Language-server plugins and account-connected apps are intentionally not installed by default because their usefulness depends on a repository or user account.

The list mixes first-party and curated partner work; marketplace placement is not an authorship claim:

| Package | Authorship/source relationship |
| --- | --- |
| `playwright` | Microsoft Playwright MCP, curated through Anthropic's marketplace. |
| `superpowers` | Jesse Vincent / `obra/superpowers`, pinned by Anthropic's marketplace at the commit recorded in `catalog/upstreams.json`. |
| Other entries above | Shipped from Anthropic-controlled plugin directories in the managed marketplace. |

## Update behavior

`agent-kit update` performs the following:

1. Refreshes Agent Toolkit's own `stable` source and native marketplace.
2. Upgrades Graphify through its isolated Python tool manager.
3. Reinstalls Matt Pocock's 37 allowlisted skills from the catalog-pinned commit with the catalog-pinned `skills` CLI.
4. Refreshes each registered native plugin marketplace and fast-forwards the verified OpenAI fallback checkout when that adapter is in use.
5. Runs Claude's native plugin updater where available; Codex uses its refreshed marketplace-backed installation.
6. Rechecks the pinned Obscura archive and repairs toolkit-managed MCP registrations when its catalog version changes.

The allowlist points at named upstream branches for marketplace packages so updates can follow provider releases. That is convenient but means an update is also a trust decision. Review the upstream diff or use `--core-only` when you need a frozen, repository-only setup.

## Removal behavior

`agent-kit uninstall` removes the toolkit-owned `evidence-workflows` plugin and its marketplace. It can also remove the marked shared-guidance block.

Upstream packages are intentionally preserved. Their original package managers may be shared with other projects or installers, so mass-removing them would be unsafe. Use each provider's native uninstall command when you deliberately want to remove an upstream package.

## Why account-connected plugins are excluded

The public allowlist focuses on local developer workflows. It does not auto-install Dropbox, Figma, Notion, Airtable, finance, messaging, CRM, calendar, or other account-connected plugins. Those require a user-specific need, permission review, and authentication decision.

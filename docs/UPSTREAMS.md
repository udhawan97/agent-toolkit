# Upstream source ledger

Agent Toolkit keeps outside code outside this repository. The default profile fetches each bundle from the source below using the provider's native marketplace, package manager, or signed-release surface.

The machine-readable allowlist is [`catalog/upstreams.json`](../catalog/upstreams.json). A change to a repository, package name, archive, checksum, marketplace name, or plugin list is a reviewed installer change.

## Sources

| Bundle | Original source | Distribution | License signal | Clients |
| --- | --- | --- | --- | --- |
| Graphify | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Version-pinned PyPI package `graphifyy`, installed in a toolkit-managed Python environment | Apache-2.0 | Codex + Claude |
| Matt Pocock's Skills | [mattpocock/skills](https://github.com/mattpocock/skills) | Current upstream `main`; every discovered skill is validated and copied; exact commit, inventory, and targets are receipted | MIT | Codex + Claude |
| Hallmark | [nutlope/hallmark](https://github.com/nutlope/hallmark) | Current upstream `main`; only `skills/hallmark` is validated and installed; exact commit and targets are receipted | MIT | Codex + Claude |
| Vercel Frontend Skills | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | Current upstream `main`; only composition patterns, React best practices, and web-design guidelines are validated and installed; exact commit and targets are receipted | Per selected skill; MIT signals | Codex + Claude |
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

## Frontend set

- `hallmark` supplies opinionated anti-template building, audit, redesign, and study workflows. It remains Nutlope/Together AI's third-party work; Agent Toolkit does not list it as a personal skill.
- `composition-patterns` supplies scalable React component APIs.
- `react-best-practices` supplies React and Next.js performance guidance.
- `web-design-guidelines` supplies accessibility and interface-quality review guidance.
- Anthropic's `frontend-design` remains in the Claude provider bundle for broader visual direction.

The default does not connect Figma. Its skills and app require account-specific access and permission review, so users add that integration separately when they actually need it.

## Update behavior

`agent-kit update` performs the following:

1. Refreshes Agent Toolkit's own `stable` source and native marketplace.
2. Upgrades Graphify inside the toolkit-managed isolated Python environment, pins that exact executable in each generated client skill, and verifies the command can be discovered from those instructions.
3. Fetches Matt Pocock's current upstream `main`, checks out the exact fetched commit, validates every complete skill tree, installs every discovered skill for the selected clients, archives receipt-owned skills removed upstream, and records the resolved commit, inventory, and targets in `~/.agent-toolkit/upstreams.json`.
4. Fetches Hallmark and Vercel's frontend source from their allowlisted upstream branches, validates only the named skill trees, and records each exact commit, inventory, and managed target.
5. Refreshes each registered native plugin marketplace and fast-forwards the verified OpenAI fallback checkout when that adapter is in use.
6. Reinstalls the toolkit-owned, receipted personal workflow plugin from the refreshed marketplace source in both clients. Claude keeps plugin data during replacement.
7. Rechecks the pinned Obscura archive and repairs toolkit-managed MCP registrations when its catalog version changes.

The allowlist points at named upstream branches for marketplace packages and tracked skill sources so updates can follow provider releases. That is convenient but means an update is also a trust decision. `doctor` proves installed skill trees still match the exact commit recorded at install/update time, not that an upstream branch has remained unchanged. Review the upstream diff or use `--core-only` when you need a repository-only setup.

If a destination skill already exists without a toolkit ownership receipt, setup refuses to touch it. Use `--adopt-existing` only when you intend to replace it. If its contents differ, the existing tree is preserved under the source-specific folder in `~/.agent-toolkit/backups/` before replacement. Receipt-owned skills removed from an allowlist or tracked source are archived instead of being left agent-visible. Symlinked or otherwise unsafe skill trees are always refused.

## Removal behavior

`agent-kit uninstall` removes the toolkit-owned `evidence-workflows` plugin and its marketplace. It can also remove the marked shared-guidance block.

Upstream packages are intentionally preserved. Their original package managers may be shared with other projects or installers, so mass-removing them would be unsafe. Use each provider's native uninstall command when you deliberately want to remove an upstream package.

## Why account-connected plugins are excluded

The public allowlist focuses on local developer workflows. It does not auto-install Dropbox, Figma, Notion, Airtable, finance, messaging, CRM, calendar, or other account-connected plugins. Those require a user-specific need, permission review, and authentication decision.

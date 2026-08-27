# Security policy

Agent plugins can instruct models to use tools and may bundle executable helpers. Treat installation as a code-review decision.

The sanitized public root and its reachable history do not accept secrets, credentials, private memories, production data, personal paths, real-name metadata, or unredacted audit evidence. The Python bootstrap uses argument-vector subprocess calls rather than a shell. Setup writes a dedicated managed source checkout, local `~/.agent-toolkit` receipts and backups, native plugin configuration, and marked guidance blocks unless `--no-guidance` is supplied. It does not copy client credentials, authentication state, or personal memories.

When a standalone Codex CLI does not expose the runtime-owned `openai-curated` marketplace, setup clones `openai/plugins` over HTTPS into private toolkit state, verifies the Git origin, and generates a local adapter containing only allowlisted paths. It never registers another source under Codex's reserved official marketplace name.

Receipt and backup files are created with owner-only modes and symlink-safe paths on POSIX systems. On Windows they inherit the current user profile’s access controls; an equivalent owner-only ACL guarantee has not yet been verified.

Marketplace identity is checked against its exact local path or canonical GitHub repository. Codex's source-less reserved runtime catalog is accepted only when the complete allowlisted OpenAI selector set is available. Pre-existing marketplaces are never removed unless the receipt created them, and pre-existing plugins are never managed unless the user supplies `--adopt-existing`.

Third-party and provider code is not vendored. `catalog/upstreams.json` is the reviewed allowlist for repository names, package names, plugin selectors, and release artifacts. Marketplace updates follow named upstream branches, so running `update` is also a decision to trust new code from those listed providers. Use `--core-only` when that is not acceptable.

Obscura is downloaded only from its GitHub release URL. Setup selects an allowlisted platform archive, verifies the archive plus executable and worker SHA-256 values, rejects archive traversal and link entries, and only then copies the payload into toolkit state. Existing cached payloads and MCP registrations are rechecked exactly before use. The MCP server uses local stdio; setup does not expose its unauthenticated HTTP transport.

Upstream packages are deliberately preserved during Agent Toolkit uninstall because another project or installer may share them. Remove those packages through their original package managers only after reviewing ownership.

Report a suspected vulnerability through a [private GitHub security advisory](https://github.com/udhawan97/agent-toolkit/security/advisories/new). Do not open a public issue containing exploit details, credentials, or private data.

Supported security fixes target the latest published `stable` preview. Earlier versions may be fixed when a safe backport is practical.

# Security policy

Agent plugins can instruct models to use tools and may bundle executable helpers. Treat installation as a code-review decision.

The sanitized public root and its reachable history do not accept secrets, credentials, private memories, production data, personal paths, real-name metadata, or unredacted audit evidence. The Python bootstrap uses argument-vector subprocess calls rather than a shell. Setup writes a dedicated managed source checkout, local `~/.agent-toolkit` receipts and backups, native plugin configuration, and marked guidance blocks unless `--no-guidance` is supplied. It does not copy client credentials, authentication state, or personal memories.

When a standalone Codex CLI does not expose the runtime-owned `openai-curated` marketplace, setup clones `openai/plugins` over HTTPS into private toolkit state, verifies the Git origin, and generates a local adapter containing only allowlisted paths. It never registers another source under Codex's reserved official marketplace name.

Receipt and backup files are created with owner-only modes and symlink-safe paths on POSIX systems. On Windows they inherit the current user profile’s access controls; an equivalent owner-only ACL guarantee has not yet been verified.

Marketplace identity is checked against its exact local path or canonical GitHub repository. Codex's source-less reserved runtime catalog is accepted only when the complete allowlisted OpenAI selector set is available. Pre-existing marketplaces are never removed unless the receipt created them, and pre-existing plugins are never managed unless the user supplies `--adopt-existing`.

Third-party and provider code is not vendored. `catalog/upstreams.json` is the reviewed allowlist for repository names, package names, plugin selectors, and release artifacts. Marketplace updates follow named upstream branches, so running `update` is also a decision to trust new code from those listed providers. Use `--core-only` when that is not acceptable.

The one-line launcher may install missing Git and Python with a detected operating-system package manager. It prints the missing prerequisites before invoking Homebrew, `apt`, `dnf`, `pacman`, `apk`, `zypper`, or `winget`; administrator approval may be requested by the OS. Set `AGENT_KIT_AUTO_PREREQS=0` to disable this behavior.

Matt Pocock's complete skill bundle and the allowlisted Hallmark/Vercel frontend trees intentionally track upstream `main` so updates can receive provider changes. Setup validates complete selected trees, rejects links and duplicate or unsafe names, records each exact fetched commit, inventory, and managed target, and refuses unreceipted destination conflicts unless the user explicitly adopts them. It checkpoints pending ownership before changing skill trees, so the unchanged setup command can recover after an interruption. Adopted or changed receipt-owned trees are backed up before replacement; receipt-owned skills removed upstream or from an allowlist are archived out of agent discovery. This protects integrity after resolution but does not make a mutable upstream equivalent to a reviewed immutable pin. Running install/update accepts the provider's current branch; `doctor` verifies the local result against the receipted commit.

Automatic updates are disabled by default. `auto-update enable` is explicit authorization to create one current-user launchd job, systemd user timer, or Windows scheduled task. The scheduled wrapper is owner-only where POSIX modes apply, captures the user's current executable search path, disables automatic prerequisite installation, follows the receipted GitHub repository/channel, and logs locally. `auto-update disable` removes only the known schedule and wrapper; it does not uninstall the toolkit or upstream packages. Enabling automatic updates accepts future mutable `stable` and allowlisted upstream changes without a per-run prompt.

Graphify runs from a toolkit-owned virtual environment and its discovery instructions pin that exact executable. Existing unreceipted Graphify skill directories are refused unless explicitly adopted; changed adopted copies are preserved before replacement. `CODEX_HOME` and `CLAUDE_CONFIG_DIR`, when supplied, must be non-empty absolute directories and may not be a filesystem root.

Obscura is downloaded only from its GitHub release URL. Setup selects an allowlisted platform archive, verifies the archive plus executable and worker SHA-256 values, rejects archive traversal and link entries, and only then copies the payload into toolkit state. Existing cached payloads and MCP registrations are rechecked exactly before use. The MCP server uses local stdio; setup does not expose its unauthenticated HTTP transport.

Upstream packages are deliberately preserved during Agent Toolkit uninstall because another project or installer may share them. Remove those packages through their original package managers only after reviewing ownership.

Report a suspected vulnerability through a [private GitHub security advisory](https://github.com/udhawan97/agent-toolkit/security/advisories/new). Do not open a public issue containing exploit details, credentials, or private data.

Supported security fixes target the latest published `stable` preview. Earlier versions may be fixed when a safe backport is practical.

# Disposable core lifecycle

This manual acceptance test keeps all native marketplace, plugin, receipt, and guidance state in a fresh temporary root. It intentionally retains that root for inspection; the operating system can clear it later.

```bash
AGENT_KIT_TEST_ROOT=$(mktemp -d)
mkdir -p "$AGENT_KIT_TEST_ROOT/home" "$AGENT_KIT_TEST_ROOT/codex" "$AGENT_KIT_TEST_ROOT/claude"

HOME="$AGENT_KIT_TEST_ROOT/home" \
CODEX_HOME="$AGENT_KIT_TEST_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_TEST_ROOT/claude" \
./bin/agent-kit install --source local --clients both --profile recommended --core-only

HOME="$AGENT_KIT_TEST_ROOT/home" \
CODEX_HOME="$AGENT_KIT_TEST_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_TEST_ROOT/claude" \
./bin/agent-kit doctor --core-only

HOME="$AGENT_KIT_TEST_ROOT/home" \
CODEX_HOME="$AGENT_KIT_TEST_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_TEST_ROOT/claude" \
./bin/agent-kit update --core-only

HOME="$AGENT_KIT_TEST_ROOT/home" \
CODEX_HOME="$AGENT_KIT_TEST_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_TEST_ROOT/claude" \
./bin/agent-kit uninstall --remove-guidance
```

Acceptance requires both clients to report the marketplace and every profile plugin after install and update, the receipt to remain owner-only on POSIX, Claude uninstall to use `--keep-data`, and the final marketplace lists plus managed guidance blocks to be empty. On Windows, record the inherited ACL until an owner-only ACL assertion is added. A public `stable` preview additionally requires a clean clone of the exact candidate SHA. An immutable tagged release also requires fresh authenticated invocation of every bundled skill in both clients.

Before uninstall, verify that the Codex plugin's canonical `skills/` root and the Claude plugin adapter's `skills/` root each contain exactly 15 `SKILL.md` entrypoints, even though the Codex package also contains the nested Claude adapter for marketplace portability. Confirm `claude plugin details evidence-workflows@agent-toolkit` reports the same 15 names. Confirm `dev-review`, `improve-userflow-design`, `loop-refine-release`, `main-cleanup`, `releasegit`, and `tech-debt` carry `disable-model-invocation: true` in the installed Claude adapter and `allow_implicit_invocation: false` in installed Codex metadata.

## Disposable expanded-profile lifecycle

Run this only with network access, Git, Python 3.10+ with `venv` support, and the two real client CLIs. It fetches the allowlisted upstream packages, creates a managed Graphify environment, resolves the current Matt Pocock, Hallmark, and Vercel branches, and downloads a checksum-verified Obscura archive into a disposable home.

```bash
AGENT_KIT_UPSTREAM_ROOT=$(mktemp -d)
mkdir -p "$AGENT_KIT_UPSTREAM_ROOT/home" "$AGENT_KIT_UPSTREAM_ROOT/codex" "$AGENT_KIT_UPSTREAM_ROOT/claude"

HOME="$AGENT_KIT_UPSTREAM_ROOT/home" \
CODEX_HOME="$AGENT_KIT_UPSTREAM_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_UPSTREAM_ROOT/claude" \
./bin/agent-kit install --source local --clients both --profile recommended

HOME="$AGENT_KIT_UPSTREAM_ROOT/home" \
CODEX_HOME="$AGENT_KIT_UPSTREAM_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_UPSTREAM_ROOT/claude" \
./bin/agent-kit doctor

HOME="$AGENT_KIT_UPSTREAM_ROOT/home" \
CODEX_HOME="$AGENT_KIT_UPSTREAM_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_UPSTREAM_ROOT/claude" \
./bin/agent-kit update
```

Acceptance requires the upstream receipt to record exact commits and managed targets for `matt-pocock-skills`, `hallmark`, and `vercel-frontend-skills`; Hallmark plus the three allowlisted Vercel skill trees must byte-match their receipted source in both client discovery roots. No unallowlisted Vercel skill may appear.

## Automatic-update command generation

Repository tests exercise GitHub-source gating, owner-only POSIX configuration/wrapper modes, and daily/weekly command parsing without registering a real background job. Before promoting scheduler support on a platform, use a disposable OS account to run `auto-update enable`, `status`, `run`, and `disable`; confirm the current-user schedule is active, the log is written, prerequisite installation remains disabled, and disable removes only the known schedule files.

Acceptance requires all toolkit and upstream doctor rows to pass, each Graphify client skill to name the exact invokable toolkit-managed executable, every Matt Pocock skill discovered at the receipted source commit to byte-match that source and resolve in both client homes, provider marketplace identities plus plugins to be installed and enabled, the Obscura executable and worker checksums to match the catalog, and both MCP registrations to point exactly to the toolkit-managed binary with the `mcp` argument. Provider login is not part of this test.

Uninstall the core layer with `--remove-guidance`. Then confirm upstream packages remain, as documented; removal of provider-managed packages is intentionally outside Agent Toolkit's uninstall contract.

Also verify ownership fail-closed behavior before release: manually install a matching plugin, confirm bootstrap installation stops without `--adopt-existing`, and confirm receipt-less update and uninstall leave that plugin untouched. The receipt stages ownership before a native install so an interruption can be recovered safely; rerun the same install command to complete any missing plugin. Native commands are idempotent, and each client’s recovery state is recorded independently.

Verify reconciliation separately: install with only one client executable visible, make the second client visible, rerun the no-argument launcher, and confirm the new client inherits the receipted profile, upstream, and guidance policy before the final doctor passes. For Matt skills, test a synthetic prior receipt with one now-removed skill and confirm update moves that directory into the backup tree rather than leaving it agent-visible.

After `stable` is public, repeat the lifecycle from the real remote launcher in fresh homes and a fresh source directory:

```bash
AGENT_KIT_REMOTE_ROOT=$(mktemp -d)
mkdir -p "$AGENT_KIT_REMOTE_ROOT/home" "$AGENT_KIT_REMOTE_ROOT/codex" "$AGENT_KIT_REMOTE_ROOT/claude"

AGENT_KIT_SOURCE_DIR="$AGENT_KIT_REMOTE_ROOT/source" \
HOME="$AGENT_KIT_REMOTE_ROOT/home" \
CODEX_HOME="$AGENT_KIT_REMOTE_ROOT/codex" \
CLAUDE_CONFIG_DIR="$AGENT_KIT_REMOTE_ROOT/claude" \
sh -c "$(curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup)" -- install --clients both
```

Verify the managed checkout and both native marketplace roots resolve to the exact published `stable` candidate before reporting public installation as complete.

The automated launcher regression suite also proves that a depth-1 checkout can fast-forward and that a clean local commit ahead of the fetched channel is refused:

```bash
python -m unittest discover -s tests -v
```

POSIX behavior runs on macOS and Linux. The mirrored PowerShell behavior is configured to run on the Windows CI job.

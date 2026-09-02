# Getting started

Agent Toolkit installs one curated catalog through the native plugin marketplace built into Codex, Claude Code, or both. It does not replace either client and does not copy authentication between them.

## Prerequisites

- Codex CLI, Claude Code, or both available on `PATH`
- macOS/Linux copy-paste path: the system's `curl` and POSIX shell

The agent client is the only product prerequisite you choose. When Git or Python 3.10+ with `venv` support is missing, the launcher attempts to install it with a supported OS package manager. Graphify uses a toolkit-managed Python environment, and Matt Pocock's skills are copied directly from their validated source, so Node.js, `npx`, `uv`, and `pipx` are not required.

Automatic system-package setup supports Homebrew, `apt`, `dnf`, `pacman`, `apk`, `zypper`, and Windows `winget`. Set `AGENT_KIT_AUTO_PREREQS=0` if you want setup to stop and let you install prerequisites yourself.

Homebrew must already be available for automatic package installation on macOS. Without it, setup gives a manual Git/Python instruction and exits safely.

A prior macOS core-profile lifecycle covered 14 owned workflows; the current 15-workflow 0.3.0 candidate and its expanded profile still need a fresh clean install/update/doctor run. Linux and Windows validation is configured in CI, while their native client lifecycles still need community verification.

## Fast setup

### macOS or Linux

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup.ps1 | iex
```

The launcher stores its managed source checkout under the platform’s user data directory. Override this with `AGENT_KIT_SOURCE_DIR` when necessary. Rerun the same one-line command later: an existing installation is refreshed automatically, a newly available second client inherits the saved setup, and a final `doctor` verifies the result.

## Review-first setup

```bash
git clone --branch stable --depth 1 https://github.com/udhawan97/agent-toolkit.git
cd agent-toolkit
./bin/agent-kit validate
./bin/agent-kit install --source local --dry-run
./bin/agent-kit install --source local
```

Windows users can replace `./bin/agent-kit` with `python bin/agent-kit`.

### Downloaded ZIP

The ZIP is a manual local-source path, not an auto-updating installation. Extract it to a location you will keep, then run:

```bash
python bin/agent-kit install --source local
```

To update later, replace the extracted contents with a newer `stable` ZIP at the same path, then run `python bin/agent-kit update`. Use the fast launcher instead when you want the source checkout fetched automatically.

## Select clients and profiles

```bash
./bin/agent-kit install --clients codex
./bin/agent-kit install --clients claude
./bin/agent-kit install --clients both --profile recommended
./bin/agent-kit install --profile skills-only
./bin/agent-kit install --profile full
```

The default `auto` selection installs into every supported client found on `PATH`.

| Profile | Includes |
| --- | --- |
| `recommended` | Complete public-safe stack: owned workflows, tracked frontend skills, upstream tools, provider essentials, Obscura, and guidance |
| `skills-only` | Owned workflows, Graphify, Matt Pocock's skills, Hallmark, Vercel's focused frontend set, and guidance |
| `full` | Explicit alias for the complete allowlist in this preview |

Use `--core-only` to skip every upstream package. All 15 original workflows still install; orchestration skills use their bundled fallbacks where an optional upstream helper is absent.

Remote Windows examples:

```powershell
# Codex only
$s = [scriptblock]::Create((irm https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup.ps1))
& $s install --clients codex
```

```powershell
# Claude Code only
$s = [scriptblock]::Create((irm https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup.ps1))
& $s install --clients claude
```

## Shared working agreement

```bash
./bin/agent-kit install
```

The standard profiles add one marked, managed block to `~/.codex/AGENTS.md` and/or `~/.claude/CLAUDE.md`. Existing content is retained; backup files are owner-only on POSIX systems and inherit the user profile's access controls on Windows.

Skip it when needed:

```bash
./bin/agent-kit install --no-guidance
```

## Invoke a skill

Restart active client sessions after installation.

For example, ask for a read-only branch inventory or a user-flow audit:

Codex prompt:

```text
Use $main-cleanup to audit every branch and show what is safe to integrate. Do not change anything.
```

Claude Code command:

```text
/evidence-workflows:improve-userflow-design Audit the primary journey. Do not edit anything.
```

All 15 original workflows use the same naming pattern. Product-specific guardrails activate only when their named public product or release path is in scope.

## Maintain the installation

From a clone:

```bash
./bin/agent-kit doctor
./bin/agent-kit update
./bin/agent-kit uninstall
```

Using the fast launcher:

Update:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- update
```

Optional weekly automatic updates:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- auto-update enable --frequency weekly
```

Check or disable the schedule:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- auto-update status
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- auto-update disable
```

Verify:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- doctor
```

Uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- uninstall
```

Maintenance defaults come from `~/.agent-toolkit/state.json`. The core receipt records source, ref, selected profile, plugin and marketplace ownership, upstream opt-in, and guidance opt-in. Later `update` and `doctor` preserve `--core-only` and `--no-guidance` choices; when one new supported client appears on `PATH`, update applies the same saved policy to it automatically. `~/.agent-toolkit/upstreams.json` also records exact resolved upstream details, including the Matt Pocock, Hallmark, and Vercel source commits, installed skill inventories, and managed targets.

Scheduled updates are disabled unless the user runs `auto-update enable`. They require an existing GitHub installation receipt and follow the repository and channel recorded there (`stable` or `main`), run at the current-user level, set `AGENT_KIT_AUTO_PREREQS=0` so they do not install system prerequisites, and record configuration and output under `~/.agent-toolkit/auto-update/`. They are unavailable for local review or development checkouts. Disabling the schedule does not roll back an update already applied. Because automatic runs trust future channel and allowlisted upstream changes without a new prompt, use manual updates when you want to review each diff first.

Windows uses the same command shape through a downloaded script block:

```powershell
$s = [scriptblock]::Create((irm https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup.ps1))
& $s auto-update enable --frequency weekly
```

Upstream packages remain owned by their original package managers. `uninstall` removes the toolkit-owned layer; it does not mass-delete provider or third-party packages.

## Advanced options

```bash
# Track integration work instead of stable
AGENT_KIT_CHANNEL=main ./bin/setup install

# Explicitly adopt already installed matching plugins or conflicting tracked skill directories
./bin/agent-kit install --adopt-existing

# Remove the managed guidance block during uninstall
./bin/agent-kit uninstall --remove-guidance

# Also delete Claude plugin data
./bin/agent-kit uninstall --purge-data

# Install only the toolkit-owned workflows
./bin/agent-kit install --core-only --no-guidance
```

Use adoption and data purging only when you intend those ownership changes.

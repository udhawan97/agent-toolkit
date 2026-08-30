# Getting started

Agent Toolkit installs one curated catalog through the native plugin marketplace built into Codex, Claude Code, or both. It does not replace either client and does not copy authentication between them.

## Prerequisites

- Codex CLI, Claude Code, or both available on `PATH`
- macOS/Linux copy-paste path: the system's `curl` and POSIX shell

The agent client is the only product prerequisite you choose. When Git or Python 3.10+ with `venv` support is missing, the launcher attempts to install it with a supported OS package manager. Graphify uses a toolkit-managed Python environment, and Matt Pocock's skills are copied directly from their validated source, so Node.js, `npx`, `uv`, and `pipx` are not required.

Automatic system-package setup supports Homebrew, `apt`, `dnf`, `pacman`, `apk`, `zypper`, and Windows `winget`. Set `AGENT_KIT_AUTO_PREREQS=0` if you want setup to stop and let you install prerequisites yourself.

Homebrew must already be available for automatic package installation on macOS. Without it, setup gives a manual Git/Python instruction and exits safely.

The macOS native install and maintenance lifecycle is verified. Linux and Windows validation is configured in CI, while their native client lifecycles still need community verification.

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
./bin/agent-kit install --dry-run
./bin/agent-kit install
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
| `recommended` | Complete public-safe stack: owned workflows, upstream tools, provider essentials, Obscura, and guidance |
| `skills-only` | Owned workflows, Graphify, Matt Pocock's skills, and guidance |
| `full` | Explicit alias for the complete allowlist in this preview |

Use `--core-only` to skip every upstream package.

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

Codex prompt:

```text
Use $improve-userflow-design to audit the primary journey. Do not edit anything.
```

Claude Code command:

```text
/evidence-workflows:improve-userflow-design Audit the primary journey. Do not edit anything.
```

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

Verify:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- doctor
```

Uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- uninstall
```

Maintenance defaults come from `~/.agent-toolkit/state.json`. The core receipt records source, ref, selected profile, plugin and marketplace ownership, upstream opt-in, and guidance opt-in. Later `update` and `doctor` preserve `--core-only` and `--no-guidance` choices; when one new supported client appears on `PATH`, update applies the same saved policy to it automatically. `~/.agent-toolkit/upstreams.json` also records exact resolved upstream details, including the Matt Pocock source commit, full installed skill inventory, and managed targets.

Upstream packages remain owned by their original package managers. `uninstall` removes the toolkit-owned layer; it does not mass-delete provider or third-party packages.

## Advanced options

```bash
# Track integration work instead of stable
AGENT_KIT_CHANNEL=main ./bin/setup install

# Explicitly adopt already installed matching plugins or conflicting Matt skill directories
./bin/agent-kit install --adopt-existing

# Remove the managed guidance block during uninstall
./bin/agent-kit uninstall --remove-guidance

# Also delete Claude plugin data
./bin/agent-kit uninstall --purge-data

# Install only the toolkit-owned workflows
./bin/agent-kit install --core-only --no-guidance
```

Use adoption and data purging only when you intend those ownership changes.

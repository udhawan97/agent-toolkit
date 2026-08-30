# Troubleshooting

Agent Toolkit stops instead of guessing when client discovery, marketplace identity, or ownership is ambiguous.

## Neither client is found

Run:

```bash
command -v codex
command -v claude
codex --version
claude --version
```

Install at least one supported client and ensure its executable is on `PATH`, then rerun setup. You can also target one explicitly with `--clients codex` or `--clients claude`.

## Git or Python could not be installed

The one-line launcher attempts to install missing Git and Python through a supported package manager. If it cannot, check which tools are available:

```bash
git --version
python3 --version
```

Install Git and Python 3.10 or newer with your operating system's package manager, then rerun the exact same setup command. On Debian or Ubuntu, include the venv package:

```bash
sudo apt-get install git python3 python3-venv
```

If you want only the repository-owned workflows for now:

```bash
./bin/agent-kit install --core-only --no-guidance
```

## Marketplace source does not match

Another marketplace named `agent-toolkit` is registered from a different path, repository, or branch. Inspect the native lists:

```bash
codex plugin marketplace list --json
claude plugin marketplace list --json
```

Do not remove an unfamiliar marketplace until you understand who owns it. Rename or remove the conflict with the native client, then rerun installation.

The upstream marketplaces `diagram-design`, `ponytail`, `understand-anything`, `openai-curated`, and `claude-plugins-official` are also checked against their canonical repositories. Their expected sources are listed in [UPSTREAMS.md](UPSTREAMS.md). Provider-native marketplace commands do not consistently expose a branch or commit for every source, so Agent Toolkit does not claim ref verification where the client cannot report it.

## A plugin already exists

Setup refuses to take over a pre-existing matching plugin. If you intentionally want Agent Toolkit to manage it:

```bash
./bin/agent-kit install --adopt-existing
```

Without adoption, receipt-less update and uninstall leave that plugin untouched.

## The managed checkout has local changes

The quick launcher will not overwrite them. Inspect the checkout shown in the error:

```bash
git -C /path/from/the/error status --short
```

Commit or move your work, or continue managing that clone manually. The launcher never resets or cleans the directory.

## Update stops during Codex preflight

The candidate could not install in a disposable Codex home, so the active plugin was left in place. Run:

```bash
./bin/agent-kit validate --native
./bin/agent-kit doctor
```

Resolve the manifest, marketplace, Python, or network error before retrying.

## Graphify installation fails

Graphify's package name is `graphifyy`, while its command is `graphify`. Agent Toolkit installs it into `~/.agent-toolkit/tools/graphify/<version>/`; it does not trust an unrelated `graphify` executable on `PATH`. The generated Graphify skill names that exact managed executable, and `doctor` fails if the instruction or command marker drifts.

Check whether your Python can create isolated environments:

```bash
python3 -m venv /tmp/agent-toolkit-venv-check
```

If that fails on Debian or Ubuntu, install `python3-venv`. Then rerun the original one-line setup command and `agent-kit doctor`.

## Matt Pocock skills do not match

Every install/update fetches the current upstream `main`, records its exact commit, and byte-checks all discovered skill trees. Run the explicit refresh to repair ordinary drift:

```bash
curl -fsSL https://raw.githubusercontent.com/udhawan97/agent-toolkit/stable/bin/setup | sh -s -- update
```

An existing skill directory without a matching toolkit receipt is left untouched and stops setup. If you explicitly intend to replace it, rerun with `--adopt-existing`; setup first preserves that copy under `~/.agent-toolkit/backups/matt-pocock-skills/`. It refuses symlinked destinations or a modified managed source checkout; inspect those paths instead of deleting them blindly. Receipt-owned skills removed from Matt's current branch are archived under the same backup root during update.

## Obscura download or checksum fails

Setup pins one release asset for each supported platform and verifies its SHA-256 before extraction. A mismatch is a hard stop. Do not bypass it; check the upstream release and `catalog/upstreams.json`, then wait for a reviewed catalog update.

Windows ARM64 is not in the current Obscura allowlist. Use `--profile skills-only` or `--core-only` on that platform.

## An upstream plugin needs a login

Agent Toolkit installs plugin code but never copies provider authentication. Complete the provider's own login flow when you first use that plugin. Account-connected integrations are intentionally excluded from the default allowlist.

## Setup was interrupted

Rerun the same install command. The receipt records pending ownership before changing native plugins, Graphify discovery, or Matt Pocock skill trees, so the same command can safely complete a partial refresh. You may also run uninstall to remove a receipt-owned partial installation. Uninstall checkpoints each completed client, so rerunning it continues after an earlier client-specific failure.

If setup rejects `CODEX_HOME` or `CLAUDE_CONFIG_DIR`, give it a non-empty absolute directory below your user profile. Relative paths and filesystem roots such as `/` or a Windows drive root are refused before any client files are changed.

## Native validation is skipped

`validate --native` prints an explicit skip when Claude Code or Codex’s system plugin validator is unavailable. Portable repository validation still runs, but a stable promotion requires both native validators on a supported machine.

## Recover managed guidance

Managed guidance backups are retained under `~/.agent-toolkit/backups/`. Uninstall removes only the marked toolkit block when `--remove-guidance` is supplied; it does not automatically overwrite current guidance with an older backup. Install with `--no-guidance` when no global guidance change is desired.

## Still blocked?

Run `./bin/agent-kit doctor --native`, remove any secrets or personal paths from the output, and open a GitHub issue with client versions, operating system, the exact command, and the smallest relevant error message.

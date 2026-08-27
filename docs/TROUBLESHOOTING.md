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

## Graphify or Matt Pocock prerequisites are missing

The complete profiles need both commands:

```bash
uv --version
npx --version
```

Install [`uv`](https://docs.astral.sh/uv/) and a current Node.js release, then rerun setup. If you want only the repository-owned workflows for now:

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

## Graphify installs but is not found

Graphify's package name is `graphifyy`, while its command is `graphify`. When `uv` installed it, run:

```bash
uv tool update-shell
```

Open a new terminal and rerun `agent-kit doctor`. The installer can invoke Graphify through `uv` during setup, but future interactive sessions still benefit from having the tool directory on `PATH`.

## Obscura download or checksum fails

Setup pins one release asset for each supported platform and verifies its SHA-256 before extraction. A mismatch is a hard stop. Do not bypass it; check the upstream release and `catalog/upstreams.json`, then wait for a reviewed catalog update.

Windows ARM64 is not in the current Obscura allowlist. Use `--profile skills-only` or `--core-only` on that platform.

## An upstream plugin needs a login

Agent Toolkit installs plugin code but never copies provider authentication. Complete the provider's own login flow when you first use that plugin. Account-connected integrations are intentionally excluded from the default allowlist.

## Setup was interrupted

Rerun the same install command. The receipt records a pending client before setup creates its marketplace, then records plugin ownership before native installation. You may also run uninstall to remove a receipt-owned partial installation. Uninstall checkpoints each completed client, so rerunning it continues after an earlier client-specific failure.

## Native validation is skipped

`validate --native` prints an explicit skip when Claude Code or Codex’s system plugin validator is unavailable. Portable repository validation still runs, but a stable promotion requires both native validators on a supported machine.

## Recover managed guidance

Managed guidance backups are retained under `~/.agent-toolkit/backups/`. Uninstall removes only the marked toolkit block when `--remove-guidance` is supplied; it does not automatically overwrite current guidance with an older backup. Install with `--no-guidance` when no global guidance change is desired.

## Still blocked?

Run `./bin/agent-kit doctor --native`, remove any secrets or personal paths from the output, and open a GitHub issue with client versions, operating system, the exact command, and the smallest relevant error message.

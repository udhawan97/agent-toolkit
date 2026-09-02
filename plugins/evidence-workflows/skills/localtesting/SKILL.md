---
name: localtesting
description: Discover and execute the current project's own clean local build or install workflow, replace its local test artifact, remove stale duplicate macOS app bundles from Spotlight when applicable, and verify the real local surface. Use when the user invokes /localtesting or asks to locally build, install, reinstall, refresh, replace, wipe, deduplicate, or test the project in the active workspace from its latest commit.
license: MIT
---

# Project-Aware Local Testing

## Purpose

Build and install the project that contains the current working directory, using that project's own documented workflow. Never infer the product, repository, app name, bundle identifier, install path, or build command from a previous invocation.

Protect source changes and user data. Treat “wipe” as replacing generated or installed test artifacts unless the user explicitly authorizes source or application-data deletion.

## Execution Preconditions

Verify the command runner first:

```bash
pwd
```

If process launch fails before the command runs, retry a trivial command and report a runner/session blocker if it still fails. Use the runtime's workspace-dependency discovery capability when one is available. Do not attribute a runner failure to the project.

## Resolve the Project Contract

1. Resolve the project root.
   - Prefer an explicit path from the user.
   - Otherwise run `git rev-parse --show-toplevel` from the current working directory.
   - For a non-Git folder, use the current directory only when it contains a clear build manifest. If the active directory is not a project, stop and ask for the target path.

2. Read project instructions before choosing commands.
   - Read the applicable `CLAUDE.md` and `AGENTS.md` files and any matching project-specific skill or instructions.
   - Inspect `README*`, `CONTRIBUTING*`, `docs/`, `scripts/`, `Makefile`, `justfile`, and package-manager scripts.
   - Inspect platform manifests such as `Package.swift`, `project.yml`, Xcode projects/workspaces, `Cargo.toml`, Tauri configuration, `package.json`, and Electron configuration only as relevant.
   - Search for `install`, `local`, `build`, `package`, `bundle`, `run`, `clean`, and `uninstall` commands with `rg`. Prefer a documented repo script over reconstructing its internals.

3. Confirm source state.
   - Run `git status --short --branch` and `git log -1 --oneline --decorate` when the project uses Git.
   - Default “latest commit” to the current `HEAD`. If the user asks for latest remote, fetch and compare before using `git pull --ff-only` on a clean tree.
   - If the tree is dirty, explain that a normal build may include uncommitted changes and ask before building. Never stash, reset, discard, or remove source changes without authorization.

4. Establish project facts before mutation.
   - Record the project root, revision, build system, canonical clean build/install command, output artifact, installed test path, log path, and launch/smoke-test command.
   - For macOS apps, derive the product name and `CFBundleIdentifier` from project configuration or the built app's `Contents/Info.plist`. Derive the canonical install destination from the repo installer or packaging documentation.
   - Identify user-data paths that must remain untouched.
   - If multiple app targets or plausible install commands remain, stop and ask which target to test. Do not choose by product-name familiarity.

## Build and Install

1. Run the project's own clean build or local installer from the resolved project root.
2. Close the installed app first when the project workflow requires replacement and does not handle termination itself.
3. Preserve logs and report the first actionable compiler, dependency, signing, packaging, or permission failure.
4. Do not clean stale copies if the replacement build or install fails.
5. Verify the new canonical artifact exists and matches the derived identity before removing anything else.

For web apps or services, run the documented local build/start workflow and skip macOS app-bundle cleanup. Verify the documented URL, health check, or smoke-test surface instead.

## Deduplicate macOS App Bundles

After a successful macOS app install, preview matching non-canonical bundles with the bundled helper. Supply only values proven from the current project:

Resolve this skill's installed directory from the active runtime, then run its bundled helper:

```bash
CLEANUP_RECEIPT_DIR="$(mktemp -d)"
chmod 700 "$CLEANUP_RECEIPT_DIR"
CLEANUP_RECEIPT="$CLEANUP_RECEIPT_DIR/approved-preview.receipt"

<skill-directory>/scripts/cleanup-old-app-copies.sh \
  --canonical-app "$CANONICAL_APP" \
  --bundle-id "$BUNDLE_ID" \
  --scan-root "$PROJECT_ROOT" \
  --receipt "$CLEANUP_RECEIPT"
```

Add `--legacy-bundle-id "$OLD_BUNDLE_ID"` or `--legacy-executable "$OLD_EXECUTABLE"` only when repository or bundle metadata proves the former identity. Repeat those options and `--scan-root` as needed.

Show the exact preview to the user and obtain explicit cleanup approval before repeating the same command with `--apply` and the same `--receipt`. The helper binds the approved paths and identity fingerprints to that owner-only receipt and refuses the entire cleanup when a candidate appears, disappears, or changes after preview. Create a new receipt for every new preview, and remove its temporary directory after the approved apply or cancellation. A general request to build or test locally is not cleanup approval. The helper must:

- preserve the canonical app unconditionally;
- match bundles by current or explicitly supplied legacy identifiers plus executable identity, and require the same signing team whenever the canonical app has one;
- move only candidates inside normal Applications locations, Xcode DerivedData, or explicitly supplied project/build roots; report Spotlight matches elsewhere without moving them;
- skip mounted volumes and Trash;
- move stale `.app` bundles to Trash rather than permanently deleting them;
- leave source files, whole build directories, DMGs, user documents, preferences, containers, caches, application support, databases, and worktrees untouched;
- refresh LaunchServices and Spotlight metadata, then fail unless the canonical app is the only live indexed match.

Do not use `--apply` until the preview paths are understood and the canonical app has been verified. Never reuse a receipt after a refused, completed, or cancelled cleanup.

## Verify the Real Local Surface

Use checks appropriate to the discovered project contract:

- Confirm the installed artifact path, version, build number, and identity.
- For macOS apps, run `codesign --verify --deep --strict --verbose=2 "$CANONICAL_APP"` when signing applies.
- Compare the installed executable or artifact with the just-built output when the project provides both and byte comparison is meaningful.
- Launch the exact installed path and confirm the process originates from it.
- Run a bounded project-specific smoke test on the actual installed app, local URL, CLI, or service—not only unit tests or build logs.
- For macOS apps, query Spotlight by bundle identifier and verify that only the canonical live bundle remains.
- Re-run `git status --short --branch` and report whether the source tree changed.

## Failure Handling

- If project discovery is ambiguous, report the candidates and request the target instead of falling back to a previously known product.
- If the installer is missing or stale, use the repository's documented fallback; do not invent copy/signing logic without explaining the gap.
- If cleanup cannot move a duplicate, leave the canonical install intact and report the exact path and error.
- If Spotlight still shows a duplicate, verify whether its path exists, inspect its bundle identifier, and refresh that registration. Do not reset the entire Spotlight index or delete all DerivedData first.
- Treat `spctl --assess` rejection of an ad-hoc local build as informational when `codesign --verify` passes and the app launches, unless the project contract requires notarization.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

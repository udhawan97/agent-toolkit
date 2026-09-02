---
name: releasegit
description: Prepare and publish a verified Orifold GitHub release when the user invokes /releasegit or asks to ship a v* or release-v* tag, including tests, packaging, CI, assets, installer paths, checksums, and live release verification.
license: MIT
disable-model-invocation: true
---

# ReleaseGit

Ship Orifold from the active repository checkout to a verified GitHub release. Resolve the checkout from the user's explicit path or current Git root; never assume a home-directory layout. Do not treat a tag or local package as completion.

## Baseline

1. Run `git status --short --branch`, fetch tags, and compare `HEAD`, `origin/main`, and the requested tag.
2. Preserve unrelated dirty or untracked files. Ask before including pre-existing changes in a release.
3. Inspect the current `.github/workflows/release.yml`, README, installer scripts, and the previous release. Derive conventions from current files rather than old pdFold/PDFold history.

## Release gate

Run the applicable checks:

```zsh
swift build
swift test
git diff --check
zsh -n install.sh
zsh -n scripts/install-mac.sh
zsh -n scripts/uninstall-mac.sh
ORIFOLD_UNIVERSAL=1 ./scripts/install-mac.sh --clean --no-open --package-only --package /tmp/Orifold.zip
```

Inspect failures before editing. Fix only confirmed blockers, keep patches scoped, and rerun affected gates.

## Publish and verify

1. Ensure the requested tag identifies the exact validated commit. If the tag already exists at any other commit, return `HOLD`: never move, delete, recreate, or force-update an existing release tag. Use a new version tag instead.
2. Let the release workflow build the universal app, DMG, stable-name `Orifold.dmg`, `Orifold.zip`, checksum, and `manifest.json`.
3. Watch the hosted workflow through completion and inspect logs for any failed or skipped release-critical step.
4. Verify the GitHub release title, tag, latest/prerelease status, and downloadable assets.
5. Download the published assets to a temporary directory and verify checksums, bundle metadata, embedded frameworks/resources, and `codesign --verify --deep --strict`.
6. Verify the one-line installer and latest-release URLs resolve to the intended release.
7. Verify the live documentation/download page and final `main`/tag alignment.

For a local acceptance install, use `scripts/install-mac.sh --clean --verbose`, then verify `~/Applications/Orifold.app`, bundle id `com.ud.Orifold`, launch behavior, and a clean source tree.

## Report

End with the exact commit and tag, checks run, published assets, installed/live surfaces verified, remaining risks, and one verdict: `PASS`, `PASS WITH FOLLOW-UPS`, `HOLD`, or `BLOCKED`.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

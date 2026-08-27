# Maintaining Agent Toolkit

## Package contract

Each folder under `plugins/` is one self-contained package. It carries both `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`, while its `skills/` directory is the canonical shared payload. Never make a packaged skill reach into a sibling plugin or a developer home directory.

Both marketplace catalogs must list the same plugin names. Plugin versions must match across both manifests and the Claude marketplace entry. Release plugin changes with strict semantic versions.

Outside packages belong in `catalog/upstreams.json`, not under `plugins/`. Each upstream entry must name its original repository, distribution mechanism, license signal, supported clients, and the smallest allowlisted plugin set. Release archives also require an immutable version plus archive and executable-payload SHA-256 values for every supported platform.

## Adding a plugin

1. Scaffold the Codex package with the system plugin creator into `plugins/` and the repository marketplace.
2. Add the matching Claude manifest and marketplace entry.
3. Restrict shared skill frontmatter to the portable Agent Skills fields.
4. Add the plugin to one or more profiles.
5. Run `./bin/agent-kit validate --native`.
6. Test a local installation with isolated client homes before updating the changelog.

## Adding an upstream bundle

1. Confirm the repository belongs to the named provider or maintainer.
2. Inspect its license, manifest, release/update path, authentication behavior, and executable surfaces.
3. Add the smallest useful bundle to `catalog/upstreams.json`; do not copy its payload.
4. Add the bundle to only the profiles that should install it.
5. Update `docs/UPSTREAMS.md`, `SECURITY.md`, `COMPATIBILITY.md`, and the changelog.
6. Exercise install, update, and doctor from disposable client homes. Test checksum and archive-safety failures for downloaded executables.
7. Run privacy and provenance scans before promotion.

## Release channels

`main` is the integration branch. `stable` is the reviewed preview-install channel and advances only after both native clients install the exact candidate successfully. Immutable `v*` tags are the stricter release boundary and provide rollback points. Never force-update a release tag.

The 0.2.0 preview begins with a one-time privacy reset. Before publishing it, archive the earlier bootstrap repository privately, recreate the public repository at the original URL, and publish only the new privacy-scrubbed root. The launcher preserves a clean checkout of the exact earlier bootstrap root before cloning the replacement. Verify that the earlier commit is not reachable from the recreated public repository. After this sanitized baseline is public, the no-history-rewrite rule in the promotion checklist applies normally.

## Public surface contract

The root README is the first-time-user path; detailed setup and recovery guidance belongs under `docs/`. Keep the generated hero, repo-owned SVGs, quick launcher commands, marketplace manifests, and compatibility claims synchronized.

- Preserve editable SVG sources and require a `viewBox`, accessible title, and inspected render.
- Keep raster assets below practical repository-review sizes and free of text, logos, private data, and unverifiable UI claims.
- Keep `bin/setup` and `bin/setup.ps1` thin: they may fetch a clean managed checkout and delegate lifecycle behavior, but must not reset, clean, or silently overwrite one.
- Run `python bin/agent-kit validate`; it checks local public links, SVG structure, and launcher presence in addition to plugin packaging.

## Stable preview promotion checklist

1. Start from a clean `main` checkout and record `git rev-parse HEAD` as the candidate SHA.
2. Run `python bin/agent-kit validate --native` and both disposable-home lifecycles in [TESTING.md](TESTING.md) on that exact SHA.
3. Run `sh -n bin/setup`, validate `bin/setup.ps1 help` on Windows, and render-inspect every README asset.
4. Confirm the changelog, compatibility matrix, marketplace catalogs, plugin manifests, profile membership, and public commands all describe the candidate.
5. Require the two-round council gate to approve the preview evidence with no blockers.
6. For the one-time 0.2.0 privacy reset, use the private-archive and public-recreation procedure above. For later previews, move `stable` to the candidate SHA without rewriting published history. Then clone the public branch into a clean directory and run the quick launcher plus doctor.
7. Compare the public `main` and `stable` refs with the recorded SHA before announcing the preview.
8. Re-fetch every mutable upstream source used by the profile and confirm it still resolves to the reviewed provider and marketplace identity.

## Immutable release checklist

Complete the stable preview checklist first. Then start fresh authenticated Codex and Claude sessions from the disposable installation and invoke every bundled skill at least once without granting mutation or publication authority. Repeat the public-clone lifecycle on the exact candidate, create an immutable `v*` tag at that SHA, and verify the public tag plus release artifacts before announcing a versioned release.

## Secrets and third-party work

Reference third-party marketplaces rather than vendoring packages without confirmed redistribution rights. Authentication remains per user. Do not add access tokens, account identifiers, personal configuration, private memories, or captured product data to the repository.

---
name: refresh-docs
description: Perform a complete, evidence-led redesign and synchronization of a product README and public website so they match the verified current app, including copy, information architecture, downloads, icons, SVGs, screenshots, demos, social assets, install guidance, and responsive/accessibility polish. Use when the user invokes /refresh-docs or $refresh-docs, asks for a README and website overhaul, wants public docs brought up to date with the app, or requests a FolioOrb-quality product presentation and download experience.
license: MIT
---

# Refresh Docs

Rebuild the public story around the product that actually exists. Make the README and website feel like one original, trustworthy product surface: immediately understandable to a layperson, visually aligned with the current app, and effortless to download or start.

Read [Public Surface Standard](references/public-surface-standard.md) completely before editing. Apply it as the quality rubric and closure checklist.

## Operating contract

- Treat the runnable or shipped app as the visual and behavioral source of truth. Treat source, tests, configuration, release artifacts, and approved product documents as supporting evidence.
- Implement the full refresh; do not stop after an audit or mood board. State a brief plan first, then continue unless a deletion, framework replacement, destructive action, external publication, or material product choice needs approval.
- Preserve the logo's recognizable identity by default. Re-export, clean, animate, or adapt it for light/dark contexts when justified, but do not replace its concept or silhouette unless the user explicitly asks.
- Derive the public visual system from the app's real colors, typography, density, shapes, motion, voice, and interaction character. Do not paste a generic landing-page skin over it.
- Use FolioOrb as a standard for content completeness, proof, progressive disclosure, and download clarity—not as a template to copy. Produce an original structure and design for this product.
- Write for a curious first-time user before writing for developers. Explain outcomes and boundaries in plain language; keep technical setup and architecture available lower in the page.
- Preserve unrelated user changes and repository boundaries, including pre-existing edits inside the README, website, and asset files being refreshed. Integrate around them when ownership is clear; stop and ask for direction when they cannot be safely separated. Never clean, reset, overwrite, or delete user work.
- Never invent features, metrics, testimonials, platform support, signing status, release state, screenshots, or download URLs.

## 1. Establish product truth

1. Read every applicable `AGENTS.md`, `CLAUDE.md`, contribution guide, product-specific skill, ADR, and repository instruction.
2. Inspect `git status --short --branch`, the current revision, and active worktrees. Separate existing changes from this refresh.
3. Discover the README, website/docs source, generated output, build commands, asset directories, release workflows, installers, manifests, and deployed URLs. Do not assume paths or frameworks.
4. If `graphify-out/graph.json` exists, run a scoped `graphify query` about the app surfaces, website, README, assets, install paths, and release flow before broad source searching. Build a graph only when cross-file understanding materially helps.
5. Create a compact fact sheet from evidence:
   - the product's one-sentence job and intended audience;
   - current shipped features and exact UI terminology;
   - supported platforms, architectures, prerequisites, and install modes;
   - privacy, network, data-storage, AI, security, and trust boundaries;
   - current version, release channels, signing/notarization state, updater behavior, checksums, and stable download destinations;
   - known limitations, experimental features, and roadmap items.
6. Run the product through its documented local or installed workflow when safe. Before launch or capture, use a proven isolated temporary data directory, demo profile, or repository fixture. Never open writable live user state without explicit consent, and never expose private user data in public artifacts.
7. Record every claim and planned visual in a coverage ledger with its evidence source and verification status. Mark unsupported items for removal or honest qualification.

If the real app cannot run, continue with the strongest static evidence, label the runtime gap, and do not fabricate current-app screenshots.

## 2. Inventory the public surface

Find and trace all user-visible documentation and assets, including:

- root and nested READMEs, website pages, docs pages, navigation, footer, metadata, and structured data;
- logos, wordmarks, icons, badges, favicons, app icons, SVGs, diagrams, screenshots, posters, videos, animated assets, and social previews;
- installation scripts, download buttons, release links, checksums, update instructions, troubleshooting, and platform requirements;
- duplicated assets, generated copies, stale filenames, case-sensitive path drift, dead routes, broken anchors, and obsolete marketing claims.

Determine which files are sources and which are generated. Edit authoritative sources only unless the repository explicitly versions generated output.

Before editing, name the files or bounded areas expected to change. Treat the redesign request as authority for in-place redesign and additive assets, not for deleting route trees, replacing the website framework, changing the logo concept, or publishing externally.

## 3. Define one public design system

Extract a small token system from the app and existing brand:

- color roles for canvas, surfaces, text, borders, accents, statuses, and focus;
- display/body/mono type roles using the repository's licensed fonts or system fallbacks;
- spacing, radius, border, shadow, icon, screenshot-frame, and motion rules;
- light/dark behavior when supported by the app;
- a distinctive layout rhythm and visual motif rooted in the product's purpose.

Keep the README and website recognizably related without forcing Markdown to imitate the website. Use the same logo family, voice, screenshot set, and color story; adapt composition to each medium.

Reject generic AI-design defaults: interchangeable gradient blobs, fake browser chrome, made-up dashboards, unsupported stat strips, excessive pills, random glass cards, and decorative motion without meaning. Favor fewer, stronger moments and real product proof.

## 4. Recompose the README

Build a concise, scannable README in this order unless the product evidence supports a better narrative:

1. Theme-aware logo or wordmark, product name, plain-language promise, and trust boundary.
2. One dominant action row: website, direct download/start, and documentation, using accessible icons and text labels.
3. Only truthful release, build, platform, and license badges.
4. A short “choose how to run it” or platform matrix with direct, stable actions and install guides.
5. Outcome-led “what it does” content organized by user jobs, not an undifferentiated feature dump.
6. One excellent current-app screenshot or a small purposeful visual sequence with useful alt text and captions.
7. A clear workflow, privacy/trust explanation, setup, troubleshooting, and limitations.
8. Developer setup, architecture, contributing, roadmap, and license after the user-facing story.

Use HTML inside Markdown only when it materially improves GitHub rendering and remains accessible. Keep copy-paste commands exact. Prefer collapsible detail for long setup or architecture sections. Do not turn the README into a duplicate of the full docs site.

## 5. Redesign the website

Create an original narrative arc around verified user value. A strong default is:

`promise → how it works → feature proof → real demo → trust/privacy → download → updates/help`

Vary the structure when the product calls for it. Preserve existing routes and component ownership unless a separate plan authorizes structural removal.

- Put the product's job and primary download/start action above the fold.
- Anchor important claims to real screenshots, recordings, code/release evidence, or clearly labeled diagrams.
- Make navigation shallow and the next action obvious at every stage.
- Use progressive disclosure for technical detail without hiding limitations or safety notes.
- Keep release/download fallbacks useful when JavaScript or a release API fails.
- Update page titles, descriptions, Open Graph/Twitter assets, favicon/app icons, canonical links, and relevant structured metadata.
- Preserve reduced motion, keyboard navigation, semantic headings, focus visibility, contrast, screen-reader clarity, touch targets, and 200% zoom.
- Design for height as well as width. Validate at `320`, `375`, `414`, `768`, and desktop widths, including `375×812` and `1440×900`.

## 6. Make downloads effortless and honest

Use recognizable platform icons plus visible text; never use an icon as the only accessible label.

- Provide a primary download/start action in the README opening and website hero, then a complete platform section later.
- Distinguish macOS architectures, Windows architectures, Linux formats, source installs, web mode, and prerequisites exactly as shipped.
- Link directly to a stable asset only when the URL is proven stable. Otherwise link to the latest release page or resolve assets from verified release metadata with a static fallback.
- Show version, file type, architecture, signing/notarization caveats, checksum verification, and install guide close to the relevant action.
- Keep unavailable platforms visible only when an honest explanation helps; never style a roadmap platform as downloadable.
- Test every CTA, redirect, asset response, anchor, and fallback. Confirm that README and website lead to the same supported release paths.

Do not publish a release or change product distribution merely to make the download section look complete.

## 7. Refresh the visual artifacts

Capture screenshots and recordings from the verified current app with safe, realistic demo data. Exercise the state shown; do not stage impossible combinations.

- Prefer crisp, legible app views that prove one claim each.
- Capture the app's supported themes and the website's target breakpoints when useful.
- Remove secrets, personal paths, private holdings, location history, emails, tokens, and identifying notifications before capture.
- Preserve original editable sources. Use deterministic capture or conversion scripts already in the repository; add a small documented script only when repeatability materially improves maintenance.
- Validate SVG XML, `viewBox`, intrinsic dimensions, theme contrast, clipping, external references, accessibility role/title behavior, and GitHub/browser rendering.
- Optimize raster and video output without making UI text blurry. Keep aspect ratios and declared dimensions accurate to reduce layout shift.
- Update every reference, manifest, preload, poster, and metadata entry that consumes a replaced asset. Remove an obsolete asset only after proving it is unreferenced and obtaining any required deletion approval.

## 8. Verify the complete experience

Run repository-provided checks first, then add the smallest targeted checks needed:

- README/Markdown rendering, anchors, local links, images, commands, and badges;
- website formatting, types, tests, production build, link validation, and route generation;
- rendered desktop and mobile browser checks for layout, overflow, fold, theme, keyboard, reduced motion, console errors, and failed requests;
- screenshot, SVG, video, favicon, and social-preview visual inspection;
- safe local/installed app comparison for screenshot and copy fidelity;
- current live website and download/release links when network access is available;
- repository-wide stale-name, old-version, old-screenshot, and superseded-link search;
- `graphify update .` plus one scoped query when the project already has a graph;
- final `git diff --check`, diff review, and `git status` to confirm scope.

Fix failures caused by the refresh. Identify unrelated pre-existing failures with evidence. Never equate a source build with proof of the rendered or installed surface.

## 9. Run the council before any push

After implementation and verification are provisionally complete, read and follow [Council Review](../council-review/SKILL.md).

- Run exactly two rounds with four actual reviewers in each: evidence, coverage, risk, and outcome.
- Give reviewers the request, changed artifacts, relevant evidence, verification results, and proposed completion report; keep private product data and secrets out of the packet.
- Reconcile Round 1 findings, apply valid fixes, and rerun affected checks before Round 2.
- Resolve every valid Round 2 blocker. Obtain targeted acceptance for a material blocker fix as required by the council protocol.
- Do not simulate missing reviewers. If four actual reviewers are unavailable, stop before material findings, completion claims, commit, or push and ask the user whether to waive or change the reporting requirement. A waiver to report blocked or partial work is not permission to push; this skill must not push without the completed two-round, four-reviewer council gate unless the user explicitly replaces that delivery rule.
- Do not commit, push, open a pull request, merge, deploy, tag, publish, or create a release unless the user explicitly authorized that action. When push is authorized, perform it only after the council passes and then verify the resulting remote checks or surface as applicable.

## 10. Report the outcome

Lead with what is now better for a first-time user. Include:

- the verified product facts that shaped the design;
- README, website, download, and asset surfaces changed;
- screenshots or rendered pages inspected;
- validation commands and outcomes;
- council-driven corrections that materially changed the result;
- remaining uncertainty, untested platforms, or external actions not taken;
- commit, push, deployment, or release state without implying work that did not occur.

Use clickable file links. Keep the report concise and layperson-readable.

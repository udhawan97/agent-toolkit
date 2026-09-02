# Public Surface Standard

Use this reference as the rubric for a `/refresh-docs` implementation. Adapt its patterns to the actual product instead of checking boxes mechanically.

## 1. Quality bar

A successful refresh makes a first-time visitor able to answer, in order:

1. What is this?
2. Is it for me?
3. What does it help me do?
4. Can I trust it?
5. What does it really look like?
6. How do I download, install, or start it on my device?
7. Where do I go if something fails?

The README should answer those questions quickly. The website should make them memorable. The docs should handle depth.

## 2. FolioOrb-inspired content pattern

Borrow these strengths, not FolioOrb's exact copy, theme, or page structure:

- Pair a concise promise with a clear local/cloud/privacy boundary.
- Offer “run it your way” choices early, with platforms and prerequisites visible.
- Explain features as user actions and outcomes.
- Use real product imagery as proof instead of decorative mockups.
- Separate user onboarding from developer detail.
- Put trust, download verification, update behavior, and first-launch caveats near installation.
- Keep roadmap language explicitly non-binding.
- Let the product have a voice without sacrificing clarity.

Create a product-specific narrative and visual motif. A trip planner, PDF editor, portfolio tool, and developer utility should not share the same landing-page skeleton.

## 3. Evidence and coverage ledger

Maintain a compact internal table while working:

| Surface or claim | Source of truth | Status | Public destination | Verification |
| --- | --- | --- | --- | --- |
| Product promise | App flow + approved brief | Shipped | README hero + site hero | Runtime observed |
| macOS download | Release manifest | Shipped | README + download section | Link and checksum checked |
| Screenshot | Current demo build | Current | README + feature proof | Captured and visually inspected |
| Future platform | Roadmap | Planned | Roadmap only | Clearly labeled |

Use status values such as `Shipped`, `Experimental`, `Planned`, `Deprecated`, `Unavailable`, and `Unverified`. Never allow a lower-confidence source to silently override verified runtime evidence.

## 4. README composition

### Opening screenful

- Theme-aware logo/wordmark with a useful fallback and restrained size.
- Product name and one memorable, literal promise.
- One short paragraph explaining what it does, for whom, and the decisive trust boundary.
- A dominant CTA row using small repository-owned icons with adjacent text:
  - download or start;
  - website/live demo;
  - documentation.
- A small set of truthful badges. Remove decorative badge noise.

### Core story

- “Choose your path” matrix for installers, source, web, CLI, or mobile as applicable.
- Outcome table or grouped feature chapters with exact product language.
- One hero screenshot with a caption that explains what the viewer is seeing.
- Three-to-five-step workflow for the primary job.
- Honest privacy/trust/limitations block.

### Depth

- Setup and install guides, with complex paths in `<details>` blocks.
- Troubleshooting and first-launch warnings.
- Developer setup, architecture, testing, contribution, roadmap, and license.

Keep the README useful when images fail and on a narrow mobile viewport. Avoid huge centered copy blocks, walls of badges, dozens of screenshots, or a feature table so long that the product's core job disappears.

## 5. Website composition

Treat the page as a product story, not a catalog of cards.

### Promise

- Show product identity, job, audience, and primary action immediately.
- Pair the promise with the strongest real product visual or interaction.
- Use a short trust strip only for material facts such as local-first, open source, no account, or checksum support.

### Workflow

- Explain the primary journey as visible cause and effect.
- Use product-specific verbs and concrete inputs/outputs.
- Show recovery or control where trust matters.

### Proof

- Give each major claim one strong proof artifact: screenshot, recording, traceable release fact, or honest diagram.
- Caption what the visitor should notice.
- Avoid fake chrome and impossible composite screens.

### Trust

- Explain data location, network use, AI/provider behavior, updates, backups, signing, permissions, and user control only as applicable.
- Link to detailed privacy, security, architecture, or verification docs.

### Download

- Repeat the primary action with platform cards or rows that show icon, platform, architecture, format, prerequisite, and guide.
- Include release notes and checksum verification nearby.
- Provide a useful static fallback if dynamic release metadata fails.

### Help and continuation

- Link to getting started, troubleshooting, releases, source, and issue reporting.
- Keep the footer small and complete.

## 6. Visual system rubric

Score each axis from 1 to 5 before the council review. Revise any axis below 4.

| Axis | A score of 5 means |
| --- | --- |
| Product fidelity | The palette, type, density, visuals, and voice unmistakably belong to the current app. |
| Hierarchy | A layperson understands the promise, proof, trust boundary, and next action without rereading. |
| Originality | The layout and motif arise from the product rather than a reusable AI landing-page pattern. |
| Restraint | Every visual effect supports hierarchy or meaning; nothing competes with the product. |
| Proof | Important claims are demonstrated with current, traceable evidence. |
| Download clarity | A supported user reaches the correct artifact and install guidance without guessing. |
| Accessibility | Semantics, contrast, keyboard, motion, zoom, alt text, and touch behavior hold across target viewports. |
| Maintenance | Assets, release data, screenshots, and links have clear sources and repeatable update paths. |

## 7. Icon and SVG rules

- Prefer existing brand and platform icons already licensed in the repository.
- Use a single stroke/fill vocabulary and optical size across a set.
- Pair all functional icons with visible text or an accessible name.
- Keep decorative SVGs hidden from assistive technology.
- Provide `viewBox`; avoid hard-coded dimensions that clip at different ratios.
- Resolve CSS variables and theme colors in the target rendering environments, including GitHub's image handling.
- Avoid embedded scripts, remote dependencies, base64 bloat, font outlines for ordinary text, and needlessly complex paths.
- Render-inspect important SVGs; source validity alone is not visual proof.

## 8. Screenshot and demo rules

- Capture only from a verified current build or installed artifact.
- Use seeded/demo data that is realistic but not traceable to a real person.
- Choose states that explain a user outcome, not merely the dashboard's prettiest region.
- Keep UI text readable at the rendered size.
- Capture at a stable viewport and device scale; avoid inconsistent browser scaling.
- Prefer WebP/AVIF for site photography-like captures when supported; preserve PNG when crisp lossless UI detail materially benefits.
- Include accurate width/height and lazy/eager loading behavior to prevent layout shift.
- Use posters for video, controls when needed, muted autoplay only when it adds understanding, and reduced-motion fallbacks.
- Give every informative asset meaningful alt text and every decorative asset empty alt text.

## 9. Download checklist

For each shipped platform, verify:

- platform and architecture label;
- exact package type and current filename pattern;
- stable destination or release-resolution logic;
- HTTP success and expected redirect behavior;
- prerequisite and supported OS version;
- signing/notarization or first-launch warning;
- checksum/signature availability and instructions;
- install, update, and uninstall guide consistency;
- static fallback when a dynamic release request fails;
- identical support claims across README, site, docs, manifests, and release metadata.

Do not show a direct-download icon that silently leads to a release index unless the label says so.

## 10. Responsive and accessibility matrix

Exercise at least:

| Viewport or mode | What to inspect |
| --- | --- |
| 320 px wide | Long words, buttons, nav, tables, code, and horizontal overflow |
| 375×812 | Above-fold promise/CTA, sticky elements, dialogs, footer reachability |
| 414 px wide | Touch targets, platform rows, screenshots, caption wrapping |
| 768 px wide | Intermediate layout transitions and navigation behavior |
| 1440×900 | Reading width, visual balance, screenshot detail, empty space |
| 200% zoom | Reflow, clipped controls, sticky collisions, readable ordering |
| Reduced motion | No required information lost; no forced ambient motion |
| Keyboard only | Logical focus order, visible focus, usable menus and CTAs |
| Light/dark | Contrast, logo variant, screenshots, icons, and theme persistence |

Check viewport height, not width alone. Confirm there is no horizontal scroll and no primary CTA or dismiss control is hidden behind a fixed element.

## 11. Closure search

Before council review, search for:

- old product names, slogans, versions, platform lists, and feature labels;
- stale screenshots, diagrams, and social cards;
- replaced asset filenames and paths;
- broken relative links, fragments, case mismatches, and generated-source drift;
- generic placeholder copy, invented metrics, `TODO`, `TBD`, and temporary notes;
- inaccessible icon-only links, missing alt text, empty headings, and duplicate IDs;
- downloads that disagree with release manifests or installer names;
- untracked browser artifacts, capture output, logs, and accidental private data.

Finish only when every in-scope item is current, intentionally retained, or explicitly reported as blocked.

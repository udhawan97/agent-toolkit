# Dev Review HTML Report

Create one private, visual, self-contained HTML report for each run. The report should feel like a sharp senior friend reviewing a production candidate: specific, calm, occasionally funny, and never glib about high-stakes failures.

## Integrity and privacy

- Create a fresh task-specific directory named `dev-review-<timestamp>-<run-id>` under the current user’s OS temporary directory. Use mode `0700` for the directory and `0600` for `report.html` from the first byte on POSIX; on Windows, keep it inside the current-user temp/state location and verify it is not writable by broad groups when the host exposes an ACL check.
- Make **zero external requests**. Use inline CSS, accessible inline SVG, and raster screenshot `data:` URIs only. No CDN, remote font/image, analytics, iframe, form, or script.
- Put a restrictive Content Security Policy in `<head>`: `default-src 'none'; script-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:; connect-src 'none'; media-src data:; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'`.
- Encode repository/runtime content for its exact HTML context. Never place untrusted content in `<style>`, raw SVG markup, event handlers, URLs, selectors, or metadata directives.
- Allow generated links only to same-document `#fragment` anchors. Render external URLs and absolute paths as text.
- Redact tokens, account identifiers, personal data, private content, internal hostnames, and unrelated applications before evidence enters the report or reviewer packets.
- Show real screenshots in plain evidence frames. Do not add fake browser, phone, IDE, or code-window chrome.
- Keep every diagram understandable through adjacent text and every image useful through `alt` text and a factual caption.

## Required structure

### 1. Header and verdict

Show confirmed repository/product, revision/build, date, mode, scope, runtime, fixture type, tested platforms/viewports/themes/inputs, and report run ID.

Prominently show:

- overall score as `x.x / 10`;
- coverage confidence: `High`, `Medium`, or `Low` with one-line rationale;
- production verdict: `Ready`, `Ready with follow-ups`, `Hold`, or `Blocked`;
- count by severity and evidence grade;
- a concise “senior read” that names the strongest quality and largest concern.

The score is not certification. A high score with low coverage confidence must look visibly provisional.

### 2. What works / preserve

List evidence-backed strengths: product identity, successful journeys, deep modules, clear interfaces, resilient state, strong tests, accessibility wins, security controls, or operational safeguards. State why each matters and what later work must not flatten.

### 3. Coverage charter and production map

Include:

- selected user journeys with success, cancel, retry, recovery, and re-entry branches;
- a system map from user step through runtime, state, interfaces, persistence, external adapters, and delivery/observability where applicable;
- architecture hot spots and recent-change rationale;
- coverage matrix with `Pass`, `Gap`, `Blocked`, `N/A`, or `Not tested`;
- exact sampling rule and explicit omissions.

Use inline SVG or hand-built HTML/CSS. Keep diagrams editorial and readable rather than decorative.

### 4. Scorecard

Score each applicable lens from 0 to 10 using evidence anchors:

- `0–2`: broken or unsafe in the tested scope;
- `3–4`: major repeated failures or missing fundamentals;
- `5–6`: functional but material gaps remain;
- `7–8`: strong with bounded improvements;
- `9`: excellent and broadly verified in scope;
- `10`: exceptional, with all applicable high-risk paths in scope verified and no material finding.

Default weights, renormalized across applicable lenses:

| Lens | Weight |
| --- | ---: |
| User journeys and design craft | 15% |
| Architecture and maintainability | 15% |
| Correctness and data integrity | 15% |
| Tests and verification | 10% |
| Security and privacy | 10% |
| Reliability and recovery | 10% |
| Accessibility and input | 10% |
| Performance and resource use | 5% |
| Operability and observability | 5% |
| Delivery, dependencies, and docs | 5% |

Show the arithmetic and one evidence sentence per lens. Score only the tested portion of a partially covered lens and label the remainder; `N/A` removes a weight, while `Not tested` does not become a fake zero or pass but lowers coverage confidence. Apply visible headline caps: unresolved `P0 Blocker` caps the overall score at `3.9` and requires verdict `Blocked`; unresolved production-relevant `P1 Major` caps it at `6.4` and normally requires `Hold` unless evidence establishes it is outside the selected release path. Explain any cap next to the score.

Coverage confidence guidance:

- `High` — real surface and source traced across applicable high-risk paths with meaningful failure/recovery coverage.
- `Medium` — primary paths verified but some platforms, states, or production mechanisms remain source-only or blocked.
- `Low` — mostly static review, missing runnable surface, stale evidence, or major applicable areas untested.

A static-only review cannot receive `Ready` or `Ready with follow-ups`; its maximum verdict is `Hold`.

### 5. Friendly roast

Use one compact section, not stand-up comedy. Good examples:

- “The happy path is tidy; the retry path has been living unsupervised.”
- “This module is doing three jobs and asking the tests to keep the secret.”
- “Load-bearing weirdness, but documented and earning rent.”

Never joke about P0/P1 safety, security, privacy, accessibility, data loss, money, health, destructive behavior, or people. When the situation is serious, switch to plain language immediately.

### 6. Finding cards

Each card uses a stable ID and contains:

1. user/production outcome title;
2. severity, outcome evidence, causal confidence, recommendation strength, classification, effort, and status badges;
3. exact scope, runtime/state, and relevant files;
4. deterministic reproduction or source trace;
5. observed versus expected behavior;
6. evidence frame and caption where available;
7. root cause or explicitly labeled hypothesis;
8. architecture explanation using module/interface/seam/depth/leverage/locality when applicable;
9. design context, mismatch, and preserve constraint when applicable;
10. bounded fix direction—not `After` before implementation; every material architecture finding includes an accessible before/direction diagram;
11. acceptance checks, non-regression checks, rollback trigger, and stop condition;
12. user impact, production risk, and consequence of deferral;
13. owner/peer and resolution evidence after implementation.

Do not inflate one shared cause into many screen-level findings. Do not show a direction as a completed fix.

### 7. Decision board

Separate:

- `Fix candidates` — high-confidence, bounded, selectable now;
- `Research next` — concern plus missing proof and exact next experiment;
- `Preserve / justified` — apparent complexity or convention that should remain;
- `Deferred` — out of scope, low-impact, speculative, or authority-blocked.

Order fix candidates by user/production impact, evidence strength, reach, risk, and then effort. Do not use low effort to outrank a major recovery or correctness gap.

### 8. Implementation and production gate

After authorized work, preserve before evidence and add same-condition after evidence. Show changed files, focused tests, worker/senior/peer receipts, neighboring flows checked, full verification commands/results, remaining limitations, score change, confidence change, and final verdict.

Do not call the report `Ready` or `Merge-ready` when a required check failed, a graph known to exist is stale, the real affected surface was not replayed, or the candidate tree differs from what reviewers inspected.

### 9. Not tested / blocked

List unavailable credentials, devices, fixtures, platforms, browsers, permissions, data, external systems, production access, unsafe actions, build blockers, and time-bounded branches. State what evidence or authority would be needed. Keep `N/A`, `Not tested`, and `Blocked` distinct.

### 10. Continuity handoff

Show prior run ID when resumed, unresolved stable IDs, stale evidence, research experiments, decisions, preservation constraints, and the exact next-session starting point. Do not imply that an old finding remains current without revalidation.

## Visual direction

- Derive one restrained accent from the product when a rendered product exists; otherwise use a neutral indigo/ink palette.
- Use strong hierarchy, generous spacing, visible evidence labels, readable code/path wrapping, and varied containment based on meaning.
- Use before/direction architecture diagrams that expose leakage and proposed depth; use before/after only after verification.
- Avoid glassmorphism, excessive gradients, decorative dashboards, fake metrics, and microscopic screenshots.
- Make the report useful at 320 CSS pixels and in print. Tables may scroll locally inside a labeled region; the page itself must not overflow.

## Verification

Before delivery:

1. load with network access blocked and confirm zero requests;
2. check console/CSP and broken resources;
3. inspect at 320, 375, 414, and 768 CSS pixels plus desktop width;
4. keyboard-check fragment links and visible focus;
5. verify every score has evidence, every finding has confidence, and every recommendation links to a finding;
6. verify high-stakes findings use serious language;
7. scan for secrets, private content, unsafe URLs, scripts, event handlers, forms, frames, external resources, and unintended absolute paths;
8. restrict the final file to mode `0600`, record its digest, keep it private through the exact-artifact council gate, persist the matching `reportCouncilApproval`, and only then tell the user the absolute path.

Remove unredacted captures as soon as redacted evidence is sufficient. At closure, remove only the exact run-owned scratch files that are no longer needed; never recursively clean a broad temporary, repository, or user directory. Preserve the final report while its ledger references it unless the user asks to remove it.

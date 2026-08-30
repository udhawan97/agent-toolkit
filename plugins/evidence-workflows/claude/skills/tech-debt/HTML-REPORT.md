# Tech Debt Flow Review — HTML Report

Create one visual, private, offline HTML report inside a newly created task-specific directory beneath the OS temp root. Do not change permissions on the shared temp root. The report should make the causal chain readable at a glance:

`user journey -> visible friction -> stack mechanism -> bounded improvement -> acceptance proof`

## Integrity contract

- Make zero external requests. No CDN, remote font, remote image, iframe, analytics, or network-fetched script.
- Use inline CSS and inline SVG. Keep the report script-free and understandable with JavaScript disabled.
- Create the containing temporary directory with owner-only permissions (`0700` on POSIX) and create the report file with owner-only permissions (`0600`) before writing its first byte. Do not write privately scoped evidence to a permissive file and tighten it afterward.
- Put a strict CSP meta element first in `<head>`, such as:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
/>
```

- Embed redacted screenshots only as raster `data:` URIs. Render captured URLs, logs, product copy, and file paths as context-encoded text, never as executable markup or CSS.
- Keep active links limited to same-document `#fragment` anchors. Render external URLs and local file paths as inert, context-encoded text.
- Use semantic HTML and text equivalents for every diagram.
- Restrict the report to its owner (`0600` on POSIX where supported).
- Delete raw captures after their redacted evidence is embedded and the report is verified. Retain only the final report for handoff, state that retention rule in the report, and remove superseded reports created during the task. Track each generated path when it is created and clean up only those exact paths—never a wildcard, the shared temp root, or another broad directory.
- Keep it usable at 320 CSS pixels and printable.

## Visual direction

Use restrained editorial evidence chrome: neutral surfaces, one product-derived accent, red only for verified breaks, amber for source-proven concerns, and a dashed treatment for untested risks. Avoid vanity scores, generic gradients, and identical cards for every section.

The report is not a replacement product design. Preserve the product's visual identity in evidence and direction sketches without inventing copy, metrics, logos, or features.

## Required structure

### 1. Header and legend

Show only confirmed metadata:

- product and audited surface;
- repository, commit/build/app version, date, runtime, and fixture;
- selected journeys and risk-based charter;
- platform/browser/OS, layouts/windows, themes, inputs, and network/device conditions tested;
- counts by severity, outcome evidence, and cause confidence;
- legends for severity, outcome evidence, cause confidence, recommendation strength, flow status, and stack-diagram notation.

Do not produce a single debt or UX score.

### 2. What works / Preserve

Name stack choices, deep modules, stable interfaces, accessibility behavior, recovery paths, and product-specific strengths that should not regress. Cite runtime or source evidence.

### 3. Journey map

Show entry, action, feedback, completion, return, cancel, and recovery branches. Use semantic ordered lists, CSS connectors, or accessible inline SVG. Mark pass, verified gap, source-proven concern, and untested branch distinctly.

### 4. Flow-to-stack cross-section

For each selected flow, draw only participating roles:

```text
User step
  -> visible UI/runtime state
  -> navigation and state module
  -> network interface and adapter
  -> persistence/backend module
  -> delivery/observability
```

Match the mechanism treatment to cause confidence: use a solid highlight only for a `Confirmed cause`, a lighter treatment for a `Supported cause`, and a dashed callout for a `Cause hypothesis`. Leave the mechanism unhighlighted when no cause clears the evidence bar. Show other steps only as proven or explicitly labeled reach, and include a concise text description.

### 5. Coverage matrix

Rows are journeys or material states. Columns cover tested platform/layout, input, success, recovery, return, and relevant measurements. Each cell is `Pass`, `Gap`, `Blocked`, `N/A`, or `Not tested`. State the sampling rule above the table.

### 6. Candidate cards

Each candidate is one article with a stable evidence ID and:

1. **Title** — user-visible outcome, not an implementation smell.
2. **Badges** — severity, outcome evidence, cause confidence, recommendation strength, effort, flow, platform/condition, and status after implementation.
3. **User outcome** — exact step and consequence.
4. **Reproduction** — 2–5 deterministic steps or the precise source-only condition.
5. **Observed / expected** — concise and falsifiable.
6. **Evidence** — screenshot/trace/log where relevant plus `file:line`, manifest, config, or official support evidence.
7. **Stack mechanism** — the smallest module, interface, dependency, runtime, or delivery cause.
8. **Causal bridge** — why this mechanism creates the outcome, what isolates or merely supports it, and which other flows share its reach.
9. **Before / Direction diagram** — side-by-side at wide widths and stacked on narrow screens. Use a flow-stack cross-section, call-graph collapse, sequence, or interface-mass diagram. Reserve `After` for same-condition evidence captured after implementation.
10. **Bounded improvement** — the narrowest option and why broader migration is unnecessary or justified.
11. **User benefit and architecture benefit** — separate user outcome from locality, leverage, depth, and testability.
12. **Intervention contract** — baseline, target provenance, non-regression budget, migration slice, rollback trigger, stop condition, and temporary-debt removal criteria.
13. **Preserve / migration / rollback** — load-bearing behavior, compatibility risk, reversibility, and stop conditions.
14. **Acceptance check** — same-condition behavior that proves improvement.
15. **Files** — relevant paths in monospace.

For an `Untested risk` or `Cause hypothesis`, omit fake screenshot proof and show exactly what test would promote or dismiss it. A verified symptom must not visually imply a confirmed stack cause.

### 7. Recommendation stack

List at most five items. Each includes the candidate anchor, why it comes first, affected flows, outcome evidence, cause confidence, effort, migration risk, and required validation. Order by user impact, reach evidence, outcome evidence, cause confidence, leverage, reversibility, then effort. State when frequency is unknown.

Finish with one top recommendation and a one-sentence reason. Do not propose a module interface until the user selects that item.

If no item clears the evidence bar, replace the recommendation stack with **No material debt established** and list the tested coverage plus the smallest remaining evidence checks. Do not fill a quota.

### 8. Looks like debt, but is justified

Record inspected choices that remain load-bearing, with the deletion test or contract evidence that cleared them. This section prevents modernization-by-fashion and gives future reviewers preserve constraints.

### 9. Not tested / blocked

List missing credentials/fixtures, unsupported platforms, external side effects, unavailable field data, blocked builds, time-bounded branches, and unverified support claims. Explain what evidence would close each gap.

## Diagram patterns

- **Flow-stack cross-section** — horizontal journey steps with vertical stack roles; highlight one shared mechanism.
- **Call-graph collapse** — before shows scattered calls; direction shows one deep module with internal details faded.
- **Interface mass** — before shows a wide interface and thin implementation; direction shows a small interface and deeper implementation.
- **Sequence** — before shows extra round trips or ambiguous feedback; direction shows fewer transitions with explicit progress/recovery.
- **Adapter swap** — show a stable interface with current and proposed adapters only when two real implementations justify the seam.

Use inline SVG or positioned HTML boxes. Keep text labels readable and provide a text equivalent. Diagrams carry structure; prose carries evidence and uncertainty.

## After implementation

Keep original evidence. Add:

- `Resolved`, `Partially resolved`, or `Remaining`;
- same-condition after evidence;
- exact acceptance result and focused regression tests;
- neighboring flows rechecked;
- intervention-contract result, migration/rollback outcome, temporary machinery removed or still required, and remaining limitations.

## Report verification

Before handoff:

1. Load with network access blocked and confirm zero requests.
2. Check the console for CSP, script, and broken-resource errors.
3. Inspect at 320, 375, 414, 768, and desktop CSS widths. Confirm no page-level overflow, clipped evidence, unreadable diagrams, accidental control wrapping, or long-content overlap.
4. Keyboard-test same-document links and any CSS-only controls; focus must be visible. Confirm no external URL or local file path is an active link.
5. Confirm every recommendation links to one candidate and every candidate has a journey step, stack mechanism, causal bridge, separate outcome/cause labels, intervention contract, and acceptance check.
6. Search for invented metrics, unsupported support/version claims, placeholders presented as proof, secrets, personal data, private content, and unnecessary absolute paths.
7. Confirm `Looks like debt, but is justified` and `Not tested / blocked` are present even when they contain only a truthful `Nothing material` statement.

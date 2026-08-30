# User Flow Design Review — HTML Report Format

Generate one visual, offline, self-contained HTML report in the OS temp directory. The report is an evidence surface, not a dashboard of vanity scores.

## Integrity contract

- Make **zero external requests**. Use no CDN, remote font, analytics, remote image, iframe, or network-fetched script.
- Embed screenshots as `data:image/...;base64,...`; inline all CSS and use a script-free report theme toggle.
- Use semantic HTML and inline SVG for journey maps, annotations, focus order, and wireframes. Include text equivalents for every visual relationship.
- Encode product copy, URLs, logs, file paths, and captured DOM text for the exact context where each value is inserted. Keep captured values out of `<script>`, `<style>`, inline event handlers, raw SVG markup, and CSS selectors.
- Render captured URLs and file paths as text. Generated links may use fragment-only `#...` targets; add other schemes only through a documented allowlist. Accept screenshot data URIs only for raster MIME types such as PNG, JPEG, or WebP.
- Redact tokens, personal data, private filenames/document contents, account identifiers, and unrelated applications before embedding captures.
- Use only real product content in evidence and direction wireframes. Mark unknown copy, metrics, testimonials, logos, and claims as unknown or pending; never invent proof to make a direction look complete.
- Present screenshots in plain, labeled evidence frames. Do not redraw browser traffic lights, URL bars, phone notches, IDE chrome, or code-window title bars.
- Keep the report understandable with JavaScript disabled and usable at 320 CSS pixels.

## Visual direction

- Derive one restrained accent from the audited product while preserving neutral evidence colors.
- Keep the report visually related to the product without impersonating it. The report is evidence chrome, not a redesign proposal or a competing brand system.
- Use deliberate whitespace, readable typography, strong hierarchy, and labeled evidence frames. Vary containment by meaning instead of putting every section inside an identical card.
- Avoid generic glass cards, excessive gradients, vanity scores, and unsupported claims.
- Use compact tables only when they remain readable; wrap them in a labeled horizontal-scroll region on narrow screens.
- Include a compact **Design context** summary and a **What works / Preserve** section before the gaps. Name real strengths and accessibility wins so later fixes do not flatten them.

## Offline scaffold

Adapt this scaffold to the product, but keep the content-security policy and `script-src 'none'`. Use semantic HTML/CSS or a clear noninteractive equivalent for any behavior that would otherwise require JavaScript.

```html
<!doctype html>
<html lang="en" data-theme="light">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'none'; font-src data:; connect-src 'none'; media-src data:; object-src 'none'; base-uri 'none'; form-action 'none'"
    />
    <title>User flow design review — {{product}}</title>
    <style>
      :root {
        color-scheme: light;
        --paper: #f7f5f0;
        --ink: #172033;
        --muted: #667085;
        --line: #d9d6cf;
        --surface: #ffffff;
        --accent: #315c4c;
        --danger: #b42318;
        --warning: #b54708;
        --success: #287253;
      }
      body:has(#report-theme-toggle:checked) {
        color-scheme: dark;
        --paper: #101513;
        --ink: #f3f5f4;
        --muted: #a6b0ab;
        --line: #34413b;
        --surface: #18201c;
        --accent: #8fc5ae;
        --danger: #fda29b;
        --warning: #fec84b;
        --success: #75d6ae;
      }
      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; overflow-x: clip; }
      body {
        margin: 0;
        overflow-x: clip;
        background: var(--paper);
        color: var(--ink);
        font: 16px/1.55 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      main { width: min(72rem, 100%); margin: 0 auto; padding: 2.5rem 1rem 5rem; }
      h1, h2, h3 { min-width: 0; line-height: 1.15; overflow-wrap: anywhere; text-wrap: balance; }
      p, li, dd, figcaption { overflow-wrap: anywhere; }
      a { color: var(--accent); }
      button { font: inherit; }
      .theme-toggle { display: inline-flex; align-items: center; gap: .5rem; cursor: pointer; white-space: nowrap; }
      .theme-toggle input { inline-size: 1.1rem; block-size: 1.1rem; }
      :focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
      .surface { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; }
      .section { margin-block: 3rem; }
      .stack { display: grid; gap: 1rem; }
      .split { display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .split > * { min-width: 0; }
      .gap-card { padding: clamp(1rem, 3vw, 2rem); }
      .badges { display: flex; flex-wrap: wrap; gap: .5rem; }
      .badge { border: 1px solid var(--line); border-radius: 999px; padding: .25rem .65rem; }
      .muted { color: var(--muted); }
      .evidence-frame { overflow: hidden; }
      .evidence-frame img { display: block; width: 100%; height: auto; }
      figure { min-width: 0; margin: 0; }
      .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: .75rem; }
      table { width: 100%; border-collapse: collapse; min-width: 42rem; }
      th, td { padding: .7rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
      pre { white-space: pre-wrap; overflow-wrap: anywhere; }
      @media (max-width: 44rem) { .split { grid-template-columns: 1fr; } }
      @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
      @media print { .theme-toggle { display: none; } .surface { break-inside: avoid; } }
    </style>
  </head>
  <body>
    <main>
      <header id="summary">
        <label class="theme-toggle" for="report-theme-toggle">
          <input id="report-theme-toggle" type="checkbox" />
          Use dark report theme
        </label>
        ...
      </header>
      <section id="strengths" class="section">...</section>
      <section id="journeys" class="section">...</section>
      <section id="coverage" class="section">...</section>
      <section id="gaps" class="section">...</section>
      <section id="recommendations" class="section">...</section>
      <section id="untested" class="section">...</section>
    </main>
  </body>
</html>
```

The CSS-only report theme toggle is report chrome, not evidence about the audited application's theme. If `:has()` is unsupported, the report remains usable in its default light theme.

## Header

Show only confirmed metadata:

- product and audited surface;
- repository/build/commit/app version when known;
- audit date, runtime, fixture/account type, browser or OS, and relevant hardware/emulation;
- flow scope and risk-based test charter;
- design context: evidence-backed audience, primary job, established product language, constraints, and unknowns;
- flows, viewports/windows, themes, and input methods actually tested;
- counts of gaps by severity and confidence;
- severity/confidence legend and accessible report-theme toggle.

Do not show a single “UX score.” It hides uneven coverage.

## What works / Preserve

List the product-specific choices and accessibility wins that the audit found effective. Each item names the rendered state or source evidence and explains why it supports the audience, task, product identity, or platform convention. Do not force a quota; include only defensible strengths. These become explicit non-regression constraints for any later implementation.

## Journey map

Use semantic ordered lists, CSS connectors, or accessible inline SVG. Every node is one user-visible step. Mark:

- pass in muted green;
- verified gap in red;
- source-proven concern in amber;
- untested branch with a dashed outline.

Show return, cancel, retry, and recovery paths when they exist. Include a concise text description of branches so the map remains understandable to screen readers and when SVG styling is unavailable. A left-to-right happy path alone is not a user-flow review.

## Coverage matrix

Render a compact table with rows for flows and columns for tested combinations. Each cell is `Pass`, `Gap`, `Blocked`, `N/A`, or `Not tested`.

Minimum dimensions when applicable:

- flow step and meaningful state;
- viewport/window size;
- light/dark/system theme;
- mouse/keyboard/touch input;
- success/recovery/return behavior.

State the sampling rule above the matrix. Do not imply that one tested combination covers all themes, viewports, inputs, or branches.

## Gap card

Each gap is one `<article>` with a stable evidence ID and:

1. **Title** — user-visible failure, not an implementation label.
2. **Badges** — severity, confidence, flow, viewport/window, theme, and status after implementation.
3. **Reproduction** — 2–5 deterministic steps, including fixture or precondition.
4. **Observed / Expected** — one concise sentence each.
5. **Evidence** — actual screenshot in a plain frame labeled with the real runtime, viewport/window, theme, and input; annotate the exact failure with CSS or inline SVG. Add console/network evidence only when it explains the behavior.
6. **Product/task fit** — for design-craft findings, state the concrete mismatch and user consequence. A named anti-pattern may appear as a lead, but “looks AI-generated” is not sufficient impact.
7. **Preserve** — established product character, useful convention, or accessibility behavior that the direction must keep.
8. **Proposed improvement** — an accessible hand-built direction wireframe or state-flow adjustment when a visual change is proposed. Use real content and label it `Direction`, never `After` before implementation. If materially different directions would change product identity, show concise alternatives and mark `Choice required`.
9. **Root cause** — smallest confirmed shared behavior; label an unconfirmed explanation `Hypothesis`.
10. **Files** — relevant source paths in monospace.
11. **Acceptance check** — observable same-condition behavior that will prove the gap resolved.
12. **Flow impact** — blocked, slowed, confusing, risky, cosmetic, or product-identity opportunity.

Use side-by-side evidence/direction at wide widths and stack at narrow widths. Never shrink phone screenshots until annotations are illegible. Give every image useful `alt` text and a `<figcaption>` that states what the capture proves. Do not add decorative browser or device chrome around the image.

## Severity and confidence

Severity:

- `P0 Blocker` — a core flow cannot complete, the user is trapped, or data/work is lost.
- `P1 Major` — a serious navigation, recovery, guidance, responsive, theme, or interaction failure.
- `P2 Polish` — repeated friction, inconsistency, readability issue, or weak feedback that does not block completion.
- `P3 Opportunity` — an observed enhancement with a clear user benefit, not a proven defect.

Confidence:

- `Verified` — reproduced on the real surface with evidence.
- `Source-proven` — deterministic from current source/config but not exercised at runtime.
- `Untested risk` — plausible and worth checking; never phrase it as a defect.

## Recommendation stack

End with at most five ordered recommendations. Each includes:

- gap title and anchor;
- why it comes first in one sentence;
- affected flows;
- effort: `Small`, `Medium`, or `Large`;
- validation required after implementation.

Order by user impact, frequency evidence, confidence, and then effort. If frequency is unknown, say so. A low-effort cosmetic fix does not outrank a verified recovery failure.

## Not tested / blocked

List every material omission: unavailable credentials, missing fixture, unsupported device, blocked build, external side effect, absent theme, inaccessible native surface, or time-bounded branch. Explain what would be needed to test it. Keep `N/A`, `Not tested`, and `Blocked` distinct.

## After implementation

When authorized gaps are fixed, update their cards with:

- status: `Resolved`, `Partially resolved`, or `Remaining`;
- after screenshot from the same flow, fixture, viewport/window, theme, and input condition;
- exact verification result and relevant regression test;
- neighboring flows rechecked;
- any remaining limitation.

Keep the original before evidence. Same-condition comparison is the proof.

## Report verification

Before handing off the report:

1. Load it with network access blocked and confirm it makes no requests.
2. Check the browser console for CSP, script, and broken-resource errors.
3. Inspect at 320, 375, 414, and 768 CSS pixels plus desktop width. Confirm no page-level horizontal scroll, clipped evidence, unreadable annotations, accidental two-line controls, or long-content overlap. An intentional table or code region may scroll locally when labeled.
4. Keyboard-test navigation, disclosure controls, links, and the theme toggle; confirm focus is immediate and visible.
5. Confirm every recommendation links to a gap, every gap has an evidence grade, every design gap states product/task fit and preserve constraints, and every untested claim is labeled.
6. Confirm the report contains no invented metrics, testimonials, logos, product claims, or placeholder proof presented as fact.
7. Search the final HTML for unredacted tokens, personal data, private file contents, and absolute paths that are not necessary evidence.

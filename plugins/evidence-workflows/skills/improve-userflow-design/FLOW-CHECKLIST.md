# User Flow and UI Quality Checklist

Use this as a coverage map, not a ritual or a claim of exhaustive certification. Apply the checks that match the product and record what was skipped.

## How to apply the checklist

- Baseline every selected flow: orientation, primary completion, cancel/back/out, return/re-entry, one plausible recovery, and narrow plus normal layout.
- Deep-test flows that are critical, destructive, sensitive, recently changed, or dependent on widely shared controls.
- Sample combinations by risk or pairwise coverage. Do not multiply every state, viewport, theme, input, and locale unless the product risk justifies it.
- Mark an inapplicable check `N/A`; mark an applicable but unexercised check `Not tested`. Explain material blockers.
- Use disposable data for side-effecting paths and redact sensitive evidence before it enters screenshots or reports.
- Read [DESIGN-QUALITY.md](DESIGN-QUALITY.md) before assigning visual, copy, motion, or product-identity findings. Record the product context and an initial rendered impression before using named anti-patterns or detectors.
- Record specific strengths and accessibility wins to preserve; an audit should make clear what must not be flattened by a fix.

## 1. Flow orientation and guidance

For every primary flow:

- Entry makes the page or step's purpose clear.
- One primary action is visually and semantically clear.
- Labels explain actions before the user commits.
- Progress, current location, and completion are visible when the flow spans steps.
- Browser back, in-app back, close, cancel, and Escape behave consistently with platform conventions.
- Returning to the flow preserves useful form, selection, scroll, and task state unless reset is explicit.
- Back navigation restores prior scroll position and list context instead of returning the user to the top.
- Session expiry or forced re-authentication mid-task preserves in-progress work and returns the user to where they left off.
- Success feedback says what changed and exposes the next useful action.
- Error feedback says what happened, what remains safe, and how to recover.
- Disabled controls explain the prerequisite when it is not obvious.
- Destructive actions distinguish cancel from confirm and avoid ambiguous button labels.
- Deep links, reloads, and reopened windows restore or safely reject unsupported state.
- Rapid repeat actions do not double-submit, duplicate records, or strand progress.
- Refresh, duplicate tabs/windows, and interrupted transitions do not expose a stale or unauthorized state.
- No modal, drawer, wizard, empty state, or error page is a dead end.

## 2. Required state coverage

Exercise applicable states with realistic data:

- first run and returning run;
- empty, one item, several items, and a long list;
- short copy, long copy, long unbroken tokens, and roughly 30% text expansion;
- loading, delayed response, partial content, and background refresh;
- validation errors at the field and form level;
- server/network error, retry, offline, and reconnection;
- permission request, denial, later enablement, and revoked permission;
- unsaved changes, cancel, discard, undo, and confirmation;
- expired session, re-authentication, and return to the interrupted task;
- the same account in a second tab, window, or device, including sign-out in one of them;
- stale data, simultaneous action, repeated click/tap, and interrupted navigation;
- media success, slow media, missing media, corrupt media, and fallback content.

## 3. Forms and data entry

When flows collect input:

- Input types and `inputmode` produce the right mobile keyboard (email, number, tel, date, search).
- Autofill and password managers work; `autocomplete` hints are correct and autofill does not corrupt adjacent fields.
- Paste works wherever it is useful, including one-time codes and values formatted with spaces or dashes.
- Masking and auto-formatting never fight the caret, delete typed input, or reject the value they themselves produced.
- Validation does not flag a field while the user is still completing a first attempt, and errors clear once fixed.
- Failed submission moves focus and scroll to the first error and announces a summary.
- Enter/Go submits where users expect and never submits a half-finished multi-step form.
- Required and optional fields are marked consistently; character limits are visible before they silently truncate.
- Password fields offer a visibility toggle where policy allows.
- Long forms survive navigation, refresh, and session expiry via draft, restore, or an explicit warning.
- IME composition and dictation input do not trigger premature validation or submission.

## 4. Shared components and design-system primitives

Inventory the shared controls actually used by the selected flows: buttons, links, fields, selects, checkboxes, tabs, menus, navigation, dialogs, sheets, toasts, tooltips, cards, tables, media frames, and status indicators.

- Exercise default, hover, focus, pressed, selected, disabled, loading, success, warning, error, and destructive states when supported.
- Test text-only, icon-only, icon-plus-label, short-label, long-label, and localized/expanded-label variants.
- Verify component variants share predictable sizing, typography, focus, spacing, and interaction rules.
- Confirm disabled/loading controls cannot accidentally submit and communicate why interaction is unavailable.
- Confirm fields associate labels, help text, validation, required state, and errors without layout movement that hides the field.
- Confirm menus, tabs, dialogs, and tooltips implement expected keyboard and dismissal behavior.
- Check every relevant component in light and dark themes and at narrow/wide container sizes.
- Use Storybook, previews, or a component harness when present, but reproduce the component inside a real flow before assigning user impact.
- When one shared primitive causes several screen-level symptoms, report one root-cause gap and list all affected flows rather than inflating the issue count.

## 5. Search, filters, and collections

For lists, tables, feeds, and search surfaces:

- Zero-item and zero-result states are distinct; no-results offers recovery (clear filters, fix spelling, broaden scope).
- Active filters are visible, individually removable, and clearable at once; deep links restore them when the product supports shareable state.
- Sort column and direction are visible; sorting is stable and does not scroll the user away from their row.
- Typing in search does not flash "no results" mid-query; slow queries show progress and the query survives back navigation.
- Pagination and infinite scroll preserve position and selection on back/return; loading more never duplicates or reorders existing rows.
- Bulk selection states its real scope (this page vs all matches) before destructive or bulk actions run.
- Wide tables expose a visible horizontal-scroll affordance; truncation is intentional with a discoverable full value.

## 6. Responsive layout and scaling

Use project-defined breakpoints first. When none exist, cover representative widths such as 320, 375, 414, 768, 1024, and 1440 CSS pixels. For desktop apps, include documented minimum, normal, and maximized windows.

Check:

- No document-level horizontal scroll unless the product explicitly needs it.
- No text, button, badge, tooltip, menu, or validation message overlaps another element.
- Text does not bleed through cards, dialogs, sticky regions, images, or neighboring columns.
- Content is not clipped by fixed headers, bottom bars, safe areas, notches, or virtual keyboards.
- Full-height layouts track the visual viewport (dynamic viewport units, keyboard-aware) instead of a fixed `100vh` that hides content behind mobile browser chrome.
- Dialogs, popovers, dropdowns, and toasts remain inside the usable viewport and can be dismissed.
- Sticky elements do not cover headings, anchors, focused fields, or final actions.
- Grid and flex children can shrink; long tokens wrap or truncate intentionally with a discoverable full value.
- Headings, translated copy, identifiers, chips, badges, validation text, and primary action labels reflow without clipped glyphs or accidental overlap.
- Buttons, top-level navigation, tabs, breadcrumbs, and compact action labels remain scannable; awkward two-line affordances trigger a copy or composition fix rather than silent clipping.
- Images, video, canvas, SVG, and charts respect their containers at every breakpoint.
- Portrait/landscape changes and desktop resizing do not lose controls or task state.
- Browser zoom/text scaling up to 200% remains usable; record any platform exception instead of silently skipping it.
- Pointer targets remain distinct; touch targets are comfortably operable under the project's platform standard.
- Mobile composition is intentionally reordered rather than merely shrinking desktop UI.
- Layout does not shift when scrollbars appear, on both overlay- and classic-scrollbar platforms.
- Layout-critical screens are spot-checked in a second browser engine when the product targets the open web; record which engines were tested.
- Root-level overflow suppression does not hide a broken child layout; confirm the content itself fits or has an intentional, labeled local scroll region.

Useful web probes, followed by visual confirmation:

```js
// Unexpected page-wide overflow lead
document.documentElement.scrollWidth > window.innerWidth + 1;

// Broken raster/image resource lead
[...document.images]
  .filter((image) => image.complete && image.naturalWidth === 0)
  .map((image) => ({ src: image.currentSrc || image.src, alt: image.alt }));

// Elements whose content exceeds their own box; many are intentionally scrollable
[...document.querySelectorAll("body *")]
  .filter((element) => element.scrollWidth > element.clientWidth + 1)
  .map((element) => ({
    tag: element.tagName,
    class: element.className,
    overflowX: getComputedStyle(element).overflowX,
  }));
```

## 7. Theme and dark mode

When themes are supported, test light, dark, and system behavior:

- Toggle is findable, labeled, keyboard-operable, and reflects the active state.
- Theme persists across route changes, reload, relaunch, and new windows as intended.
- System theme changes are respected when `System` is selected.
- Initial paint does not flash the wrong theme before hydration.
- Text, muted text, links, focus rings, dividers, shadows, overlays, and disabled states remain legible.
- Native controls, browser autofill, charts, code blocks, maps, syntax highlighting, and third-party widgets match the theme.
- Logos, illustrations, transparent PNGs, SVG strokes, icons, and image treatments remain visible without halos or unintended inversion.
- Hover, pressed, selected, validation, success, warning, and destructive states remain distinguishable without relying on color alone.
- Forced-colors / high-contrast mode keeps borders, focus, selection, and state changes visible when the product claims accessibility support.

Do not claim formal contrast compliance unless it was measured against the named standard and state.

## 8. Images, icons, charts, and media

- Every meaningful image loads, has the intended crop/focal point, and preserves its aspect ratio.
- Responsive sources resolve to valid assets; high-density screens do not receive visibly blurred critical art.
- Broken or unavailable assets have stable fallbacks that preserve layout and guidance.
- `object-fit`, clipping, masks, and rounded corners do not cut off faces, labels, legends, or essential content.
- Media never bleeds outside cards, sheets, dialogs, or the viewport.
- Reserved dimensions prevent disruptive layout shift while media loads.
- Decorative images are ignored by assistive technology; meaningful images have useful alternatives.
- SVGs have a valid view box and do not clip strokes at different sizes.
- Charts and canvases resize without stale dimensions, illegible labels, or pointer-coordinate drift.
- Fullscreen, zoom, download, pause, mute, and retry controls work when present.
- Favicon, app icons, and OS-level surfaces (PWA splash, title bar, notifications) stay legible in both light and dark contexts.

## 9. Localization and formats

- Dates, times, numbers, and currency follow the user's locale or a deliberate product convention; timezone is user-local or explicitly labeled, never silently server-local.
- Relative timestamps stay truthful and expose the absolute time on demand.
- Pluralized and templated strings survive counts of 0, 1, and many.
- Non-Latin scripts, diacritics, and emoji render without clipped glyphs or jarring fallback fonts.
- When RTL is supported: layout, alignment, and directional icons (back, next, progress) mirror correctly; when unsupported, record it instead of guessing.
- Sorting and search are locale-aware where users would notice (names, accented strings).

## 10. Interaction and accessibility fundamentals

- Keyboard order follows the visual/task order.
- Every interactive control has an accessible name and correct role/state.
- Focus is visible in every theme and is not clipped.
- Opening a modal/drawer moves focus appropriately; closing restores it to a meaningful control.
- Escape and platform-standard dismissal do not discard work silently.
- Status changes, validation errors, and async completion are announced when needed.
- Reduced-motion preferences remove nonessential motion without removing information.
- Hover-only information has keyboard and touch access.
- Drag-only interactions have another usable path when the product requires accessibility.
- Scroll containers do not trap keyboard, trackpad, wheel, or touch navigation.
- Tooltips do not contain essential actions and remain readable at edges.

This is a usability audit, not an automatic certification. Name any standard tested and preserve the evidence.

## 11. Visual hierarchy and polish

Start with the design context record and the rendered flow, then apply the detailed lens in [DESIGN-QUALITY.md](DESIGN-QUALITY.md).

- The first visual emphasis matches the page or step's primary user job.
- Typography establishes a clear title, section hierarchy, body rhythm, and supporting roles without flattening everything or making every element compete.
- Spacing communicates relationships: tight within groups, open between unrelated groups, and deliberate across sections.
- Structural devices—headings, dividers, labels, numbering, cards, and background changes—encode real information instead of decorating empty hierarchy.
- Primary, secondary, tertiary, destructive, cancel, and recovery actions are visually and semantically distinct.
- Copy uses user-recognizable nouns and specific verbs; action names remain consistent through loading, success, and failure.
- Empty, loading, validation, error, and success states give direction in the product's voice without invented claims, metrics, testimonials, or filler.
- Dense screens support scanning and progressive detail; sparse screens do not force excessive navigation or scrolling to reach the job.
- Alignment, radii, borders, shadows, icons, image treatments, and motion form one coherent system or intentionally documented exceptions.
- Semantic state has a visible counterpart: current, expanded, selected, invalid, busy, and disabled states can be perceived, not only exposed to assistive technology.
- Near-instant operations do not flash spinners; loading feedback preserves geometry and never masquerades as actionable content.
- Motion has a named purpose—feedback, continuity, state explanation, or prevention of a jarring change—and its intensity matches how often the action occurs.
- The interface has at most a small number of expressive moves; decoration that does not help comprehension, identity, or useful delight is removed.
- Product-specific copy, imagery, terminology, and interaction details make the surface feel grounded in its subject where expression matters.
- Familiar patterns such as centered heroes, equal feature cards, repeated eyebrows, card nesting, generic gradients, common nav/footer shapes, or universal hover lifts are treated as leads. Report only the concrete task, trust, accessibility, comprehension, or identity cost observed in context.
- Real product screenshots are shown without fake browser, phone, IDE, or code-window chrome.
- Polishing one screen does not create a parallel token system, replace the product's identity, or regress established accessibility wins.
- The audit names specific strengths and product signatures to preserve, not only defects.

## 12. Technical UI health

Observe while traversing the flows:

- uncaught exceptions, rejected promises, hydration failures, and framework warnings;
- failed page, data, font, image, icon, and source-map requests;
- repeated requests, loops, duplicate event handlers, and double navigation;
- interaction delay, scroll jank, or main-thread stalls that materially obscure feedback or cause missed input;
- cumulative layout movement during fonts, images, async data, and route transitions;
- invisible overlays or stale backdrops intercepting pointer/keyboard input;
- orphaned focus, scroll lock left behind, and body overflow not restored after dialogs;
- stale cached assets or service workers producing mismatched UI versions;
- route/history entries that trap back/forward navigation;
- state reset caused by unstable keys, remounts, or theme/runtime initialization.
- secrets, reset links, private record contents, or session identifiers leaking into URLs, logs, screenshots, or clipboard affordances.

## 13. Evidence record

For every test pass, record:

| Field | Required evidence |
| --- | --- |
| Evidence ID | Stable identifier used by the report card and capture |
| Flow | User goal and start/end state |
| Step | Exact action where behavior occurs |
| Runtime | URL/build/app version/commit and browser engine when known |
| Viewport | CSS pixels or native window dimensions |
| Theme | Light, dark, system, or unsupported |
| Input | Mouse, keyboard, touch emulation, or native input |
| Outcome | Pass, gap, blocked, or not applicable |
| Evidence | Screenshot plus console/network/log detail when relevant |
| Data safety | Fixture/account used and any redaction performed |
| Reproduction | Minimal deterministic steps |
| Confidence | Verified, source-proven, or untested risk |

For every visual-design or copy finding, also record the product/task mismatch, the existing strength to preserve, the narrow direction, and a same-condition acceptance check. Omit unsupported aesthetic preference. Use `P3 Opportunity` only for an observed, evidence-backed user or product benefit, or for product-grounded brand-expression work the user explicitly requested.

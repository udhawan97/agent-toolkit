# Product-Specific Design Quality Lens

Use this reference to judge visual hierarchy, structural design, copy, motion, responsiveness, and product identity inside a real user journey. It complements the flow checklist; it does not replace runtime evidence or authorize a redesign.

## Operating posture

- Start from the rendered product, its real content, and the selected user job.
- Read the existing design language before judging it: tokens, typography, icons, imagery, motion, component conventions, platform norms, and brand assets.
- Record an initial visual impression before running anti-pattern detectors. Detector output is a lead, not the frame for the whole review.
- Distinguish a deliberate convention from an unexamined default. Familiar does not mean wrong; unusual does not mean good.
- Preserve specific strengths and accessibility wins. An improvement that erases the product's recognizable character is a regression.
- Keep continuity ahead of expression. A blocked, lossy, or unrecoverable task outranks visual differentiation.

## Design context record

Write a compact record before grading craft:

1. **Audience** — who is using this flow and what they already understand, based on evidence.
2. **Primary job** — the one thing this surface must help them decide, do, read, or monitor.
3. **Product language** — established type, color, spacing, icon, motion, layout, and copy patterns.
4. **Signature** — the one or two choices that make this product recognizable, if any.
5. **Preserve** — useful conventions, strong states, and accessibility behavior that must survive.
6. **Constraints** — platform, brand, content, implementation, performance, and supported-layout limits.

If evidence does not establish an item, write `Unknown`. Do not manufacture a persona, tone, brand promise, or design rationale.

## Eight review lenses

### 1. Task-shaped hierarchy

- The first visual emphasis matches the flow's primary job.
- Primary, secondary, destructive, and escape actions have an intentional order.
- Headings, labels, dividers, numbering, and containment encode real relationships or sequence.
- The scan path remains clear in loading, empty, error, success, and long-content states.
- Density matches the work: operational surfaces favor rapid scanning; reading surfaces favor comprehension; showcase surfaces let the artifact lead.

### 2. Subject specificity and identity

- Copy, imagery, materials, terminology, and interaction details come from the product's actual domain.
- The visual system feels coherent with the product rather than interchangeable with an unrelated category.
- A memorable element earns its attention by expressing the subject or helping the task.
- Existing brand choices are refined, not replaced by the auditor's preferred aesthetic.

Ask: **Could an unrelated product use this screen unchanged?** If yes, identify the concrete cost before reporting a gap: weaker orientation, trust, comprehension, differentiation, or task priority. Category interchangeability alone is not automatically a defect in utilitarian UI.

### 3. Typography, spacing, and composition

- Type roles are distinct enough to scan but do not compete.
- Line length, line height, weight, width, and spacing fit the content and platform.
- Spacing communicates proximity: tight within a group, open between unrelated groups.
- Alignment and grid behavior are intentional across sections and states.
- Containment is earned; avoid nested surfaces when spacing or a divider communicates the relationship better.
- Minimal interfaces show precision; expressive interfaces justify their complexity.

### 4. Copy as interface

- Use nouns and verbs users recognize, not internal architecture.
- Controls name the action and retain the same verb through confirmation or error feedback.
- Labels label, examples demonstrate, helper text helps; no element quietly performs two jobs.
- Empty, loading, validation, and error states say what happened and what to do next.
- Links make sense out of context; generic `Click here`, `OK`, and unexplained `Submit` are leads.
- Tone matches the product and situation, especially in failure and high-stakes paths.
- Never invent metrics, testimonials, logos, research, user quotes, or product claims to fill a visual slot.

### 5. Interaction and motion craft

- Every supported interactive state is visible and semantically correct: default, hover, focus, pressed, selected, disabled, loading, success, warning, error, and destructive.
- Semantic state has a visible counterpart; for example, `aria-current`, `aria-expanded`, and `aria-invalid` are perceivable in the rendered UI.
- Motion has a named purpose: feedback, spatial continuity, state explanation, or prevention of a jarring change.
- Motion intensity reflects action frequency. Repeated navigation and keyboard work should feel immediate; rare explanatory moments may carry more expression.
- Hover behavior has keyboard and coarse-pointer equivalents.
- Focus appears immediately and remains visible. Reduced motion preserves information without unnecessary spatial movement.
- Avoid universal hover lifts, `transition: all`, repeated scroll reveals, flashing spinners, and celebratory feedback for an already-visible success unless the product context earns them.

### 6. System coherence

- Reuse the existing token and component vocabulary where it is sound.
- Raw color, spacing, type, radius, shadow, z-index, and motion values do not form an accidental parallel system.
- Similar controls look and behave alike; different meanings remain distinguishable.
- Icon families, stroke weights, illustration styles, and image treatments are coherent.
- Theme changes preserve hierarchy, semantic colors, assets, and focus—not merely background and body text.
- A shared root cause should produce one finding with affected surfaces, not inflated duplicates.

### 7. Responsive composition

Use project-defined support and breakpoints first. When the web project has no documented widths, representative checks may include 320, 375, 414, 768, 1024, and 1440 CSS pixels.

- No page-level horizontal scroll or clipped essential content.
- Long headings, translated text, identifiers, chips, badges, and errors reflow without overlap.
- Buttons, primary navigation, tabs, breadcrumbs, and compact action labels stay legible; if a label wraps awkwardly, shorten it or recompose its container rather than hiding meaning.
- Grid and flex children can shrink; media tracks do not force overflow; images keep a deliberate crop and aspect ratio.
- Mobile order follows task priority rather than merely stacking desktop columns.
- Dialogs, popovers, sticky regions, safe areas, and virtual keyboards do not hide work or escape controls.
- Text zoom and roughly 30% expansion remain usable.

Do not treat `overflow-x: hidden` or `clip` as proof that overflow is fixed. Confirm the offending content itself fits or has an intentional local scroll region.

### 8. Restraint and truthful content

- Decoration has a job. Remove elements whose loss does not affect comprehension, identity, or useful delight.
- Use one primary expressive move instead of scattering effects across every section.
- Real screenshots use simple evidence frames; do not redraw fake browser, phone, IDE, or code-window chrome.
- Generic gradients, floating blobs, decorative emoji, card-in-card nesting, repeated eyebrow labels, equal three-card rows, generic nav/footer shapes, and centered full-viewport heroes are **named leads**, not automatic defects.
- When a named lead appears, test whether it is justified by the content, product genre, task, and surrounding system. Report the observed mismatch, not the label alone.

## Evidence and severity rules

- `Verified` requires the rendered flow and named state or viewport.
- `Source-proven` may establish token drift, missing state code, or deterministic semantics, but not perceived hierarchy or visual impact that was never rendered.
- `Untested risk` stays a hypothesis.
- Omit a design preference without demonstrated user or product benefit or cost. Use `P3 Opportunity` only for an observed, evidence-backed benefit or for product-grounded brand-expression work the user explicitly requested.
- Use `P1 Major` for design only when the rendered issue seriously impairs completion, recovery, comprehension, accessibility, or trust. Use `P0 Blocker` only when the task truly cannot complete or work/data is lost.

For every design-craft gap, record:

1. screenshot and exact state;
2. observed visual or copy choice;
3. product/task mismatch and user consequence;
4. what existing strength must be preserved;
5. narrow fix direction;
6. same-condition acceptance check.

Also record specific strengths. A useful critique tells the implementer what not to change.

## Direction brief for authorized visual fixes

Before a material visual change, write five lines:

- **User job** — what becomes easier to understand or do.
- **Preserve** — identity, content, behavior, and accessibility that stay.
- **Change** — the narrow visual or interaction rule being corrected.
- **Rationale** — why this direction fits the product rather than a generic template.
- **Proof** — the state, viewport, theme, input, and observable result that will validate it.

If two materially different directions would both satisfy the gap but change product identity, show concise alternatives or wireframes and ask the user to choose. Gap-selection authority does not authorize an unmentioned rebrand.

## Bounded critique loop

Use two deliberate passes for authorized craft work:

1. **Before code:** critique the direction brief for product specificity, truthful content, structural meaning, and restraint.
2. **After render:** inspect same-condition screenshots, remove any flourish the comparison shows is unnecessary, and otherwise make no aesthetic-only change; then check neighboring states, narrow layouts, focus, and reduced motion.

Stop when the acceptance checks pass. Do not turn polishing into an open-ended redesign loop.

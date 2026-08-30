# Dev Review Lenses

Read this file before the three-specialist audit. It is a risk map, not a quota and not a claim of exhaustive certification. Apply relevant checks, record `N/A` separately from `Not tested`, and deepen coverage where failure can block, lose, expose, corrupt, misprice, or misrepresent user work.

## Evidence discipline

For every material claim, record:

- evidence ID, repository revision/build/runtime, and exact scope;
- observed behavior or deterministic source fact;
- reproduction or trace and relevant file locations;
- user or production consequence;
- root cause, supported mechanism, or explicit hypothesis;
- preservation constraint and smallest plausible direction;
- observable acceptance check;
- severity, outcome evidence, causal confidence, recommendation strength, effort, and regression risk.

`Verified` requires runtime reproduction or an executed production-path check. `Source-proven` is deterministic from current source/config but not runtime-exercised. `Untested risk` is a lead, never a defect claim. Keep causal confidence separate: a reproduced symptom can still have only a `Cause hypothesis`.

One scanner warning, old dependency, large file, TODO, style preference, benchmark from another product, or unfamiliar pattern is not a finding by itself.

## 1. Product promise and user journeys

- Identify the audience, primary job, supported platforms, data promises, and success state from evidence.
- Map selected journeys as `entry -> action/decision -> feedback -> completion -> return/recovery`.
- Baseline first/returning entry, primary completion, cancel/back/out, re-entry, one failure/recovery path, and narrow plus normal supported layout.
- Deep-test destructive, sensitive, stateful, recently changed, high-reach, and high-frequency flows when frequency evidence exists.
- Check empty, loading, delayed, validation, partial, offline, permission-denied, session-expiry, stale, retry, destructive-confirmation, and interrupted states where applicable.
- Check double action, concurrent tab/window, refresh, back/forward, reload, and resume behavior for duplication or state loss.
- At each step ask: Where am I? What can I do? What happened? What comes next? How can I cancel, retry, or recover safely?

## 2. Product-specific design craft

Create a compact design context record before judging appearance:

- audience and primary job;
- established type, color, spacing, icon, motion, layout, and copy language;
- recognizable product signatures and accessibility wins to preserve;
- platform, brand, content, performance, and implementation constraints;
- unknowns.

Review task-shaped hierarchy, copy as interface, interaction feedback, system coherence, responsive composition, truthful content, and restraint. Familiar heroes, card grids, gradients, common fonts, or hover treatments are leads only. Report the concrete task, trust, comprehension, accessibility, or identity cost observed on the real surface. Never “fix” an established product by imposing a generic design system or invented brand story.

For material visual changes, require a five-line direction brief: `User job`, `Preserve`, `Change`, `Rationale`, `Proof`.

## 3. Accessibility and input

- Keyboard order follows visual/task order; focus is visible, immediate, and restored after overlays.
- Controls expose correct names, roles, states, labels, instructions, errors, and status announcements.
- Pointer, touch, keyboard, paste, autofill, IME, dictation, and mobile keyboard behavior match the supported product.
- Escape, cancel, back, and destructive confirmation follow platform expectations without silent data loss.
- Text zoom, roughly 30% expansion, reduced motion, forced colors/high contrast, and color-independent states remain usable when supported.
- Hover-only and drag-only interaction has an equivalent path when required.

Do not claim conformance to a named accessibility standard without executing and recording the applicable checks.

## 4. Responsive and visual states

Use documented breakpoints first. Otherwise sample risk-relevant widths such as 320, 375, 414, 768, 1024, and 1440 CSS pixels; for native apps use minimum, normal, and maximized windows.

- No accidental page-level overflow, clipping, overlap, hidden action, unreadable annotation, or viewport/safe-area trap.
- Long labels, identifiers, errors, translations, empty content, one item, many items, slow/broken media, and dynamic content reflow intentionally.
- Dialogs, menus, toasts, sticky regions, virtual keyboards, charts, images, and icons stay inside the usable surface.
- Light, dark, and system themes preserve hierarchy, semantic states, assets, native controls, and focus where supported.
- Loading and async feedback preserve geometry and do not double-submit or masquerade as completed content.

Automated overflow or accessibility probes are leads; visually confirm them in a real journey before assigning user impact.

## 5. Domain and architecture

- Read `CONTEXT.md` and relevant ADRs. Use domain terms, not incidental class names, when describing seams.
- Find recent hot spots and high-reach paths. Churn plus consequence matters more than line count.
- Identify shallow modules, leaked decisions, shotgun changes, duplicated orchestration, message chains, speculative abstractions, and implicit coupling.
- Apply the deletion test and confirm that any proposed seam has real variation. Do not add an interface for a single imagined adapter.
- Favor small interfaces that hide complex invariants and make the interface the behavior test surface.
- Check dependency direction, ownership, state lifetime, error semantics, cancellation, time, randomness, I/O, serialization, and external adapters.
- Respect ADRs. Reopen one only when current evidence establishes a cost it did not account for.
- Prefer delete/simplify/configure/deepen/incrementally replace over layering or rewriting.

Do not propose a new interface in the audit report when a material product or domain choice is unresolved. Record the decision question first.

## 6. Correctness and data integrity

- Trace invariants from input through state, persistence, output, and recovery.
- Check validation at trust transitions, numeric/date/timezone/locale behavior, ordering, idempotency, retries, partial failure, and duplicate delivery.
- Check concurrency, stale reads, race windows, optimistic updates, cancellation, background work, and multi-process/tab/device behavior.
- Check schema changes, migrations, backward/forward compatibility, rollback, serialization, cache invalidation, and old-client behavior.
- Distinguish retry-safe, reversible, compensating, and irreversible operations.
- Verify errors preserve safe user work and do not turn partial success into silent corruption.

Use fictional or disposable data for financial, medical, authentication, deletion, messaging, or other high-stakes paths unless explicit authority and a safe environment exist.

## 7. Tests and verification quality

- Tests specify observable behavior through stable interfaces, not private implementation.
- Expected values come from independent truth, not a duplicate of the implementation.
- Cover critical success, failure, recovery, state transition, and regression conditions at the narrowest useful seam.
- Prefer a focused regression test that fails before the fix and passes after it.
- Avoid snapshots without meaningful assertions, excessive internal mocks, tautologies, timing sleeps, test-only production interfaces, and brittle fixture oceans.
- Inspect skipped/flaky/quarantined tests, coverage blind spots, nondeterminism, and environment assumptions.
- Run repository-owned checks before inventing tooling. A test command passing does not prove it exercised the affected behavior.

## 8. Security, privacy, and supply chain

- Map trust transitions, authentication, authorization, tenancy, secrets, sensitive data, retention, deletion, export, logging, and third-party egress.
- Check injection, path/file handling, unsafe deserialization, request forgery, cross-site behavior, permission boundaries, dependency execution, and privilege changes relevant to the stack.
- Confirm deny-by-default behavior, redaction, least privilege, safe errors, secure configuration, and no credential leakage in code, logs, URLs, screenshots, reports, or fixtures.
- Inspect dependency provenance, lock integrity, install/build scripts, licenses where distribution is affected, pinned artifacts, and update behavior.
- Treat automated security output as a lead until scope, exploitability, and current configuration are established.

Do not publish exploit details or test destructive behavior against real systems without explicit authority and a safe target.

## 9. Reliability, recovery, and operability

- Check timeouts, cancellation, retry/backoff, idempotency, circuit or queue behavior, resource cleanup, graceful shutdown, and partial degradation.
- Check restart/reload/reconnect recovery, offline state, queued work, duplicate work, and safe resume.
- Confirm logs, metrics, traces, audit events, alerts, and health signals answer the likely production questions without collecting excess sensitive data.
- Check configuration validation, feature-flag failure modes, environment drift, clock assumptions, disk/memory/network exhaustion, and dependency outages.
- Require a rollback or containment path for risky changes and migrations.

Do not invent service-level objectives, traffic, frequency, or production incidents.

## 10. Performance and resource use

- Start with a user-visible or operational symptom and measure the relevant path.
- Check latency, responsiveness, startup, memory, CPU, network, storage, bundle/load cost, query count, rendering work, and large-data behavior as applicable.
- Compare like-for-like conditions and record tools, fixtures, warm/cold state, hardware/emulation, and variance.
- Find algorithmic or architectural causes before micro-optimizing.
- Establish a non-regression budget for changes with meaningful performance risk.

No benchmark, no performance claim. “Could be faster” is not a finding.

## 11. Delivery, dependencies, docs, and production fit

- Verify clean setup, pinned/runtime versions, build reproducibility, configuration examples, migrations, packaging, install/update/uninstall, and supported-platform claims.
- Check CI gates, artifact provenance, signing/notarization where applicable, release notes, rollback, and compatibility.
- Synchronize affected documentation only after behavior stabilizes and only within authorized scope.
- Check observability and support instructions for new failure modes.
- Before merge-ready status, inspect the full diff, staged scope, generated files, secrets, debug flags, fixtures, and untracked artifacts.
- If a code graph exists, refresh it after changes and verify a scoped query.

Green CI is necessary evidence, not proof of a safe release or correct real journey.

## Finding classification

- **Fix candidate** — verified/source-proven outcome, confirmed/supported cause, bounded fix, acceptance check, and acceptable regression risk.
- **Research** — material concern with missing causal proof, unsafe reproduction, or unresolved product decision. Record the exact next experiment or source needed.
- **Preserve / justified** — complexity or convention that is load-bearing, supported, or intentionally accepted.
- **Deferred** — speculative, low-impact, unrelated, superseded, or outside authority.

Zero material findings is valid. Do not pad a roast to make the report entertaining.

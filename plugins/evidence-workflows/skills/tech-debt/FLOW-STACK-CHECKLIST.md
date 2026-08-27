# Flow-to-Stack Evidence Checklist

Use this as a causal investigation map, not a comprehensive scorecard. Start with the selected journey, apply the relevant sections, and record material omissions as `Not tested`.

## Evidence record

For each test or finding, preserve:

| Field | Required record |
| --- | --- |
| Evidence ID | Stable ID used by captures and report cards |
| Journey | User goal and start/end state |
| Step | Exact action and visible state |
| Runtime | Commit/build/version, browser or OS, configuration |
| Conditions | Fixture, layout/window, theme, input, network or device limits |
| Outcome | Pass, gap, blocked, N/A, or not tested |
| User consequence | Blocked, lost, delayed, misled, inaccessible, stale, risky, or opportunity |
| Runtime evidence | Screenshot, timing, trace, console/network/log detail as applicable |
| Stack evidence | File/line, manifest, configuration, dependency path, or authoritative support source |
| Causal bridge | Why the stack mechanism produces the user consequence |
| Outcome evidence | Verified, Source-proven, or Untested risk |
| Cause confidence | Confirmed cause, Supported cause, or Cause hypothesis |
| Data safety | Disposable data/profile and redaction performed |

## 1. Flow continuity and state

Check applicable entry, completion, cancel/back/out, return/re-entry, and recovery behavior.

Stack leads:

- duplicate or competing state stores;
- route state that cannot survive reload, deep link, back/forward, or relaunch;
- unstable keys or remounts that erase drafts, scroll, focus, or selection;
- session expiry that discards work or returns to the wrong place;
- optimistic updates without reconciliation or rollback;
- non-idempotent retries or repeat actions;
- stale cache reads, invalidation gaps, version skew, or service-worker mismatch;
- migrations that cannot read prior user data safely;
- multi-window, multi-tab, multi-device, or background-resume conflicts.

The debt is not “state management is messy.” It is the smallest shared mechanism that causes a named continuity failure or makes that failure untestable.

## 2. Feedback, responsiveness, and perceived progress

Exercise first load, repeat load, navigation, the most important interaction, delayed response, and long-running work.

Stack leads:

- unnecessary request waterfalls or client/server round trips;
- blocking work on the main or UI thread;
- synchronous I/O in an asynchronous path;
- over-large startup bundles, eager modules, fonts, images, or data;
- framework hydration or initialization that delays usable feedback;
- duplicated serialization, parsing, transformations, or rendering;
- polling where push, eventing, or explicit refresh better fits the user job;
- loading state coupled to one request while dependent work continues;
- queues or background jobs that expose no stable progress or recovery state.

Measure user-visible delay and feedback under named conditions. A profiler hotspot without a journey consequence is only a lead.

For web, distinguish real-user field data from controlled lab measurements. Use LCP, INP, and CLS only for the aspects they represent; still complete the flow and inspect the interaction that produced the metric.

## 3. Reliability and recovery

Exercise a plausible error, timeout, offline/interrupted condition, retry, and return after failure.

Stack leads:

- blanket catches or swallowed errors at a seam;
- inconsistent error shapes that prevent a useful recovery action;
- missing timeout, cancellation, retry budget, or idempotency contract;
- retries that duplicate work or hide permanent failure;
- background work without durable status or resume behavior;
- partial writes without transaction, compensation, or user-visible reconciliation;
- network, persistence, or external adapters instantiated inside callers and hard to replace in tests;
- logging without user-facing state, or user-facing failure without diagnostic context.

Test behavior through the same interface used by callers. A mock-only success path is not proof of recovery.

## 4. Compatibility and accessibility reach

Test documented minimum and normal platforms, narrow/normal layouts, keyboard or platform input, and the target browser/OS where relevant.

Stack leads:

- runtime or framework versions outside verified support;
- a dependency that prevents current browser, OS, assistive-technology, locale, or input support;
- non-semantic custom controls created to work around the UI stack;
- focus or accessibility state lost across portals, navigation, hydration, or native bridges;
- unsupported platform APIs without fallback or guarded capability checks;
- styling/build transforms that remove labels, state, focus, reduced-motion, high-contrast, or text-scaling behavior.

Verify lifecycle and compatibility claims against current official documentation. “Old” and “not fashionable” are not findings.

## 5. Data integrity, privacy, and ownership

Trace where the selected flow stores, transmits, caches, synchronizes, exports, and deletes user data.

Stack leads:

- two sources of truth with unclear reconciliation;
- lossy serialization or schema drift;
- client/server validation mismatch;
- unbounded or sensitive data in URLs, logs, analytics, caches, screenshots, or clipboard paths;
- silent cloud/third-party egress where the product contract implies local ownership;
- destructive migrations or one-way data conversion without backup/rollback;
- eventual consistency presented as confirmed completion;
- permissions enforced only in UI code.

Do not exercise real sensitive data or production mutation without explicit authority. Route security-specific work to a security review when the concern extends beyond the selected user journey.

## 6. Delivery and version freshness

Exercise cold start/install, reload/relaunch, update behavior, and a stale-client scenario when supported.

Stack leads:

- client/server contract versions deployed independently without compatibility handling;
- stale service workers, CDN caches, packaged assets, or native bundles;
- non-reproducible builds or floating dependency inputs;
- environment configuration that changes user behavior silently;
- source maps, feature flags, or runtime configuration unavailable when recovery depends on them;
- release packaging that omits migrations, assets, entitlements, permissions, or platform metadata.

A green CI job is not proof that the installed or live surface contains the intended stack change.

## 7. Testability and observability that protect the flow

Map which interface a caller uses and whether tests can exercise the same contract.

Stack leads:

- tests reach past the interface into implementation details;
- production dependencies are created inside the module and cannot be controlled;
- one conceptual journey requires setup across many shallow modules;
- integration bugs sit between pure helpers with no test at the actual seam;
- telemetry cannot distinguish load, action, failure, retry, and completion;
- traces/logs omit stable correlation across a multi-step flow;
- high-churn, high-reach flow code has no deterministic regression path.

Do not report missing coverage percentages without a named behavior the missing test leaves exposed. Do not add observability that collects more user data than the product needs.

## 8. Dependency and platform fitness

Inspect only dependencies and platform choices that participate in the selected journey.

Ask:

- What user-visible capability does this dependency provide?
- Is its interface smaller than the complexity it hides?
- Does it create duplicate runtime weight, state, networking, rendering, or storage?
- Is support, security, compatibility, or licensing status current and verified?
- Would removal spread complexity across callers, or make it disappear?
- Does replacement improve the journey enough to justify migration and regression risk?

Possible outcomes are `keep`, `configure`, `remove`, `upgrade`, `replace incrementally`, or `needs evidence`. “Latest available” is not automatically “best for this flow.”

## 9. Migration debt traps

Before recommending an upgrade or replacement, check whether the plan creates more debt than it removes:

- dual reads, dual writes, compatibility shims, or feature flags with no removal condition;
- two frameworks, runtimes, state stores, clients, schemas, or build paths kept indefinitely;
- backfills or migrations that cannot resume, retry, verify, or roll back safely;
- dependency upgrades that leave duplicate major versions or abandoned adapters;
- a seam introduced for one adapter with no demonstrated variation;
- temporary observability that captures unnecessary user data or becomes permanent by default;
- rollout steps that cannot identify which artifact, schema, or configuration a user actually received;
- a migration whose success is defined only as “build passes.”

Every temporary mechanism needs an owner-independent deletion condition: an observable state that tells a future maintainer it is safe to remove. A calendar date alone is not proof.

## 10. Intervention contract

Before implementation, record:

| Field | Required decision |
| --- | --- |
| Baseline | Current journey behavior and measurement conditions |
| Target | Observable result and provenance for the threshold or comparison |
| Change lever | Smallest stack mechanism expected to move the target |
| Preserve | Product behavior, data, accessibility, privacy, and supported platforms that remain unchanged |
| Non-regression budget | Named neighboring outcomes that may not worsen, with measurement conditions |
| Migration slice | Smallest reversible step that can test the causal bridge |
| Rollback trigger | Observable condition that stops or reverses the change |
| Stop condition | Condition that ends the experiment or prevents further migration |
| Temporary machinery | Flags, shims, adapters, or dual paths plus deletion criteria |
| Proof | Journey replay and interface tests required for resolution |

For a small reversible change, one concise line per applicable field is enough. Expand the contract only as data, platform, rollout, or rollback risk grows. If the target has no product requirement, platform contract, field evidence, or defensible baseline comparison, measure first. Do not invent a threshold to make a recommendation look precise.

## 11. Candidate proof and priority

Before a candidate enters the report, verify:

- the journey step and user consequence are explicit;
- the stack mechanism is cited;
- the causal bridge is more than correlation;
- outcome evidence and cause confidence are labeled separately;
- affected flows and reach evidence are bounded;
- preserve constraints and justified complexity are recorded;
- the narrowest change was considered before migration or rewrite;
- the intervention contract covers effort, migration risk, reversibility, rollback, and temporary-debt removal;
- the acceptance check can be replayed under the original conditions;
- severity, outcome evidence, cause confidence, and recommendation strength are separate labels;
- unsupported frequency, money, adoption, or performance claims are absent.

Severity calibration:

- `P0 Blocker` — core completion is impossible, the user is trapped, or material user work/data is irrecoverably lost.
- `P1 Major` — serious completion, recovery, accessibility, integrity, or trust harm.
- `P2 Friction` — repeatable delay or confusion with completion and recovery intact.
- `P3 Opportunity` — observed improvement potential with a clear user benefit.

Recommendation strength:

- `Strong` requires a `Confirmed cause`, a bounded intervention, and meaningful user benefit.
- `Worth exploring` carries cause, migration, or payoff uncertainty that the next step can reduce.
- `Speculative` names the next evidence test; it is not implementation advice.

If the causal bridge cannot be established, keep the item as a `Cause hypothesis` in `Needs evidence` or `Not tested`; do not promote it with confident prose. Zero material candidates is a valid result.

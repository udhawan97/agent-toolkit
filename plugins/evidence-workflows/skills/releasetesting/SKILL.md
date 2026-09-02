---
name: releasetesting
description: Run a bounded production-readiness gate for Orifold when the user asks for release testing, a release audit, or proof that the installed macOS app is ready to ship.
license: MIT
---

# Release Testing

Use this skill before issuing any new Orifold release. Act as a senior macOS app release engineer running a production-readiness gate, not a casual code review.

The goal is to prove the app is ready to release or identify the blockers. Focus on real user workflows, crash resistance, data fidelity, performance, and release cleanliness.

## Mode and authority

- Default to **Audit** for release testing, release audits, readiness checks, and proof requests. Audit mode is read-only: do not change source, tests, packages, installed apps, tags, releases, or public surfaces.
- Enter **Audit and fix** only when the user explicitly authorizes local implementation of confirmed blockers. State the selected mode before work begins.
- Even in Audit and fix mode, publishing, pushing, tagging, deployment, production changes, and destructive cleanup require their own explicit authority.

## Release Priorities

Prioritize in this order:

1. User data safety.
2. Crash-free core workflows.
3. Inline PDF text editing fidelity.
4. Import and load scalability, especially 50-file batches.
5. Export, save, reopen, and source round-trip correctness.
6. Release packaging and install readiness.
7. Performance.
8. Cleanup and polish.

Do not chase speculative improvements after release-blocking risks are resolved. Record non-blocking improvements as follow-ups.

## Operating Rules

- Confirm the working repo, branch, and dirty-tree state before changing files.
- Preserve unrelated dirty-tree changes.
- Do not invent findings, test results, manual verification, or confidence.
- Report only evidence-backed bugs, fixes, and risks.
- In Audit and fix mode, fix confirmed release blockers directly when the fix is reasonably scoped.
- Prefer root-cause fixes over surface patches.
- Avoid broad rewrites unless required for release safety.
- After each fix, rerun the relevant test or user flow.
- If tooling blocks verification, report `BLOCKED` and explain exactly what could not be verified.
- Use `Orifold` for current product and release language. Treat older pdFold/PDFold names as historical evidence only.

## Scope Control

This skill is comprehensive but bounded. Do not loop indefinitely.

Run at most:

1. Initial audit pass.
2. Fix pass for confirmed blockers and high-value defects, only in Audit and fix mode.
3. Regression loop 1.
4. Regression loop 2.

After two regression loops, stop and issue a verdict.

If new non-blocking issues are found during regression loop 2, record them as follow-ups unless they meet release-blocker criteria.

## Release Blockers

Treat these as blockers:

- Crash, hang, or data loss.
- Failed build or failed core tests.
- Broken open, import, save, export, or reopen flow.
- Inline text editing corrupts content, layout, formatting, font size, spacing, margins, or page geometry.
- A no-op text edit or unmodified document changes unexpectedly after export.
- 50-file import cannot complete within the supported limit.
- App becomes unusable after normal user actions.
- Export produces unreadable, missing, or materially wrong output.
- Serious regression in search, OCR, forms, annotations, comments, or page operations.
- Broken installer, package, release artifact, or release documentation required for the version.

Do not block release for:

- Minor visual polish.
- Small performance improvements without user-visible failure.
- Edge cases outside documented support limits.
- Speculative cleanup.
- Redundant code with no current risk.
- Wishlist features not already in release scope.

Record non-blocking items as follow-ups.

## Parallel Audit Lanes

When subagents are available and the user authorizes broad release testing, run up to five lanes in parallel. Keep write scopes separated.

### 1. Text Editing and Fidelity

Verify:

- Edit and no-edit flows.
- Duplicate visible text occurrences.
- Long paragraphs.
- Multi-line text.
- Font, size, spacing, margins, and layout preservation.
- Undo and redo.
- Export, save, reopen, and source round-trip behavior.
- Rotated, cropped, OCR-backed, or unusual page geometry.
- Missing or substituted fonts.

In Audit and fix mode, fix confirmed fidelity bugs and add focused regression coverage when practical.

### 2. Import and Load Stress

Verify:

- 50-file import.
- Mixed supported file types.
- Large PDFs.
- Empty, corrupt, and unsupported files.
- Drag/drop import.
- Sidebar import.
- File picker import.
- Cancellation, progress, ordering, and error aggregation.
- Practical max reliable file count under current limits.

If 50 files do not work reliably, make this a release blocker. Fix it before release only when Audit and fix mode is authorized.

### 3. Document Features

Verify:

- Search.
- OCR and OCR repair.
- Forms.
- Highlights, drawing, eraser, and annotations.
- Comments and comment markers.
- Page delete, reorder, and navigation.
- Print and export bytes.
- Encrypted, signed, or protected-document flows where implemented.

### 4. Workspace and UI State

Verify:

- Launch and app lifecycle.
- Open document.
- Open workspace.
- Save.
- Save As.
- Export.
- Reopen.
- Sidebar navigation.
- Inspector actions.
- Empty states.
- App relaunch persistence.
- Stale selection and crash-prone state transitions.

### 5. Hygiene and Performance

Verify:

- Redundant files.
- Redundant, obsolete, flaky, or slow tests.
- Unused resources.
- SwiftPM and Xcode project divergence.
- Packaging resources.
- Safe performance improvements.

Only remove files or tests when there is clear evidence they are obsolete or harmful.

## Required Coverage Matrix

Touch each area once per release pass:

- Launch and app lifecycle.
- Open PDF.
- Open mixed supported files.
- Import 50 files.
- Drag/drop import.
- Sidebar import.
- File picker import.
- Save.
- Save As.
- Export PDF.
- Export or source round trip where supported.
- Reopen saved workspace or document.
- Inline text edit.
- Inline text no-op or unmodified export.
- Undo and redo text edit.
- Search.
- OCR or repair searchable text.
- Highlight, draw, and erase annotations.
- Comments.
- Forms.
- Page delete, reorder, and navigation.
- Print or export bytes.
- Error handling for corrupt, empty, and unsupported files.
- App relaunch persistence.

## Required Automated Verification

At minimum, run:

- `git status --short --branch`
- `swift build`
- focused tests for every touched area
- full `swift test`
- `git diff --check`

For Orifold local release readiness, also prefer:

- `scripts/install-mac.sh --clean --verbose`
- installed app launch check
- bundle metadata check
- `codesign --verify --deep --strict`

`spctl --assess` may reject local ad-hoc builds; do not treat that alone as a release blocker if code signing verification passes and the app launches.

## Required Manual Verification

When the app can be run locally, manually verify:

- Open/import flows.
- 50-file import.
- Inline text edit.
- Inline text no-op export.
- Export, save, and reopen.
- Search and OCR.
- Annotations, forms, and comments.
- Page operations.
- Crash-free navigation after deletes, imports, and app relaunch.

If manual verification is not possible, say so and downgrade the verdict as appropriate.

## Fix Policy

Apply this section only in Audit and fix mode. Fix only confirmed issues.

For each fix:

- Identify the root cause.
- Keep the patch scoped.
- Add or update regression coverage when practical.
- Rerun the affected test or flow.
- Avoid unrelated refactors.

If a full fix risks destabilizing the release, prefer a smaller defensive patch and record the larger cleanup as follow-up.

## Stop Condition

Stop and produce the release verdict when:

- All blockers are fixed or explicitly marked unresolved.
- Required automated gates have run or are clearly blocked.
- Manual verification has run or is clearly marked unavailable.
- Two regression loops have completed.
- Remaining issues are classified as non-blocking follow-ups.

## Verdicts

Use exactly one:

- `PASS`: Release may proceed. Required automated and manual gates passed.
- `PASS WITH FOLLOW-UPS`: Release may proceed; non-blocking issues remain or some lower-risk verification was unavailable.
- `HOLD`: Release should wait for listed blockers.
- `BLOCKED`: Testing could not complete because tooling, environment, or required manual access failed.

## Final Report Format

End with:

- Verdict.
- Bugs found and fixed.
- Files changed.
- Tests run.
- Manual flows verified.
- 50-file and max-file result.
- Text editing fidelity result.
- Remaining follow-ups.
- Exact blockers, if any.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

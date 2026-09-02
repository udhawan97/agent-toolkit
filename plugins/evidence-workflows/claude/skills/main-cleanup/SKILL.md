---
name: main-cleanup
description: Audit every local branch, remote branch, and worktree in a Git repository; identify unique relevant work; safely integrate verified work into the default branch; push the completed default branch; and prune only refs proven safe to remove. Use when the user invokes /main-cleanup or asks to check all branches, merge relevant work, consolidate parallel efforts, rescue overlooked changes, synchronize or clean up main, or finish repository branch cleanup.
license: MIT
disable-model-invocation: true
---

# Main Cleanup

Consolidate valuable repository work without losing user changes. Finish with a verified, synchronized default branch and an evidence-backed account of every branch.

## Respect the requested mode

- Execute the workflow when the user invokes `/main-cleanup` or explicitly asks to check, merge, and clean branches.
- Stay read-only when the user asks only for a plan, audit, explanation, or status report.
- Treat an execution request as authorization to inspect refs, create a temporary integration branch/worktree, merge relevant work, run repository checks, update and push the default branch, and remove branches proven safely integrated.
- Do not infer authorization for releases, tags, deployments, force pushes, history rewrites, or deleting ambiguous work.
- Apply additional user arguments as scope or constraints. Let repository instructions and explicit user constraints override this workflow.

## State a brief plan

Before mutating Git state, state a short plan covering inventory, relevance analysis, isolated integration, verification, promotion, and cleanup. Proceed without pausing for routine choices. Ask only when ambiguity could discard work, change product intent, or require authority the user did not grant.

## 1. Establish repository truth

1. Resolve the repository root and confirm this is a Git worktree.
2. Read applicable `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, release notes, roadmaps, and repository-specific merge or validation instructions.
3. Identify the default branch from repository and remote evidence. Use `main` when present; otherwise use the configured default branch without renaming it unless requested.
4. Record before-state evidence:
   - `git status --short --branch`
   - `git remote -v`
   - `git branch -vv`
   - `git worktree list --porcelain`
   - local and remote refs with upstream, tip SHA, author date, and subject
5. Fetch all configured remotes with pruning. Do not treat a stale local tracking ref as current evidence.
6. Inspect every worktree for staged, unstaged, and untracked files. Never stash, reset, clean, overwrite, move, or delete user-owned changes merely to simplify cleanup.
7. Inspect local-only default-branch commits and uncommitted work as possible relevant work rather than assuming `origin/<default>` is the whole truth.
8. Use an isolated temporary worktree and uniquely named integration branch when the current checkout is dirty, another worktree owns the default branch, or multiple branches must be combined. Create temporary paths with `mktemp -d`; record the exact path and ref.

## 2. Inventory and classify every candidate

Include local branches, remote-only branches, branches checked out in other worktrees, and open or recently closed pull requests when `gh` is available. Exclude only the resolved default branch and the temporary integration ref.

For each candidate:

1. Determine ancestry and stacking relationships with the default branch and other candidates.
2. Inspect commit subjects, full diffs, changed files, tests, documentation, generated artifacts, and linked issue or pull-request context.
3. Distinguish unique work from replayed or squash-merged work. Do not rely only on `merge-base --is-ancestor` or the hosting provider's merged flag. Use evidence such as:
   - `git log --left-right --cherry-pick <default>...<candidate>`
   - `git cherry <default> <candidate>`
   - merge-base and ancestry checks
   - direct commit and final-tree diffs
   - `git range-diff` when commits were rebased, replayed, or squashed
4. If `graphify-out/graph.json` exists and cross-file behavior affects relevance, query the existing graph before broad source searching. Corroborate graph results with current diffs and source.
5. Classify the candidate and record concise evidence:
   - **Integrate**: contains unique, coherent work that still fits current product intent and can be verified.
   - **Already present**: its meaningful change is already in the default branch, even if commit hashes differ.
   - **Preserve**: active, ambiguous, externally owned, attached to a dirty worktree, blocked by a material decision, or not yet safe to integrate.
   - **Obsolete**: superseded or irrelevant work with no unique value worth rescuing.
6. Treat generated-only drift, dependency churn, experiments, and partial features as relevant only when their source and current product intent support them.
7. Prefer rescuing a clear valuable subset from a mixed branch over merging unrelated or obsolete changes wholesale.

Never classify by branch name, age, apparent merge status, or green CI alone.

## 3. Build an integration order

1. Order stacked or dependent branches from foundation to dependent work.
2. Merge complete coherent branches using the repository's established history convention. Infer that convention from repository instructions and recent default-branch history.
3. If no convention exists, preserve provenance for complete branches with an explicit merge commit; cherry-pick the minimal coherent commits from mixed branches.
4. Avoid rebasing or rewriting user branches unless explicitly requested.
5. Re-fetch and ensure the integration base is current before the first integration.

## 4. Integrate safely

For each **Integrate** candidate:

1. Apply only its relevant unit to the isolated integration branch.
2. Resolve conflicts from current source, tests, product contracts, and branch intent. Never resolve a whole conflict set by blindly choosing `ours` or `theirs`.
3. Check the resulting diff for accidental reversions, generated-file drift, secrets, debug artifacts, or unrelated changes.
4. Run the smallest meaningful targeted validation before proceeding to the next candidate.
5. Record the source branch, source commits, integration method, resulting commit, conflicts, and validation.
6. Stop and preserve the candidate when conflict resolution requires a material product decision or when its intent cannot be established from evidence.

After all candidates are combined:

1. Rebuild generated outputs from the complete integration tree when the repository owns generated artifacts. Never rebuild from a tree missing another required branch.
2. Run formatting, linting, type checking, unit/integration tests, builds, and repository-specific checks in proportion to the change risk.
3. Exercise real user-facing or packaged surfaces when repository instructions require them; source tests alone do not replace shipped-surface verification.
4. If the repository already has a Graphify graph, run `graphify update .` and verify one scoped query against the refreshed graph. Treat refresh failure as a completion gate.
5. Diagnose failures. Repair only bounded integration defects whose intended result is clear; do not mask, skip, or weaken checks to make the cleanup pass.
6. Re-fetch the remote default branch after validation. If it moved, integrate the new tip and rerun affected checks.

## 5. Promote and synchronize the default branch

1. Require a clean integration worktree and passing required checks.
2. Update the local default branch by fast-forward when it is not protecting user changes in another worktree.
3. If a dirty worktree owns the local default branch, preserve it. Push the verified integration commit to the remote default branch with a normal non-force refspec when doing so is a valid fast-forward, then report the intentionally preserved local state.
4. For user-owned repositories, push the verified default branch by default. Respect explicit review-only requests, unfamiliar or collaborative remotes, branch protection, required pull requests, and required checks.
5. When branch protection requires a pull request, push the integration branch, open or update the PR, wait for required checks, and merge through the repository's normal path when authorized. Do not bypass protection.
6. Never force-push the default branch.
7. Verify the local and remote default-branch SHAs after promotion. Do not call the task complete from a successful push message alone.

## 6. Clean branches and temporary state

Clean only after the verified work is present on the remote default branch.

1. Protect the default branch, long-lived protected branches, open-PR branches, branches owned by dirty worktrees, and every **Preserve** candidate.
2. Delete exact local branch names only after proving their relevant content is integrated or patch-equivalent. Prefer `git branch -d` for ancestor-merged branches.
3. Use force deletion for a non-ancestor local branch only when patch equivalence is proven by multiple signals and the exact ref is recorded. Never use a pattern or broad deletion loop for force deletion.
4. Delete an exact remote branch only when the repository is user-owned, the cleanup request covers remote refs, the remote default branch contains its relevant work, no open PR or worktree depends on it, and the ref is not protected.
5. Preserve obsolete-but-unmerged or ambiguous branches and report them instead of guessing that they are disposable.
6. Remove the temporary worktree and integration branch only after confirming they are clean and their commit is reachable from the promoted default branch.
7. Prune stale tracking refs and stale worktree metadata. Do not run `git clean`, `reset --hard`, broad recursive deletion, or destructive commands against unresolved paths.

## 7. Verify the clean end state

Confirm:

- the expected default branch is checked out where safe;
- required work is reachable from the default branch;
- local and remote default SHAs match, or any intentionally preserved local divergence is explicit;
- required checks pass on the final tree;
- no merge, rebase, cherry-pick, or bisect is in progress;
- temporary integration refs and worktrees are gone;
- every original candidate has a recorded disposition;
- protected, active, ambiguous, and user-owned dirty work remains intact.

## Report the result

Lead with whether the default branch is clean, verified, and synchronized. Include:

1. the final local and remote SHA;
2. checks run and their outcomes;
3. a compact table of each branch with classification, evidence, integration method or preservation reason, and cleanup action;
4. conflicts or adaptations made;
5. branches/worktrees deliberately preserved and why;
6. deleted local and remote refs;
7. any blocker preventing full completion.

Do not say “all branches are merged” unless every branch was inventoried and every relevant change is reachable from the final default branch or proven patch-equivalent.

## Required council gate

Before communicating material findings or a final result, read and follow [Council Review](../council-review/SKILL.md). Do not run the gate for progress updates, routine questions, or approval requests that contain no material findings.

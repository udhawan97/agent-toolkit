# Evidence Workflows

One portable plugin bundles all 15 original Agent Toolkit skills for Codex and Claude Code.

## General workflows

- `council-review`: challenge important results through two independent review rounds.
- `dev-review`: coordinate a senior review across code, architecture, UX, and production readiness, then improve only selected findings.
- `improve-userflow-design`: audit real journeys and improve only selected gaps.
- `localtesting`: build, install, deduplicate, and verify the real local product surface.
- `loop-refine-release`: coordinate an explicitly requested implementation-to-local-merge loop.
- `main-cleanup`: classify and reconcile every branch and worktree without losing unique work.
- `refresh-docs`: synchronize a product README, website, visuals, and download story.
- `tech-debt`: trace stack or architecture debt to a real user-flow consequence.

## Public product guardrails

- `folioorb-financial-integrity`
- `golavo-product-trust`
- `orifold-workflow`
- `releasegit`
- `releasetesting`
- `shipped-product-verification`
- `voyalier-product-contract`

The guardrails activate only for their named public products or release workflows. They preserve product contracts, financial-data safety, packaging rules, and shipped-surface verification.

Audit skills default to read-only work. Implementation, merging, publishing, and deployment retain their own explicit authority gates. The public bundle contains no credentials, private workspace data, or developer-home paths.

The plugin works by itself. The default Agent Toolkit profile also installs optional upstream helpers that enrich some workflows; `loop-refine-release` uses its bundled architecture and documentation fallbacks when those helpers are absent.

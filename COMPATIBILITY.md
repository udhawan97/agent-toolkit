# Compatibility

| Surface | Minimum policy | Last verified | Status |
| --- | --- | --- | --- |
| Codex CLI | Must expose `codex plugin marketplace` and `codex plugin add` | 0.150.0-alpha.8 on 2026-08-29 | Pass |
| Claude Code | Must expose `claude plugin marketplace`, `install`, and `validate` | 2.1.214 on 2026-08-29 | Pass |
| macOS | At least one supported client; launcher can install missing Git/Python with Homebrew | Simplified dual-client install, repeat install, update, doctor, and ownership-safe uninstall passed on 2026-08-29 | Pass |
| Linux | At least one supported client; launcher supports `apt`, `dnf`, `pacman`, `apk`, and `zypper` for missing Git/Python | Package and POSIX launcher validation configured in CI; native upstream lifecycle pending | Planned |
| Windows | At least one supported client; launcher supports `winget` for missing Git/Python | Package and PowerShell launcher validation configured in CI; native upstream lifecycle pending | Planned |

Native client behavior is a release gate. Filesystem validation alone does not prove fresh-session discovery.

The published `main` baseline for `dev-review` passed repository validation, both native manifest validators, both packaged skill self-tests, 47 unit tests, and an isolated local-source dual-client install/update/doctor lifecycle on 2026-08-30. Fresh-session invocation and native Windows execution remain separate stable-promotion gates.

A pre-`dev-review` 0.3.0 candidate's exact-tree macOS core lifecycle covered marketplace registration, 14 toolkit-owned workflows, guidance merge, repeat installation, update, doctor, toolkit-owned uninstall, and guidance removal in isolated Codex and Claude homes on 2026-08-29. The combined 15-workflow candidate requires a fresh exact-tree lifecycle before promotion.

Hallmark, the three Vercel frontend skills, and the opt-in scheduler are new 0.3 candidate surfaces. The tracked-skill install, repeat update, receipt comparison, and doctor paths passed in isolated Codex and Claude homes against the current upstream commits on 2026-08-30. Scheduler configuration and platform command generation are covered by repository tests; a complete recommended-profile rerun and native scheduler activation check are still required before promotion.

The earlier 0.2.0 expanded-profile lifecycle additionally covered toolkit-managed Graphify 0.9.50 discovery in both configured agent homes, every Matt Pocock skill at the exact fetched commit (37 at that verification), Diagram Design, Ponytail, Understand Anything, five OpenAI essentials through the verified standalone adapter, ten Anthropic essentials, checksum-verified Obscura installation, both MCP registrations, and preservation of upstream packages. That complete expanded lifecycle has not yet been rerun against the exact 0.3.0 candidate tree.

Account authentication, provider service availability, and authenticated skill invocation remain outside automatic installation proof.

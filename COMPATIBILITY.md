# Compatibility

| Surface | Minimum policy | Last verified | Status |
| --- | --- | --- | --- |
| Codex CLI | Must expose `codex plugin marketplace` and `codex plugin add` | 0.150.0-alpha.8 on 2026-08-29 | Pass |
| Claude Code | Must expose `claude plugin marketplace`, `install`, and `validate` | 2.1.214 on 2026-08-29 | Pass |
| macOS | At least one supported client; launcher can install missing Git/Python with Homebrew | Simplified dual-client install, repeat install, update, doctor, and ownership-safe uninstall passed on 2026-08-29 | Pass |
| Linux | At least one supported client; launcher supports `apt`, `dnf`, `pacman`, `apk`, and `zypper` for missing Git/Python | Package and POSIX launcher validation configured in CI; native upstream lifecycle pending | Planned |
| Windows | At least one supported client; launcher supports `winget` for missing Git/Python | Package and PowerShell launcher validation configured in CI; native upstream lifecycle pending | Planned |

Native client behavior is a release gate. Filesystem validation alone does not prove fresh-session discovery.

The 0.3.0 integration candidate adds the explicit-only `dev-review` workflow to separate Codex and Claude payloads. On 2026-08-30, repository validation, both native manifest validators, both packaged skill self-tests, and 47 unit tests passed on the current candidate tree with Codex CLI 0.150.0-alpha.8 and Claude Code 2.1.214. An isolated local-source dual-client install/update/doctor lifecycle also passed during integration. Fresh-session invocation, a final lifecycle replay on the exact promotion candidate, and native Windows execution remain separate gates before stable promotion.

The 0.2.0 macOS lifecycle covers marketplace registration, the three toolkit-owned workflows, guidance merge, toolkit-managed Graphify 0.9.50 discovery in both configured agent homes, every Matt Pocock skill at the exact fetched commit (37 at the latest verification), Diagram Design, Ponytail, Understand Anything, five OpenAI essentials through the verified standalone adapter, ten Anthropic essentials, checksum-verified Obscura installation, both MCP registrations, repeat installation, update, doctor, toolkit-owned uninstall, guidance removal, and preservation of upstream packages.

Account authentication, provider service availability, and authenticated skill invocation remain outside automatic installation proof.

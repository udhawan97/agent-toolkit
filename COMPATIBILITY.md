# Compatibility

| Surface | Minimum policy | Last verified | Status |
| --- | --- | --- | --- |
| Codex CLI | Must expose `codex plugin marketplace` and `codex plugin add` | 0.149.0-alpha.4.3 on 2026-08-26 | Pass |
| Claude Code | Must expose `claude plugin marketplace`, `install`, and `validate` | 2.1.214 on 2026-08-26 | Pass |
| macOS | Python 3.10+, Git, `uv`, Node.js/`npx`, and at least one supported client | Complete dual-client install, repeat install, update, doctor, and ownership-safe uninstall passed on 2026-08-27 | Pass |
| Linux | Python 3.10+, Git, `uv`, Node.js/`npx`, and at least one supported client | Package and POSIX launcher validation configured in CI; native upstream lifecycle pending | Planned |
| Windows | Python 3.10+, Git, `uv`, Node.js/`npx`, and at least one supported client; invoke with `python bin/agent-kit` | Package and PowerShell launcher validation configured in CI; native upstream lifecycle pending | Planned |

Native client behavior is a release gate. Filesystem validation alone does not prove fresh-session discovery.

The 0.2.0 macOS lifecycle covered marketplace registration, the three toolkit-owned workflows, guidance merge, Graphify 0.9.50 discovery in both configured agent homes, 37 Matt Pocock skills, Diagram Design, Ponytail, Understand Anything, five OpenAI essentials through the verified standalone adapter, ten Anthropic essentials, checksum-verified Obscura installation, both MCP registrations, repeat installation, update, doctor, toolkit-owned uninstall, guidance removal, and preservation of upstream packages.

Account authentication, provider service availability, and authenticated skill invocation remain outside automatic installation proof.

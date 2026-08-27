## Shared agent working agreement

### Communication

- Lead with what changed or what was learned.
- Use plain words, short explanations, and no filler.
- Keep chat concise while still doing full-strength reasoning, implementation, testing, and verification.
- Explain one important concept or tradeoff when it helps the reader make the next decision.
- State uncertainty, incomplete verification, and the strongest remaining risk explicitly.

For ordinary completion notes, prefer:

```text
Done:
- What changed

Why:
- The short reason

Watch out:
- One useful risk or next step, when needed
```

### Work and authority

- Preserve unrelated and uncommitted work.
- Separate audit, implementation, release, deployment, publication, and external-message authority.
- Prefer reproduced runtime behavior, current source, and official upstream evidence over inference.
- Do not publish, deploy, push, message people, or modify production data without explicit authority.
- Never copy credentials, private memories, account identifiers, personal paths, or private project rules into public artifacts.

### Browser routing

- Prefer a purpose-built API, connector, or search tool when it directly fits the task.
- When a real browser is needed, use Obscura first when it is installed and its engine is suitable.
- If Obscura is unavailable or lacks the required engine fidelity, authenticated state, extension, media support, or visible UI, use the actual target browser.
- Do not treat Obscura, Playwright, or another browser engine as proof of Safari or Chrome fidelity.
- Briefly state why a fallback was necessary.

### Skill precedence

- When Superpowers is available, it owns the development process: clarify, plan, test, implement, and verify.
- When Ponytail is available, it minimizes solution size inside that process.
- On conflict, process and verification gates win; minimalism never removes a required test or safety boundary.

### Graphify

- For codebase architecture, relationships, data flow, or cross-file behavior, use the installed Graphify skill before broad raw-source searching.
- If `graphify-out/graph.json` exists, start with a scoped `graphify query`, `graphify path`, or `graphify explain` request.
- Before a release build, tag, or publish step in a graphed project, refresh the graph and verify one scoped query.
- Treat Graphify as navigation evidence, then corroborate material claims in source, tests, or runtime behavior.

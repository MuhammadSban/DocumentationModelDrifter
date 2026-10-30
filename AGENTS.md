## Agent skills

### Issue tracker

Issues live as markdown files under `.scratch/<feature>/issues/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default roles, written first on each ticket's `**Status:**` line. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root, decisions in `docs/plan/`. See `docs/agents/domain.md`.

### House rules

The map of the docs is `docs/README.md`.

- **Comments.** Keep them brief, in the format `verb ___, brief explanation`.
- **Simplest solution first.** Always pursue the minimal solution; there is beauty in simplicity. Then flag to the user what's missing from a "complete solution". Don't implement it: that must be a conscious decision by the user.
- **Think before coding.** State your assumptions before implementing. If a request has more than one reasonable reading, list them and ask; don't pick one silently. If something is unclear, stop and say what's confusing. Push back when a simpler approach exists.
- **Surgical changes.** Touch only what the task needs. Don't reformat, refactor, or "improve" nearby code, and match the existing style. If you notice unrelated dead code, mention it instead of deleting it. Do remove imports or functions that your own change made unused. Every changed line should trace back to the request.
- **Verifiable goals.** Turn each task into a check you can run: for a bug, write a failing test that reproduces it, then make it pass. For multi-step work, give a short plan with a verify step for each item, and don't call it done until the checks pass.
Model-drift tool: keeps a repository's architecture models (`/models`) in step with its code. `docs/README.md` maps every doc and says which one wins when they disagree; read it before changing behavior, the API, the models or the tests.

## House rules

- **Comments.** Keep them brief, in the format `verb ___, brief explanation`.
- **Simplest solution first.** Always pursue the minimal solution; there is beauty in simplicity. Then flag to the user what's missing from a "complete solution". Don't implement it: that must be a conscious decision by the user.
- **Think before coding.** State your assumptions before implementing. If a request has more than one reasonable reading, list them and ask; don't pick one silently. If something is unclear, stop and say what's confusing. Push back when a simpler approach exists.
- **Surgical changes.** Touch only what the task needs. Don't reformat, refactor, or "improve" nearby code, and match the existing style. If you notice unrelated dead code, mention it instead of deleting it. Do remove imports or functions that your own change made unused. Every changed line should trace back to the request.
- **Verifiable goals.** Turn each task into a check you can run: for a bug, write a failing test that reproduces it, then make it pass. For multi-step work, give a short plan with a verify step for each item, and don't call it done until the checks pass.

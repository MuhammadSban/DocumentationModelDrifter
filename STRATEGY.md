# Strategy

Only the team changes direction. An agent may propose an edit, and the human approves it.
Status: see Next action in `docs/state/WORK-ITEMS.md`.

## Now

Ship the Phase 5 release: a repository gets a drift check on every push and pull request by adding one line to its workflow. The check says "aligned" only when it really checked, and says why when it could not.

## Deploy gates

- Nothing deploys red: a commit reaches Railway only after CI is green on it.
- The release is tagged only when our tester and Team 16's tester both pass against both systems.
- Nothing other teams or the graders rely on changes without an agreed contract version.
- Agents cannot change the rules that govern them: rule files change only with the human's approval.

## Near-term

In priority order. A line is deleted when its item closes.

1. Decide where the ownership and scope rules come from, to close the self-grant hole (W0-7).
2. Draw the module map and have CI enforce it (W1-5).
3. Show drift on a pull request as annotations and a job summary (W4-3).
4. Offer the check as a reusable workflow that another repository calls in one line (W4-2).
5. Tag the release (W4-1).
6. Run the demo end to end on a public repository (W4-6).

## Long-term

- Support languages beyond Python through one parsing engine (W5-3).
- Rule on the behavioral model, which finds no states on this repository today (N2).
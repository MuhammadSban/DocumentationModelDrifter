# Owner approval instead of owner-only edits

Question: should an edit by a non-owner still be a violation when an owner approved it?

A Phase 5 proposal, not built. Nothing here changes the code, the contract or the spec until the team accepts it.

## The problem

Today every commit that changes a file must be **authored** by one of that file's owners (`docs/base/specifications.md`, ownership comparison; spec case L6: "a non-owner edits an owned path → false: ownership, 1 violation").

Example:

1. Alice owns `billing.py`. Bob does not.
2. Bob changes `billing.py` in a pull request, and Alice reviews and approves it.
3. The check still says **Drifted: ownership violation**.

In real teams many people edit the same file and the owner approves rather than writes every change. So today's rule raises violations nobody cares about.

**What we are not suggesting:** automatically adding every new editor to ownership.json. Anyone who edits a file would then become its owner on that same edit, and the check could never fail. A person who should become an owner is still added by hand, in a reviewed pull request.

## The suggestion

**An edit by a non-owner is fine when an owner of that file approved it.** The rule stays strict (an owner must agree to every change), but the owner can agree by approving, not only by writing the change themselves.

The team picks one of two ways to do this.

### Option 1: let GitHub enforce approval (simple, recommended first)

- drifter's ownership rule stays as it is today. No code change.
- Teams add a `CODEOWNERS` file and turn on branch protection with "Require review from Code Owners". GitHub then blocks the merge until an owner approves.
- Docs explain that drifter's ownership violation is a flag for a person to review, and that GitHub's approval is the real-world gate.

| Good | Bad |
| --- | --- |
| No new code, no contract change | Two places describe owners: ownership.json and CODEOWNERS, which can drift apart |
| GitHub already does it well | drifter still reports the violation even after approval |

### Option 2: drifter reads approvals from GitHub (full)

- For a check on a pull request, drifter asks the GitHub API who approved it.
- A non-owner's commit is fine if an owner of each file it changes approved the pull request. Otherwise it is a violation, as today.
- A local `drifter check` has no pull request, so it keeps today's strict rule: any non-owner edit is a violation.

| Good | Bad |
| --- | --- |
| The verdict matches what the team actually did | New code: GitHub API calls, network errors, maybe a token for rate limits |
| One place describes owners: ownership.json | Changes the contract and spec case L6; the API needs a new input (the pull request number) |
| | The local and hosted checks can give different answers for the same commit |

## Recommendation

Start with **Option 1**: it costs nothing and gives the real-world flow today. Move to **Option 2** only if teams find the leftover violations noisy after owners have approved.

Either way, fix the self-grant hole first (`docs/proposals/init/init.md`, Problem 1). With Option 2 it matters more: the approving owner must be checked against the **old** ownership.json, or a non-owner could add themselves as an owner and then approve their own change.

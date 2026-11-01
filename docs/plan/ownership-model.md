# Ownership model

**Status: built and verified.** `Source/models/ownership_model.py`, demonstrated by
`Source/models/ownership_demo.py`, driven by `Source/orchestration.py`.

Not currently listed in `docs/README.md`. Its substance belongs in the spec: it settles
**"What drifter init proposes as the first ownership.json"**, one of §Q11's open decisions.
Fold it into §3.2 or an ADR and delete this file.

## Two halves

Ownership is not regenerated and diffed like the other two models. History grows with the push
being checked, so a fresh mining would differ from the committed file whenever anyone new touched
a file, whether or not anything was wrong (spec §3.2). So:

| Half | Function | When |
| --- | --- | --- |
| Propose | `propose_ownership(head_sha, records)` | once, at `drifter init`; a person then corrects it by hand |
| Check | `check_ownership(rules, commits)` | every push, against the committed `models/ownership.json` |

Both are pure: no git, network, clock or randomness. The module imports only `dataclasses` and the shared `glob` from `models/common.py`.

## Input

```
PathTouch      path, change_type, old_path | None
CommitRecord   sha, author_email, parents, paths
```

Identity is the **git author email**, as spec §3.2 and the contract's `OwnershipViolation` both
require. No GitHub login, so the commits API is not needed for ownership at all.

`parents` carries every parent SHA. It marks a merge and proves the ordering: validation requires
every commit after the first to be a parent of one already seen, so the connector must read
history with **`git log --topo-order`**, or clock skew can place a parent before its child.

## What init proposes

```json
{ "rules": [ { "owners": ["ana@x.com"], "path": "src/a.py" } ], "schema_version": 1 }
```

Settled with Kaan, 2026-10-31:

| # | Decision | Chosen |
| --- | --- | --- |
| 1 | How many owners per file | **Every author** in the window, not a ranked top owner. No counts in the file. |
| 2 | Granularity | **One rule per file.** A folder rule would be too broad. |
| 3 | Files nobody owns | **No rule at all**, which leaves them open to anyone (spec §3.2). Changes to them are not violations. |
| 4 | Renames | Ownership **moves to the new name**; the old name gets no rule. Chains resolve. |
| 6 | Bots | Recognised by **`[bot]` anywhere in the author email**, which catches `dependabot[bot]@users.noreply.github.com`. A bot never becomes an owner. |
| 9 | `/models` | Owned by the system in v1, so **no rule is proposed** for it. |

Also, not asked but needed: a **merge** names no owner (it carries no change of its own), and a
commit touching more than 50 files is a **sweep** and names no owner. Only the newest **30**
commits per file name its owners, so a departed author does not own a file forever. All three are
keyword arguments, so they are already customisable without a config file.

## What each push checks

For every **non-merge** commit between base and head, each file it changes must have its git
author among the owners of the **first rule** matching that path. Both sides of a rename are
judged, and so are deletions. Output is the contract's `OwnershipViolation`, keys fixed at
`{author, change, commit, owners, path}`, sorted by commit then path.

Patterns use the mapping-v1.1.yaml glob, the one matcher scope.json and classification share
(spec §3.2): `**/` zero or more folders, `**` anything, `*` and `?` within one segment, `\`
before a character to make it literal. Since rules are read as globs, init escapes `\`, `*`
and `?` in the exact paths it proposes.

## Verification

Run outside the tree, not committed: **41 checks** on the model, **22** on the orchestrator
end to end against throwaway git repositories with a real `/models`, and the repo's own
**59** still pass. **16 deliberate mutations** were each confirmed to be caught by a named test,
after one that only looked caught (it was a syntax error) and one real gap (unsorted owners
slipping through) were fixed.

The invariant worth naming: init mines the whole history, and the next check judges the head
commit, whose author is always inside the window. So a fresh proposal never flags its own head.
On a repository whose rules were written by hand to match, init reproduces them byte for byte.

## Deferred

- **Behavioral model**, and with it its entry in the orchestrator's `GENERATORS`.
- **The connector's two missing reads**: a repository's history and its `/models` at a commit.
  The `Reader` interface in `check.py` marks the seam; `LocalReader` already does both against a local clone.
- **Pattern language** for `ownership.json` and `scope.json` (spec §Q11).
- **A tool identity that is not marked `[bot]`** becomes an owner. On this repository
  `noreply@anthropic.com` owns files. The fix is one entry in `bots`, not code.
- **A mining config file**, if the keyword defaults ever need to differ per repository.

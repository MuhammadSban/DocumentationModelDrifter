# Who may edit /models after init

Question: once `drifter init` has written the four files in `/models`, which of them may a person edit by hand, and what can go wrong when they do?

A Phase 5 proposal, not built. Nothing here changes the code, the contract or the spec until the team accepts it.

## Short answer

`/models` cannot be fully read-only. The ownership file is only a guess from git history, so a person has to correct it. But only two of the four files should ever be edited by hand:

| File | Edited by hand? | How it changes |
| --- | --- | --- |
| structural.json | **No** | Only `drifter init` or `drifter update` |
| behavioral.json | **No** | Only `drifter init` or `drifter update` |
| ownership.json | Yes, in a reviewed pull request | A person corrects the guessed owners |
| scope.json | Yes, in a reviewed pull request | The team chooses which files are checked |

Two problems in today's code need fixing first. The bigger one: **someone who is not an owner can make themselves an owner and change the file in the same push, and the check passes.**

## Why /models cannot be read-only

- **Ownership is a guess.** init picks owners from the last 10 commits on each file (spec, `docs/base/specifications.md:238-247`). Someone who fixed one typo becomes an owner. A real owner who has not committed lately is missing. The tool cannot know who should own a file, and the spec says people correct it by hand, like a GitHub CODEOWNERS file (`specifications.md:245`).
- **Scope is a team setting.** Which folders are checked is a choice, not something the tool can work out.
- **It cannot be enforced anyway.** `/models` is a normal folder in the user's own repository, so anyone who can push can change it. What protects it is pull-request review. The git history of `/models` shows who accepted each baseline (`specifications.md:168-170`).

## Why structural.json and behavioral.json should not be hand-edited

They are generated from the code. If one is wrong, fix the code. If the code changed on purpose, run `drifter update`, which rewrites both.

A hand edit here mostly cannot hide anything. The check regenerates both models from the code, so any edit that does not match the code shows up as drift on the next push (spec case L7, `specifications.md:384`). The only edit that removes drift is one that equals what `drifter update` writes, and that is a normal way to accept drift.

## Problem 1: a person can make themselves an owner in the same push

The ownership check reads ownership.json from the **new** commit, the one being checked (`Source/drifter/check.py:215-224`, then `check_ownership` at `check.py:91-92` and `check.py:167`).

So this passes:

1. Alice owns `billing.py`. Bob does not.
2. Bob pushes one commit that changes `billing.py` **and** adds himself as an owner of `billing.py` in ownership.json.
3. The check judges Bob's commit against the rules **inside that same commit**. Bob is now an owner, so the result is Aligned.

A rule that protects `/models` itself (as the spec allows, `specifications.md:246-247`) does not help, because Bob can edit that rule in the same commit too. Today only a human reading the pull request catches this.

scope.json has the same gap: someone can exclude a noisy folder and run `drifter update`, and drift there quietly disappears. Only the diff shows it.

## Problem 2: format checks are weaker than they look

A broken file does not break the system silently. The check stops with `INVALID_MODELS`, exit 2, no verdict, and the old baseline stays (`check.py:352-412`). But:

- **scope.json has no schema file.** Only structural, behavioral and ownership have one (`Source/models/*.schema.json`). When a schema file is missing the schema check skips that model (`check.py:368-373`), and only a few hand-written checks run (`_scope_rule`, `check.py:381`).
- **Every check tests shape only.** A wrong email, a typo in a file pattern, or rules in the wrong order all pass.
- **A broken file still blocks CI** with exit 2. It is loud, but a person only finds out after pushing.

## Recommended fixes, most valuable first

1. **Judge ownership against the old rules.** Check each commit against the ownership.json of the **base** commit (the last accepted baseline), not the new one. Also flag any change to ownership.json or scope.json made by someone who is not an owner of `/models` under the old rules. This closes Problem 1. It is a small change in `read_sources` and `check_ownership`.
2. **Protect /models on GitHub.** Add a CODEOWNERS entry for `/models/` and turn on branch protection that requires their review. Cheap, and GitHub enforces it, not our tool.
3. **Add `drifter validate`.** A local command that runs the same checks as `read_sources` on `/models` without a full check, so format errors are found before pushing. Add a `scope.schema.json` at the same time, so scope.json is checked as strictly as the others.
4. **Write the rule into the docs.** Add the table from the short answer to `docs/diagrams/init.md` and `docs/diagrams/models-folder.md`: structural.json and behavioral.json change only through `init` or `update`; ownership.json and scope.json are edited by hand, only in a reviewed pull request.

Not recommended: moving the ownership rules out of `/models`. It gains nothing and breaks the layout the spec defines.

## The rule, in one line

Only ownership.json and scope.json are edited by hand, through a reviewed pull request; structural.json and behavioral.json change only through `drifter init` or `drifter update`; and changes to ownership are judged against the old rules.

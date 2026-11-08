# Phase 5 TO-DO

What Phase 5 has to do, in the order it should be done. Written 2026-11-05 from a review of every file in `docs/deviations/`, the spec, the contract, the code and `ExampleRepoMAGE`, and from a question-by-question session with the user (Q1 to Q12). Revised the same day after a second check of every folder against this file and an independent review of that check. A plan, not a source of truth: where it disagrees with `docs/base/specifications.md` or `docs/contract/`, they win until an item here changes them.

This file replaces the two older to-do lists, `perspectives/mage_take.md` (C1 to C9, suggested changes 1 to 6) and `perspectives/mage-engineering-env.md` §13. Those files stay as the reasoning behind the items.

## How to read this file

- **Order.** Waves run top to bottom. Inside a wave, the **Depends on** column decides the order, not the item number.
- **IDs are stable.** An item keeps its ID when the file is revised. A new item gets the next free number in its wave, so a higher number does not mean "later".
- **Depends on.** Every item listed there must be finished (committed locally, its "Done when" met) before this item starts. "none" means the item can start as soon as its wave can.
- **Touches.** The files or folders the item changes. It is a footprint, not a promise: an item that needs to touch more must say so before it starts.
- **When two items may run in parallel.** Two items may run at the same time only if (1) neither depends on the other, directly or through other items, and (2) their Touches do not overlap. Where two items would touch the same file, one of them lists the other in **Depends on**, so the order is always written down.
- **Each item does one thing.** If two items seem to cover the same ground, the item text says which one owns it and the other points to it.
- **Anchor.** Spec §6.2 (a tagged pip release, a reusable workflow, answers saved as artifacts, an advisory rollout, the demo) is the core of Phase 5, and everything else is ordered around it. §6.2 may change. Treat it as the most sensible goal, not as a fixed requirement.
- **Tier**: the model that should do the item, as in `perspectives/mage-engineering-env.md` §3:
  - **Haiku**: mechanical lookups and edits;
  - **Sonnet**: make-work with a clear recipe;
  - **Opus**: multi-file or tricky work;
  - **Fable**: planning, design and review;
  - **Human**: GitHub or Railway settings, rulings, public actions and talking to Team 16. No agent can do these.
- **Difficulty**: Easy, Medium, Hard or Unknown (not enough known to estimate).
- **⚠ CONTRACT CHANGE**: the item changes what Team 16's tester or system sees. Team 16 must agree, and it bumps the contract version under `contract/pod-contract.md` §10.
- **SUGGESTION**: agreed in direction, but the team will decide later how to do it.
- **Local only.** Nothing in this file is pushed, merged or written to GitHub, or to any other public place, without the user's explicit OK.

## Facts checked on 2026-11-05

| Fact | How it was checked |
|---|---|
| 277 tests, all pass, 2 min 13 s locally (network test included) | `pytest` run on branch `phase5-kk` |
| The ownership self-grant hole is real | A temp repo: Bob's commit that edits `src/billing.py` **and** adds himself to `ownership.json` gives `aligned: true`, exit 0. The same edit without the self-grant gives a violation. Cause: `read_sources` reads `ownership.json` at the head (`Source/drifter/check.py:216-231`) |
| `Source/models` must not import `GitHub_Connector`, and today it does not | `grep` over `Source/models`, `Source/drifter` |
| Team 16 has agreed to contract 2.4.0 | the user, 2026-11-05. The docs still say "pending" in 9 places |
| `pyproject.toml` installs a top-level package named `models` | `pyproject.toml`: `packages = ["drifter", "models"]` |
| `Source/Frontend_Archive`, `Source/Modelers`, `Source/Viewer` hold only `__pycache__` | `ls` |
| There is no `.github/`, no `.claude/`, no `CLAUDE.md`, and no installed git hook | `ls`, `.git/hooks` holds only samples |
| `STRATEGY.md`, `docs/deviations/`, `docs/diagrams/init.md` and `docs/base/overview_phase4.html` are untracked | `git status` |
| "Pinned CPython ast" appears in `docs/diagrams/one-check.md`, `docs/diagrams/init.md` and `docs/base/overview_phase4.html` | `grep`. `language-engine/04-one-template.md` also names `base/specifications.md` and `base/structure.md`; `grep` found the phrase in neither |
| The spec does not use "Audit → Drain → Promote". Spec line 62 calls the path "recover, reconcile, govern" | `grep` over `docs/base/specifications.md` |

## Parallel lanes at a glance

The main chains, as a summary. A lane waits only where an arrow says so. Items not shown here (W4-7, W5-2 to W5-4, N1 to N6) wait only for what their own **Depends on** column lists. Where this table and a Depends on column disagree, the column wins.

| Lane | Chain (→ means "finish, then start") | Can start |
|---|---|---|
| Docs fixes | W0-1 → W0-2 → W0-3 → W0-4 → W0-5 | at once |
| Ownership ruling | W0-1 → W0-7 (Human ruling) → W3-5 (build) | at once |
| Package and CI | W0-1 → W0-6 → W1-1 → W1-5 → W1-4 → W1-6 → W2-1 / W2-2 | at once |
| Docker and tester | W1-2 → W1-3 → W3-6 → W4-5 → W3-7. W3-3 also waits for W3-6 (both change `api.py`) | at once |
| Process docs | W0-1 → W2-3, W2-4, W2-6, W2-7 (each independent of the others) | after W0-1 |
| Docs reorganisation | Wave 0, W2-1, W2-4 → W2-5 → W2-8 | after those |
| Refactors | W1-1, W1-6 → W3-1 → W3-2 → W3-3 → W3-4 → W3-5; W3-8 after W3-1, beside the chain | after Wave 1 |
| Release | W3-8 → W4-3 → W4-1 → W4-2 → W4-4 → W4-6 | after W1-6 (W4-1 also waits for W3-5) |
| Language-engine evidence | W5-1, W5-6 | at once |

---

## Wave 0: protect the work and correct the docs

Cheap, and nothing later should be built on wrong docs. W0-2 to W0-5 all edit the spec or the docs map, so they run one after the other. W0-6 and W0-7 touch different files and can run beside them.

| ID | Item | Tier · Difficulty | Depends on | Touches | Done when |
|---|---|---|---|---|---|
| W0-1 | **Local commit of the untracked files**: `STRATEGY.md`, `docs/deviations/` (this file included), `docs/diagrams/init.md`, `docs/base/overview_phase4.html`, and the modified `.gitignore` and docs. Local only, no push. | Human · Easy | none | git index only | `git status` shows them tracked. |
| W0-2 | **Record Team 16's agreement.** Replace "pending Team 16's agreement" with "agreed" (and the date) in `contract/pod-contract.md` (line 3, §10), spec §1.3, §5.1, §9.2, Q11 and reference [8], `docs/README.md`, and `history/contract-2.4.0-changes.md` if it says pending. | Haiku · Easy | W0-1 | `contract/pod-contract.md`, `base/specifications.md`, `docs/README.md`, `history/contract-2.4.0-changes.md` | `grep -rn pending docs/contract docs/base/specifications.md` finds no agreement-related line. |
| W0-3 | **Add the grader line (Q10).** Keep deviation 1 (no prose detector). Add one line to the access note in `pod-contract.md` §8: "`issues` is `[]` by design on a system whose `/health` does not list `prose_detector`." Closes `tickets/contract-contradictions.md` #5. ⚠ A contract text change. Ask Team 16 whether an editorial line needs a version bump. | Haiku · Easy, plus Human to tell Team 16 | W0-2 (same file) | `contract/pod-contract.md` §8, `tickets/contract-contradictions.md` | Ticket #5 is in the closed table. |
| W0-4 | **Fix the stale facts.** <br>• `docs/README.md` says `contract/model-golden-outputs.json` is "not yet written"; it exists. <br>• Spec §4.2 names the fixture `MuhammadSban/doc-tracker-model-fixtures`; the contract §3 and the goldens say `kaan-kanadasi/doc-tracker-model-fixtures`. <br>• `tickets/tracker-gaps.md` row 2 is still open, but `_schema_rule` is wired in (`check.py:227`); close it. <br>• Spec Q11 still lists the model JSON Schemas as open; all three exist. <br>This item fixes today's instances once. W2-8 adds the check that stops them coming back. | Haiku · Easy | W0-3 | `docs/README.md`, `base/specifications.md` §4.2 and Q11, `tickets/tracker-gaps.md` | Each line matches the code and the contract. |
| W0-5 | **Reword claims that run ahead of the evidence** (`mage_take.md` suggestion 6 and con 9): <br>• spec §1.2 "becomes the standard" → "becomes the accepted baseline"; <br>• the present-tense benefits become goals until Risk 1 and Risk 2 are measured (N1); <br>• narrow the Annex XI claim (spec Q11 already lists it as open); <br>• con 9: "Audit → Drain → Promote" does not fit a derived baseline, because `drifter init` leaves no backlog to drain. The spec does not use that phrase (see "Facts checked"). Check that no doc implies a backlog to drain, and reword any that does. | Sonnet · Easy, plus Human to approve the wording | W0-4 (same file) | `base/specifications.md` §1.2 and Q11; any doc found by the con 9 check | The team has approved the new wording. |
| W0-6 | **Write down which `/models` files people may edit by hand** (`init/init.md` fix 4): structural and behavioral change only through `drifter init` or `drifter update`; ownership and scope are edited by hand, in a reviewed PR. Add the table to `docs/diagrams/init.md` and `docs/diagrams/models-folder.md`. | Haiku · Easy | W0-1 | `docs/diagrams/init.md`, `docs/diagrams/models-folder.md` | Both diagrams' docs carry the table. |
| W0-7 | **DECIDE: how to close the ownership and scope self-grant hole (Q4).** See the detail below. Decide as early as possible: the build lands in W3-5, and the first release (W4-1) should not ship the hole. | Human · Unknown (deciding) | W0-1 | this file, or `docs/decisions/` once W2-5 exists | The ruling is written down and covers gaps G1 to G4. |

### W0-7 in detail: the self-grant hole

**The problem.** The check judges each commit against the `ownership.json` *in the commit being checked*. A non-owner who adds themselves as an owner and edits the file in the same commit passes. This is reproduced (see "Facts checked"). `scope.json` has the same weakness (G4).

**Already described in** `init/init.md` (Problem 1), `perspectives/mage_take.md` (con 5, C7), `perspectives/industry-architecture-research.md` (item 2), `perspectives/architecture-review.html` (C) and `ownership/owner-approval.md`. All five propose the same fix: judge against the rules at the base. None was ever turned into a ticket.

**Gaps none of those documents covers:**

| Gap | What goes wrong |
|---|---|
| G1. The first commit with `/models` | Its base (fixture case L-pre) has no `/models`. Strict base rules give `MODELS_NOT_FOUND`, and golden case L0 (T-25, expected `true`) breaks. |
| G2. Handing over ownership inside one push | An owner adds Carol in commit 1, and Carol edits in commit 2. Judged against the base's rules, Carol is flagged: a false alert. |
| G3. `ownership.json` is open to anyone | `drifter init` writes no rule for `/models`, so a fix that relies on "only owners may change the rules" needs a rule that owns `models/**`. |
| G4. `scope.json` can be narrowed in the same push | Someone adds a noisy folder to `exclude` and runs `drifter update`; drift in that folder disappears and the check passes. Only the diff shows it (`init/init.md`, Problem 1, last paragraph). S1 and S2 below cover `ownership.json` only, so whichever option is chosen must also say how a `scope.json` change is judged. |

**Options. All four keep REQ-07 (same input, same bytes, no network).**

| Option | How it works | Closes the hole | Cost and scale | Downsides |
|---|---|---|---|---|
| S1. Rules from the base | Judge every commit in base..head against `ownership.json` at the base. If the base has none, use the head's (the first acceptance, G1). For G4: read `scope.json` at the base too. | Yes | One more small blob in the existing `/models` batch download; constant per check | G2 false alert. A scope widening is also invisible until the next push. The goldens stay the same. |
| S2. Rules from each commit's parent | Each commit is judged against its parent's `ownership.json`. `drifter init` also writes a default rule owning `models/**` (G3). For G4: same as S3's flag. | Yes, with the default rule | One read per distinct blob of the file, in practice about one | Changes what `init` writes: T-33 bytes and goldens. ⚠ CONTRACT CHANGE |
| S3. Flag every rules change | Keep the head's rules. Add a violation whenever a commit changes `ownership.json` or `scope.json` and its author does not own `models/**` under the base's rules. Covers G4 directly. | Yes | Same as S1 | Needs the `models/**` rule (G3), so it also touches `init`. ⚠ probably a CONTRACT CHANGE |
| S4. GitHub enforces it | `CODEOWNERS` for `/models/` plus branch protection that requires their review. No code. Covers G4 on GitHub. | Only on GitHub, not in the CLI or the hosted check | Free | Owners are listed in two places (W4-7 tests that they match). Author emails stay spoofable. |

S4 combines with any of the others. Recommended, not decided: S1 + S4.

**Rejected:** `ownership/owner-approval.md` Option 2 (ask the GitHub API who approved the PR). It puts the network inside the check, so the CLI and `/analyze` could answer differently for the same commit. That breaks REQ-07 and the test behind `tracker-gaps.md` row 7. The problem Option 2 was meant to solve (an owner approved a non-owner's edit, and it is still flagged) is now measured in W1-6's tally instead, under its own category.

**Whatever is chosen, it also changes:** spec §3.2 ("Comparison"), probably REQ-01's sentence on what the base decides, `docs/diagrams/comparison.md`. And these tests (each written failing first, in W3-5): self-grant in one commit; a non-owner edits only `ownership.json`; an owner under the old rules; the L0 bootstrap; a non-owner narrows `scope.json` and runs `update` in one push (G4); and, for S1, a handover inside one push.

**Unverified, check while deciding:** a squash merge rewrites who authored the commits on `main` (`perspectives/mage-alignment.html` §3.5). Does the push to `main` after a squash merge judge the right author?

---

## Wave 1: foundations

Do these before the refactors (W3) and the release (W4). The Docker pair (W1-2, W1-3) shares nothing with the rest and runs in its own lane.

| ID | Item | Tier · Difficulty | Depends on | Touches | Done when |
|---|---|---|---|---|---|
| W1-1 | **Rename `Source/models` to `drifter.models` (Q8).** Move it to `Source/drifter/models/`, update the imports in `Source/` and `tests/`, update `pyproject.toml` (`packages`, `package-data`) and every doc that names `Source/models/` (`docs/diagrams/model-seam.md`, `base/structure.md`, `overview_phase4.html`, the `language-engine/` docs). Delete the empty `Source/Frontend_Archive`, `Modelers` and `Viewer`. Make the version agree: `pyproject.toml` says 0.1.0, `GitHub_Connector/settings.py` says 1.1.0. Do it in one commit, while no teammate has an open branch on those files (Human to coordinate). | Sonnet · Easy | W0-1, W0-6 (both may edit `docs/diagrams/init.md`) | `Source/`, `tests/`, `pyproject.toml`, the docs listed | `pytest` green; the wheel built by `pip wheel .` holds no top-level `models/`; `python -c "import drifter.models"` works. |
| W1-2 | **`.dockerignore`** (`docker/docker.md` R1). Record the build context size **before** adding the file, then after: `docker.md`'s 14 MB and "under 2 MB" were never measured. | Haiku · Easy | none | `.dockerignore` | Both sizes are written in this item; the context after is below 2 MB; `docker.md` checks 3 and 4 pass (no `__pycache__` or `.env` in the image). |
| W1-3 | **Reorder the Dockerfile** from least to most often changed (docker.md R2). | Haiku · Easy | W1-2 | `Dockerfile` | A one-line change in `Source/` rebuilds only from `COPY Source/`; `/system/health` still says `storage: volume` on Railway. |
| W1-4 | **Commit `/models` for this repository** (dogfooding, `mage_take.md` C5): `drifter init`, then a person corrects `ownership.json` and commits. | Sonnet · Easy, plus Human to review ownership | W1-1 (the rename changes every structural id), W1-5 (both are small; doing W1-5 first means `/models` is taken after the last pre-CI code change) | `models/` | `drifter check` exits 0 on the commit after. |
| W1-5 | **Our own architecture rule with import-linter (Q5b).** Add `[tool.importlinter]` to `pyproject.toml` with one `forbidden` contract: `drifter.models` must not import `GitHub_Connector`, `Frontend` or `Tester`. | Sonnet · Easy | W1-1 (same `pyproject.toml`, and the package name it names) | `pyproject.toml`, `requirements.txt` | `lint-imports` passes; a throwaway forbidden import makes it fail. |
| W1-6 | **CI pipeline and the drift tally. SUGGESTION (Q11).** See the detail below. This item owns the tally of red `drifter check` results; W4-4 only tells adopters to keep one. | Sonnet · Medium, plus Human for the GitHub settings | W1-4, W1-5 | `.github/workflows/ci.yml`, `pyproject.toml` (`[tool.ruff]`), files with ruff findings, `docs/tickets/drift-tally.md` | All the proofs in the detail below behave as stated. |

### W1-6 in detail: the CI suggestion

The team will decide how to do this. The direction agreed on 2026-11-05:

- **One workflow** on every pull request and on every push to `main`:
  - blocking: `pytest` (277 tests, about 2 minutes, so the whole suite fits at the PR and no timed sweep is needed), `ruff check` (fix or `noqa` the existing findings once, in one commit), `pip-audit`, `lint-imports` (W1-5);
  - coverage: report it only, with no minimum;
  - warning only: `drifter check` on our own code (`continue-on-error`). Exit 2 means "no verdict" and is never read as a pass. W4-2 later replaces this step with a call to the reusable workflow, so the step is defined once.
- **Least privilege:** the workflow declares `permissions: contents: read` and uses no secrets.
- **Branch protection on `main`** (Human): require the CI check, require one review, block direct pushes. This is the real gate. Railway deploys every push to `main`, so it is also what keeps untested code out of production. Also check whether Railway can wait for CI before it deploys.
- **GitHub settings** (Human): turn on secret scanning and Dependabot alerts.
- **The tally** (`mage_take.md` C8), in `docs/tickets/drift-tally.md`: name an owner, and add one row per red `drifter check` with the PR and one category:
  - true drift;
  - false alert;
  - accepted change;
  - **edited by a non-owner, approved by an owner** (the case `owner-approval.md` raised; if it dominates, revisit the ownership rule).
  
  A second column records whether the drift was **fixed in code or accepted with `drifter update`**. A very high acceptance rate suggests rubber-stamping (`mage_take.md` open question).
- **Promotion rule:** below 10 false alerts in 100 red checks, remove `continue-on-error`.
- **Proofs** (each is a throwaway PR, `mage_take.md` C1 to C5):
  - a PR that breaks one unit test turns red; a PR with no code change turns green;
  - a PR that adds an unused import turns red (ruff);
  - a PR that pins a dependency to a known-vulnerable version turns red (pip-audit);
  - a PR that adds an import between modules, without `drifter update`, shows drift in the step's log;
  - the CI log shows that `tests/connector/test_golden.py` ran and was not skipped.
- **Later:** `mypy`, `bandit`, a coverage floor, a weekly scheduled `pip-audit`.

---

## Wave 2: the engineering environment (slim MAGE, Q6)

Takes the parts of `ExampleRepoMAGE` that pay off with one or two agents at a time. The rest is Phase 6. W2-3, W2-4, W2-6 and W2-7 touch different files and can run in parallel as soon as W0-1 is done.

| ID | Item | Tier · Difficulty | Depends on | Touches | Done when |
|---|---|---|---|---|---|
| W2-1 | **`CLAUDE.md` as a numbered rule index.** Each rule is one sentence, says why, and names the check that enforces it, or says "guidance only". Numbers are never reused, and these numbers are the project's only list of rule IDs (no separate invariants file; see "Left out on purpose"). A rule earns a place only if it prevents a regression, cannot be read from the file being edited, and crosses files. <br>Must include: <br>• "Run `pytest` and `drifter check` before declaring a task done" (`mage_take.md` C9; enforced by W1-6); <br>• "Never edit a test or the spec to make it pass"; <br>• "A check may move to another stage, but is never deleted"; <br>• the build and test commands (`perspectives/mage-engineering-env.md` §12). Run them before writing them down: `pip install -e .` gives the `drifter` command, and the web service starts locally with the Dockerfile's `uvicorn` line. §12 left both unverified. <br>Move `AGENTS.md`'s house rules in; `AGENTS.md` becomes a one-line pointer, so the rules exist once. Starting point: `ExampleRepoMAGE/CLAUDE.md`. | Opus · Medium | W1-6 (so each rule can name its check) | `CLAUDE.md`, `AGENTS.md` | A fresh agent session cites a rule by number; both commands were run and work as written. |
| W2-2 | **Versioned git hooks** in `hooks/`, installed with `git config core.hooksPath hooks` by a setup script: <br>• `commit-msg`: subject of at most 50 characters, a body that says why, ends with `Fixes #n` or `Refs <epic>`; a commit that changes `/models` says why the drift was accepted (industry item 4). If a `Step: i/N` line is present, check its format only; never require it, because N changes during the work and many commits are not part of a brief (W2-4 owns the convention); <br>• `pre-push`: `ruff` and the fast tests. <br>Use the exact file names `commit-msg` and `pre-push`. `STRATEGY.md`'s `prepush.sh` would never run. Hooks must work in Git Bash on Windows. Local hooks are a convenience; CI (W1-6) is the control. | Sonnet · Medium | W1-6 (the ruff config), W2-4 (the `Step: i/N` format) | `hooks/`, `scripts/setup-hooks.sh` | A 60-character subject is refused; a malformed `Step:` line is refused; a commit without one is accepted; a push with a failing fast test is refused. |
| W2-3 | **`STRATEGY.md` as a real queue**: Now / deploy gates / near-term / long-term, pointing to this file. Fix the raw notes' errors ("less than 50 lines" means 50 characters; `prepush.sh` means `pre-push`). Starting point: `ExampleRepoMAGE/STRATEGY.md`. | Sonnet · Easy | W0-1 | `STRATEGY.md` | Every near-term item links to a W-item here or to an Epic. |
| W2-4 | **Templates** in `docs/templates/`, adapted from `ExampleRepoMAGE/docs/templates/`: <br>• **Epic**: each phase carries a tier and a difficulty like this file. Phase 1 of an Epic is always design, and a second Fable reviews it and refers what it cannot resolve to the human; <br>• **Design doc**, separate from the Epic: the Epic says what must change, the design doc says what must remain true (`mage-engineering-env.md` §3); <br>• **Brief**: names the target files, and defines the progress convention. The agent's first commit states the plan and lists the target files; each later commit carries `Step: i/N` (`STRATEGY.md`, `mage-engineering-env.md` §6); <br>• **Phase review**; <br>• **PHASE-DONE**: the checkpoint and Definition of Done for one phase; <br>• **Open questions** and **ruled decision**. <br>CONVERSION and PLAYBOOK are not part of this item (Phase 6). | Opus · Medium | W0-1 | `docs/templates/` | The first Epic opened from it (for example W3-5) passes its own review. |
| W2-5 | **Reorganize `docs/deviations/` (Q7).** The name clashes with the contract's "deviation 1/2" (§9). <br>• research (`perspectives/`, `language-engine/research-*`) → `docs/research/`; merge `mage-research.md` into `mage-engineering-env.md`; <br>• each proposal (docker, init, ownership, language-engine) → an Epic in `docs/active/<epic>/` when work on it starts; <br>• decisions (`language-engine/05-decisions-log.md`, `docs/adr/`) → `docs/decisions/`; <br>• this file moves with it. <br>Update `docs/README.md`, `CLAUDE.md` and `docs/agents/domain.md` (both point at `docs/adr/`) in the same change. Decide what happens to `docs/tickets/`. One docs-only change. | Opus · Medium | all of Wave 0 (they edit `docs/README.md` and this file), W2-1 (`CLAUDE.md`), W2-4 (`docs/templates/` and the Epic shape used by `docs/active/`) | `docs/` (moves), `docs/README.md`, `CLAUDE.md`, `docs/agents/domain.md` | Every file under `docs/` is in the docs map, and no link points to a moved path. |
| W2-6 | **Agent roles** in `.claude/agents/`, each with its model: planner (fable), design-reviewer (fable, never the author), implementer (opus), mechanic (sonnet), scout (haiku), auditor (opus, re-runs every gate at HEAD before an Epic closes). | Sonnet · Easy | W0-1 | `.claude/agents/` | Each role file names its model, its job and what it never does. |
| W2-7 | **Claude hooks that block**, in `.claude/settings.json`: a `PreToolUse` guard that refuses `git commit --no-verify`, `git push --force` and `git add -A`. Consider also refusing any `git push` without the user's OK, which enforces this project's "local only" rule. Optional, low value: a post-edit `ruff` hook (pre-push and CI already run ruff). Reminder-only hooks guarantee nothing, so they go to Phase 6. | Sonnet · Easy | W0-1 | `.claude/settings.json` | The guarded commands are refused in a test session. |
| W2-8 | **A narrow stale-docs check** (`mage_take.md` con 8, narrowed by review): <br>• a link checker over `docs/` (every relative link and every path in backticks that looks like a repo path exists); <br>• a few greps for known claims: the contract version is the same everywhere, and no doc calls an existing file "not yet written". <br>Runs as a test, so CI (W1-6) enforces it. Not a general "find stale docs" tool. | Sonnet · Easy | W2-5 (links must point at the new paths), W1-6 | `tests/docs/` | It fails on a planted broken link and on a planted wrong contract version, and passes on the real docs. |

---

## Wave 3: design refactors, in this order (Q9)

Start only after W1-1 (otherwise every refactor collides with the moved files) and W1-6 (so the gate checks each refactor). W3-1 to W3-5 all change `Source/drifter/check.py`, so they run one after the other; the order exists so that each step makes the next one smaller. W3-6 touches the deployment, not the core, and runs in its own lane; the one shared file is `api.py`, so W3-3 waits for W3-6. W3-7, the next step in that lane, is in Wave 4. W3-8 adds a new module and one CLI command and runs beside W3-2 onwards.

| Order | ID | Item | Tier · Difficulty | Depends on | Touches | Done when |
|---|---|---|---|---|---|---|
| 1 | W3-1 | **E**: add `scope.schema.json`; delete the hand-written `_scope_rule` and `_ownership_rule` checks that the schemas already make (`architecture-review.html` E, `init/init.md` problem 2). The model loader trusts validated input. *Why here:* self-contained, and every `/models` file then has a schema, which shrinks W3-4. | Sonnet · Easy | W1-1, W1-6 | `Source/drifter/models/scope.schema.json`, `check.py`, `Frontend/model_loader.py` | A malformed `scope.json` gives `INVALID_MODELS`; the two hand-written rules are gone; `pytest` green. |
| 2 | W3-2 | **D**: one git-output parser shared by `LocalReader` and `Comparison`, plus an in-memory reader for tests. Keep one real-git agreement test. *Why here:* W3-3 to W3-5 all change how the core reads; the in-memory reader lets their tests run without real git repos. | Opus · Medium | W3-1 | `check.py`, `GitHub_Connector/fetch.py`, a new git-format module, `tests/` | Both adapters use the one parser; the agreement test passes. |
| 3 | W3-3 | **B**: the models web page asks the core for "the models at a commit" through the reader interface, instead of re-implementing reading with weaker rules (no 1 MB limit, bad files silently dropped). Rename the page's "drift" chip, which means "changed since the parent" and clashes with `GLOSSARY.md`. *Why here:* adds "read at a commit" to the reader, which is easier after W3-2. | Opus · Medium | W3-2, W3-6 (both change `api.py`; W3-6 is short and starts earlier) | `check.py` (reader), `Frontend/model_drift.py`, `GitHub_Connector/api.py` | The route has its own test; `api.py` no longer imports from `Frontend` for reading models; the chip has a new name. |
| 4 | W3-4 | **A**: one list of model kinds (file, schema, element rule or not, its step in one check) that `answer`, `read_sources`, the loader and the seam test iterate over. The four-field answer is unchanged. *Why here:* today a kind is named in about 8 places. After this, W3-5, the language engine and `rules.json` each land in one place. | Opus · Hard | W3-3 | `check.py`, `GitHub_Connector/schemas.py`, `Frontend/model_loader.py`, `Frontend/model_viewer.py`, `tests/common/test_seam.py`, `Tester/unit_tests.py` | The dead branch at `check.py:113` is gone; the seam test reads the list instead of repeating `GENERATORS`; the answer bytes are unchanged (goldens). |
| 5 | W3-5 | **C, plus the W0-7 fix**: ownership becomes one module with `propose(history)` and `judge(rules, commits)`; the option ruled in W0-7 becomes a parameter of `judge`, and the ruling's answer to G4 (scope) is built here too. Write the W0-7 tests first. Before coding, Muhammad (ownership model) and Kaan (core) agree on merging code they each own (`docs/diagrams/model-seam.md`). Alternative: a small fix directly in `read_sources` right after W0-7, which this step then absorbs; it closes the hole sooner at the cost of some double work. | Opus · Medium, plus Human (owners agree) | W0-7, W3-4 | `drifter/models/ownership_model.py`, `check.py`, `docs/diagrams/comparison.md`, spec §3.2 | Every W0-7 test passes, including G4. |
| parallel | W3-6 | **Split the tester into its own Railway service**, from the same image, with the Compose file from `docker/docker.md` for local runs. Needs a new `Tester.app` and `SYSTEM_URL`. Use a **named** Compose volume for runs, not a bind-mounted folder: the app runs as uid 10001, which cannot write to a host folder on Linux. Put **no `VOLUME` line in the Dockerfile**; the volume belongs to Compose and Railway. | Sonnet · Medium, plus Human (second Railway service) | W1-3 | `compose.yaml`, `Source/Tester/app.py`, `Source/Tester/` wiring, `GitHub_Connector/api.py` (drops `include_router(tester.router)`, line 212), Railway settings | `docker compose up` starts both; the tester reaches the system by name; results survive `docker compose down`. |
| beside 2 to 5 | W3-8 | **`drifter validate`** (`init/init.md` fix 3): checks `/models` locally without a full check, so format errors are found before pushing. Runs the same schema checks as `read_sources`, plus: <br>• errors: a malformed owner email; a `scope.json` or `ownership.json` glob that matches no file; <br>• warning only: an ownership rule that never applies because an earlier rule already matches the same files (the checker uses first match; an overlap can be intentional). <br>`drifter check`'s answer does not change: these extra checks live in `validate` only. Making them part of `check` would change the answer (⚠ CONTRACT CHANGE) and is not this item. | Sonnet · Easy | W3-1 (the scope schema) | `Source/drifter/validate.py` (new), one command in `cli.py`, `tests/drifter/` | Each planted error gives a non-zero exit with the file and the problem; a planted shadowed rule gives a warning and exit 0. |

---

## Wave 4: the spec §6.2 deliverable

The core of Phase 5 (see "How to read"). The first release tag should come after W1-1 (package name) and W3-5 (so adopters do not get the self-grant hole). If the release must come earlier, decide that explicitly.

W3-7 sits here because it waits for W4-5. It keeps its ID, since IDs never change.

| ID | Item | Tier · Difficulty | Depends on | Touches | Done when |
|---|---|---|---|---|---|
| W4-1 | **Tagged release**: one version number, `pip install git+https://github.com/<owner>/DocumentationModelDrifter@vX.Y.Z` gives the `drifter` command. The tag is the tool version. No PyPI (spec §8.1). | Sonnet · Medium, plus Human to tag (a remote write) | W1-1, W1-6, W3-5, W4-3 (the reporter ships in the first release) | `pyproject.toml` version, release notes | A clean virtualenv installs from the tag and `drifter check` runs on a fixture checkout. |
| W4-2 | **Reusable workflow** (`on: workflow_call`) at the same tag: checkout with full history (ownership reads base..head); install drifter at the tag; `drifter check` with the PR base; upload the JSON answer as an artifact (90 days by default); write the W4-3 summary to the job summary; an `advisory` input (warn only); exit 2 is never green. **Least privilege:** declare `permissions: contents: read`, need no token beyond the default one, and never pass secrets into the check; adopters run this with their own tokens. Then switch W1-6's `drifter check` step to call it. | Opus · Medium | W4-1 | `.github/workflows/drifter.yml`, `.github/workflows/ci.yml` (the one step) | An adopter adds one `uses:` line and gets a check on every push and PR; the workflow file declares no write permission. |
| W4-3 | **Reporter**: one function from the answer to GitHub annotations plus a markdown job summary, kept out of `check.py`. Consider a module-level summary for large diffs before changing the model grain (industry items 6 and 7). | Sonnet · Easy | W1-1, W3-8 (both add to `cli.py`) | `Source/drifter/report.py` (new), one flag in `cli.py` | A drifted PR shows the changed elements in the summary. |
| W4-4 | **Adopter rollout docs** (REQ-03): how an adopting team runs the check advisory first and when to make it required (keep a tally like W1-6's; below 10 false alerts in 100). Also: <br>• Q4's S4 (`CODEOWNERS` plus branch protection) as advice; <br>• author-email evidence is advisory, because anyone can set a commit email; <br>• **migration note**: `drifter init --force` replaces a hand-corrected `ownership.json`. To change scope on a repository that already has `/models`, edit `scope.json` and run `drifter update` instead (`language-engine/06-init.md`). | Haiku · Easy, plus Human to approve | W4-2 (the docs describe its inputs) | `docs/adopting.md` (new), `README.md` link | The docs cover the four points above and a person outside the team can follow them. |
| W4-5 | **T-22 and T-23** (contract §4: review decisions, read-only analysis): decide how each is shown in Phase 5 (automated vs inspection) and implement it in the tester. Evidence for AC-04, AC-05, AC-06 (artifacts) and AC-09. | Opus · Unknown | W3-6 (both change `Source/Tester/`) | `Source/Tester/` | Both tests no longer report `skip`, or the contract says why they stay manual. |
| W4-6 | **The demo** (spec §6.2): on a public repository, push a drifting change and see a red check; commit updated `/models` and see a green one; open the run's artifact and find, through `git log -- models/`, who accepted the change. | Human · Medium, plus Sonnet to script it | W4-2, W4-3, W4-4 | the demo repository, a script in `scripts/` | It runs end to end in front of someone else. |
| W4-7 | **`CODEOWNERS` matches `ownership.json`.** Only if W0-7 adopts S4. Commit `CODEOWNERS` for `/models/` in this repo, and add a test that every owner in `ownership.json` appears in `CODEOWNERS` and the reverse. Test, do not generate: `CODEOWNERS` accepts emails only when they belong to a GitHub account with access, and commit emails often are not linked, so the test reports owner emails GitHub cannot resolve instead of guessing a mapping. | Sonnet · Easy, plus Human (branch protection: require code-owner review) | W0-7 (S4 adopted), W1-4, W1-6 | `.github/CODEOWNERS`, `tests/` | The test fails when an owner is added to one file only, and passes on the committed pair. |
| W3-7 | **Storage bucket for results and a shared concurrency limit** (docker.md "what would make the backend scale", steps 1 and 2). Only `runs.py` changes for the bucket. Keep its interface "save bytes by id, load bytes by id". The 2-check limit and the single test session move out of the process. Add a MinIO service to the Compose file as the local stand-in for the bucket. Step 3 (several copies) is Phase 6. Last in the Docker and tester lane. | Opus · Hard (the shared limit needs a shared store: Unknown), plus Human (create the bucket and credentials on Railway) | W3-6 (the Compose file), W4-5 (both change `Source/Tester/`; the test session moves here) | `GitHub_Connector/runs.py`, `GitHub_Connector/analysis.py` (the 2-check limit), the test-session code in `Source/Tester/`, `compose.yaml` | A result saved before the switch comes back byte for byte after it; the limit holds across two processes. |

---

## Wave 5: later in Phase 5, the contract changes

Agreed for Phase 5 (Q3, Q5), but not as the first change. Each item below that is marked ⚠ needs Team 16's agreement and a contract version bump.

| ID | Item | Tier · Difficulty | Depends on | Touches | Notes |
|---|---|---|---|---|---|
| W5-1 | **Rebuild the lost language-engine evidence.** The prototypes, `python.scm`, the 614-of-614 Python comparison and the benchmark scripts lived in a session scratchpad that no longer exists (`language-engine/05-decisions-log.md`, "Evidence and prototypes"). Commit the rebuilt prototype into the repo this time. | Opus · Medium | none | `research/language-engine-prototype/` (new) | Without it, decision D1 rests on evidence nobody can rerun. |
| W5-2 | **F**: parse each file once and give the generators parsed facts. **This is the same design as `language-engine/final_templates.md`'s `extract(files) -> Facts`.** Do it once, as the language engine's step-d end state, not separately. It reopens decisions D9/D10 in `docs/diagrams/model-seam.md` (`generate_x(files: dict[str, str])`), so the model owners must agree. | Fable to plan, Opus to build · Hard | W3-4, W5-1 | `Source/drifter/models/`, `check.py`, `docs/diagrams/model-seam.md` | `architecture-review.html` calls F speculative; the language-engine plan builds it anyway. Settle that in the plan. |
| W5-3 | **Multi-language engine** (`language-engine/`), in their four language waves; Python steps a to d. <br>**Decide first:** O1 duplicate ids (blocks waves 2 and 3); O2 the "partly read" list (⚠ CONTRACT CHANGE); O3 no import edges for C#, Swift and Go (a schema change); O4 behavioral for new languages; **O5 Python edges on the template (the gate of step b)**; **D6 Elixir, Haskell, Julia and Zig** (in or out). <br>**Plan input:** `05-decisions-log.md`, "Other suggestions" 1 to 6 and "C and C++". One of them can change the wave order and must be tested before the waves are fixed: TypeScript overloads are body-less signatures, so capturing `method_signature` only inside interfaces may remove its duplicate ids and move TypeScript to wave 1. <br>**Also changes:** spec §2.2 "Python source only"; `requirements.txt` gains pinned tree-sitter wheels, which affects the Docker image and `pip-audit`; only a new `drifter init` takes the new default scope; "pinned CPython ast" in `docs/diagrams/one-check.md`, `docs/diagrams/init.md` and `docs/base/overview_phase4.html`. | Fable to plan, Opus to build · Hard / Unknown | W5-1, W5-2, W3-4 | `Source/drifter/models/` (engine, `languages.toml`, `queries/`), `requirements.txt`, the docs listed | ⚠ CONTRACT CHANGE (O2) and a spec change. **Done when** (per language and per Python step): the five guards pass (vocabulary, conformance, coverage, reference corpus, goldens), and each step a to d leaves a Python-only repository's output byte-identical. |
| W5-4 | **Product `models/rules.json` (Q5a)**: authored "module X must not import Y" rules checked against the structural edges. <br>**Decide first:** <br>• write it, or run import-linter on the target repo (the industry doc's open question); <br>• where a rule violation goes: a new `rules` list (as `industry-architecture-research.md` draws it) or the existing lists (as `architecture-review.html` requires). <br>**In the design:** <br>• "may" semantics: a missing allowed edge is not a violation (industry item 3); <br>• modules that match no rule are reported as "unmapped", so a reviewer decides instead of accepting them silently (industry item 5). <br>Read `rules.json` at the base, like ownership. A known-violations list and a stale-rule alert are later (see "Later ideas"). | Fable to plan, Opus to build · Hard | W3-4, W3-5 | `Source/drifter/`, `models/` schema, spec §3.2, contract | ⚠ CONTRACT CHANGE: a fifth `/models` file, the answer shape and probably T-33. |
| W5-6 | **Report the Kotlin grammar gap upstream** (`@Synchronized set(value)`; `05-decisions-log.md` suggestion 4). A public action: only after the user's explicit OK. | Human · Easy | none | none in this repo | The issue link is recorded in `05-decisions-log.md`. |

---

## Not yet discussed: needs a decision before it gets a wave

These come from the deviations docs but were not part of the 2026-11-05 session. Each row needs a ruling; once ruled, it moves into a wave with its own ID.

| ID | Item | Source | Tier · Difficulty | Depends on |
|---|---|---|---|---|
| N1 | Run the Risk 1 (noise) and Risk 2 (behavioral coverage) experiments and report them with counts, method and limits. The behavioral miner found 0 states on this repository. | spec §9.1, `mage_take.md` suggestion 5 | Opus · Medium | none |
| N2 | **Rule on the behavioral model.** A model with 0 states always passes, so the check is green without checking anything. Options: keep the miner as it is; drop it; or turn it into an authored state model checked against mined transitions or test traces. | `mage_take.md` suggestion 5, industry finding 9 and open questions, `mage-alignment.html` §3.3 | Fable · Hard, plus Human to rule | N1 (Risk 2 result) |
| N3 | Re-decide the structural grain. Concrete options: module, class or function level; drop `params` and `decorators`; leave out private symbols; make finer grain opt-in through `scope.json`. A grain change is a schema version bump and changes every committed `structural.json`. | `mage_take.md` suggestion 4, industry item 7 | Fable · Hard | W1-6 (the tally needs real data first) |
| N4 | Make ids stable across file moves (a moved file shows up as REMOVED plus ADDED today). | industry finding 4 | Fable · Hard | N3 (the grain decides what an id is) |
| N5 | Record the generator version beside `schema_version`, so a tool upgrade is not read as code drift. | industry "Later" | Sonnet · Easy | none |
| N6 | Measure the factory: cost and latency of accepted changes, reverts, post-deploy failures (beyond the W1-6 tally). | `mage-engineering-env.md` §10 | Human · Easy | W1-6 |

**Later ideas** (too early even to discuss; listed so they are not lost): an LLM drafts `rules.json` and a person commits it; an ownership signal from files that change together; a known-violations list and a stale-rule alert for `rules.json`; for the language engine, a process pool, a persistent facts cache and a content regex to tell `.m` files apart; smarter import resolution (tsconfig `paths`), React `component` facts, and Vue or Svelte templates.

---

## Phase 6: added later, each when its signal appears

Skipped from `ExampleRepoMAGE` on purpose (Q6). They pay off when many agents land work in parallel. Davis himself warns against "the tower of governance".

| Item | Signal that makes it worth doing | Starting point |
|---|---|---|
| Timed validation sweep over `main`, with an alert and a fail-closed dispatch gate | The suite gets slow enough (well past today's 2 minutes) that waiting for it at the PR becomes the bottleneck | `ExampleRepoMAGE/.github/workflows/validation-sweep.yml`, ADR 0002 |
| Merge train | Several agent branches are ready to land at once and conflict | ADR 0001 |
| Brief lint as a pre-dispatch gate (the only lifecycle hook the lecture counts as a control) | Agents are dispatched often enough that a malformed brief slips through | `ExampleRepoMAGE/bin/mage` (`brief lint`), `docs/templates/BRIEF.md` |
| Agent registry, tombstones and recovery playbook (with the PLAYBOOK template) | Agents die or are compacted mid-Epic and work gets lost | `docs/state/registry/`, `docs/operations/playbooks/agent-died.md`, `docs/templates/PLAYBOOK.md` |
| `docs/state/`: work items, orchestrator log, hand-off | An orchestrator session runs long enough to lose state at compaction | `docs/state/WORK-ITEMS.md` |
| Reminder hooks: `SessionStart`, `SubagentStop`, `PreCompact`, the 30-minute reflection | Agents repeatedly skip a procedure that a reminder would catch | `.claude/hooks/` |
| A project skill, for example "accept drift" (run `update`, write why in the commit) | The same accept-drift steps keep being repeated by hand | `ExampleRepoMAGE/.claude/skills/` |
| `bin/mage` CLI with `query-repo` and `constraints-for` (context injection) | Agents keep rediscovering the same rules. drifter's own models could answer `query-repo` | `ExampleRepoMAGE/bin/mage` |
| Governance conversion log (with the CONVERSION template), control catalogue and daily review | Checks pile up and start to overlap or go stale | `docs/governance/`, `docs/operations/daily-review.md`, `docs/templates/CONVERSION.md` |
| Staged deploy (staging, canary, smoke, promote) | A bad deploy reaches users despite CI | `ExampleRepoMAGE/.github/workflows/deploy.yml` |
| Several backend copies (`docker.md` step 3) | The hosted service needs zero-downtime deploys, or more than 2 checks at once. Needs W3-7 first | `docker/docker.md`, "What would make the backend scale" |
| The frontend as its own service or static host | The frontend grows into its own app: a build step, a framework, its own release cycle | `docker/docker.md`, "Recommendation" |

## Left out on purpose

Each of these was considered and turned down. Reopen one only with a new reason.

| Item | Why it is left out | Decided by |
|---|---|---|
| A database or ORM | Results stay write-once files; W3-7 keeps `runs.py`'s save/load-by-id interface | the user (Q12) |
| A pip cache mount in the Dockerfile | Speeds up rebuilds only after a dependency change, and Railway needs a service-specific cache id | `docker/docker.md` |
| A multi-stage Docker build | Gives a smaller image only if build tools are needed at install time; none are | `docker/docker.md` |
| Leaving `tests/` out of the image | The `/tester` page runs them, so they must stay in the image | `docker/docker.md` |
| A separate invariants file (`docs/invariants/`) | W2-1's numbered rules already give stable IDs; a second list would drift away from the first | review, 2026-11-05 |
| `owner-approval.md` Option 2 (read PR approvals from the GitHub API) | Puts the network inside the check (REQ-07); see W0-7 | W0-7 |
| Generating `CODEOWNERS` from `ownership.json` | Commit emails often do not resolve to GitHub accounts; W4-7 tests that the two match instead | review, 2026-11-05 |

---

## Appendix: review of `docs/deviations/`

Each document was judged on four questions: is it correct, is it sound, is it worth doing, and does it repeat or contradict another document.

### Per document

| Document | Verdict | Problems found |
|---|---|---|
| `docker/docker.md` | Correct and proportionate. R1 and R2 are standard and safe. The analysis of when to split containers is sound. | Context sizes (14 MB, under 2 MB) are not measured (W1-2 measures them). The Compose sketch needs `Tester.app`, which does not exist (it says so). |
| `init/init.md` | Problem 1 is **correct, reproduced**. Problem 2 is correct (no `scope.schema.json`). | Fix 1 is incomplete: it misses gaps G1 to G3, and covers G4 (scope) only in passing (W0-7). Line references move after W1-1. |
| `ownership/owner-approval.md` | The problem is real: authorship is not approval. Option 1 is sound. | Option 2 contradicts REQ-07 and `tracker-gaps.md` row 7 (CLI = `/analyze`). Option 1 lists owners twice (`ownership.json` and `CODEOWNERS`; W4-7). |
| `perspectives/mage-engineering-env.md` | Careful and well sourced; separates the lecture from the notes. | §13 is a second to-do list, overlapping `mage_take.md` C1 to C9; both are now replaced by this file. §12's "pass status not checked" is now checked: 277 pass. §12's install and server commands are still unverified (W2-1). |
| `perspectives/mage_take.md` | Sound and fair (grade B). Its facts in con 8 are confirmed. | Its to-do lists are replaced by this file. C7's base-rules fix has the same gaps G1 to G4. |
| `perspectives/mage-research.md` | Good source map. | Mostly repeats `mage-engineering-env.md` (findings 7, 11 and 13 appear in both with the same lecture notes). Merged in W2-5. |
| `perspectives/industry-architecture-research.md` | The strongest outside evidence. Honest labels; admits the evidence is thin. | Its pipeline adds `rules[]` to the answer, which contradicts `architecture-review.html` A and the spec's four-field answer. Putting `rules.json` in `/models` contradicts the spec's "four files". Both are now W5-4 decisions. |
| `perspectives/architecture-review.html` | Concrete and well targeted. A and B are the most useful. | F duplicates the language engine's end state (W5-2). C needs the two code owners to agree (W3-5). |
| `perspectives/mage-alignment.html` | A good visual explainer of MAGE chapter 3. | Restates `mage_take.md`. Raises one unverified edge: squash merges and per-commit authors (W0-7). |
| `language-engine/` (README, 01 to 06, `final_templates.md`, research, `guide.html`) | Thorough research and a sound engine design. | `05-decisions-log.md` D1 says "decided"; `mage_take.md` says hold. Resolved by Q3: Phase 5, later wave. 02's per-language adapters are replaced by 04 but still read as current (W2-5). The evidence is lost (W5-1). It is a contract change (O2) and a spec change, which the README states only indirectly. O5 and D6 were missing from the earlier version of this file (now in W5-3). |
| `STRATEGY.md` (root) | Raw lecture notes, not a queue. | "less than 50 lines" should be 50 characters; `prepush.sh` should be `pre-push`. Rewritten in W2-3. Its "name the target files in the first commit, step i/N" is now the brief convention (W2-4). |

### Repeated in more than one place

| Topic | Where | Resolution |
|---|---|---|
| The ownership self-grant fix | `init/init.md`, `ownership/owner-approval.md`, `mage_take.md` (con 5, C7), `industry-architecture-research.md` (item 2), `architecture-review.html` (C) | One decision (W0-7), one build (W3-5) |
| The CI plan | `mage_take.md` C1 to C9, `mage-engineering-env.md` §13, `mage-alignment.html` §3.5 | One suggestion (W1-6); the C9 rule is in W2-1 |
| The red-check tally | `mage_take.md` C8, `mage-engineering-env.md` §10, the old W4-4 | Owned by W1-6; W4-4 only tells adopters to keep their own |
| Explaining MAGE | `mage-engineering-env.md`, `mage-research.md`, `mage_take.md`, `mage-alignment.html`, `ExampleRepoMAGE/README.md` | Merge the two research files in W2-5; keep the HTML as the visual |
| Phase 5 to-do lists | `mage_take.md`, `mage-engineering-env.md` §13, `STRATEGY.md` | This file. `STRATEGY.md` points here after W2-3 |
| `CODEOWNERS` | `init/init.md` fix 2, `owner-approval.md` Option 1, `mage_take.md` C7 and suggestion 1 | Q4 option S4 (W0-7); the match test is W4-7 |

### Contradictions

| Between | Contradiction | Settled by |
|---|---|---|
| `language-engine/05-decisions-log.md` D1 and `mage_take.md` con 9 | Build 14 languages now, or hold until Python shows a return | Q3: Phase 5, later wave (W5-3) |
| `industry-architecture-research.md` and `architecture-review.html` A | A rule violation adds a `rules[]` list to the answer, or the answer stays as the contract fixes it | Open, W5-4 |
| `industry-architecture-research.md` item 3 and spec §3.2 | `models/rules.json` as a fifth file, or "/models holds four files" | Open, W5-4 (contract and spec change) |
| `architecture-review.html` F and `language-engine/final_templates.md` | F is speculative, or the language engine's end state is built on it | W5-2: build it once, as part of the language engine |
| `ownership/owner-approval.md` Option 2 and REQ-07 / `tracker-gaps.md` row 7 | Network-dependent verdicts, or the same answer from the CLI and `/analyze` | Rejected (W0-7) |
| The deviations' "judge at the base" and golden case L0 | Strict base rules fail the first commit with `/models` | Gap G1 (W0-7) |
| `docker.md` "keep one container in Phase 5" and Q9 | The tester split was a signal-triggered item | The user put it in Phase 5 (W3-6) |
| `STRATEGY.md` "the agent names its files, step 3/k" and a strict `commit-msg` hook | Enforce step counts on every commit, or only in briefs | W2-4 owns the convention; W2-2 checks the format only when present |
| The folder name `docs/deviations` and contract §9 | "Deviation" means two different things | W2-5 |

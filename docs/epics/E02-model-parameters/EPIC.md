# E02: Model generation parameters, and verbosity as the first one

Status: draft · Owner: Kaan

W-row: N7 in `docs/state/WORK-ITEMS.md` · Branch: `E02-model-parameters`

## Goal

`models/scope.json` gains one key, `verbosity`, an integer from 1 to 4 that says how much of the
code the structural model describes: level 1 is the packages and the imports between them, level 4
is every function and method with its signature. Level 4 is the default and is byte-identical to
what the generators write today, so a repository that commits no key sees no change at all.
`drifter init --verbosity` sets the level before the first model is generated, and a later change
is a hand edit of `scope.json` plus `drifter update`, which regenerates at the new level and so
redefines the baseline. The models page itself gains a parameters panel: four stops that reload the
page at any level, the reader's choice remembered in their own browser, and a note saying which
level is drawn and which level the repository committed. The design, and what is deliberately left
out of it, is `DESIGN.md`, beside this file.

Who needs it: a reader of a large repository, for whom level 4 is a wall of methods, and a team
that wants its committed models to describe architecture rather than signatures. It is the "size
slider" of the human's request of 2026-11-22.

**This Epic is a direction change and needs the human's word twice before any code.** `STRATEGY.md`
reserves direction to the team, the queue's Next action is build order step 0.6b, and there is no
build-order step for this work. It also answers part of row N3, the structural grain, which is open
and is the human's call. Both are rows in `docs/decisions/OPEN-DECISIONS.md` as of this draft, and
Done criterion 3 cannot pass until they are ruled and closed.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/model-seam.md`, changes (the generator contract gains a keyword argument,
  and one sentence says a parameter is committed in `/models` and never passed from a request).
  `docs/diagrams/models-folder.md`, changes (the `scope.json` box gains the key and the ladder).
  `docs/diagrams/dependency.md`, reads (no import crosses a new boundary; the panel is inside
  `Frontend`, which already renders this page). `docs/diagrams/behavioral-model.md`, reads
  (unchanged: behavioral has no ladder in this Epic).
- Rulings: none. `docs/decisions/RULED/` holds only its README, so no ruling exists to read. This
  Epic needs two written, for N3 and for E02 itself.
- Invariants: INV-1, reads (its wording already covers a parameter committed in `/models`, and the
  default keeps today's bytes). INV-2, reads (its wording already covers the scope rules, so
  verbosity inherits gap G4 of W0-7 and whichever fix closes it). INV-3, reads (the import
  contracts are unchanged).
- Rows: W3-1, which adds `scope.schema.json` and deletes `_scope_rule`, so it would own this key's
  validation. W0-7, whose ruling must name verbosity. N3, the structural grain, which this Epic
  partly answers. N2, the behavioral grain, which is why behavioral gets no ladder here.

## Steps

One commit per step, made after the step's check passes. No step starts before RATIFY.

**Revised on 2026-11-22, a third time, after steps 1 to 7 were committed and the system was driven
by hand.** Three steps are added, 8 to 10, and the count goes from seven to ten. Steps 8 and 9
close what driving it found: changing the level took two commits, and the hosted path had no test
below level 4. Step 10 is the human's ask of the same day, to separate the reusable parameter seam
from verbosity's own part of it. The commits of steps 1 to 7 carry the trailers `Step: 1/7` to
`Step: 7/7`, from when there were seven.

**Revised on 2026-11-22, after the first review returned REVISE.** Its three blocking findings
were each checked against the disk and each held. The second generation site,
`Source/Frontend/model_drift.py:40-52`, is now named in step 3 and covered by step 6, which also
passes the same level to both `snapshot` calls so the drift chip compares like with like. Step 4's
`generate_models` parameter is keyword with a default, because
`Source/GitHub_Connector/analysis.py:132` calls it with one argument for `POST /system/generate`,
and that step's check now runs `tests/connector` to prove it. Step 6 also rewords the module
comment that says the page runs no scripts, step 7 adds the Next action line, Done criterion 9
gains the chip case, and the stale citations are corrected here and in `DESIGN.md`. The step count
is unchanged at seven.

### Step 1/7: Track the console's own tests

- Files: `tests/frontend/test_models_view.py` and `tests/frontend/test_behavioral_view.py`, both
  untracked on `main` today and both covering the page this Epic changes; `tests/frontend/__pycache__`
  stays ignored
- Check: `git status --porcelain tests/frontend` → prints nothing
- Trailer: `Step: 1/7`

The 26 tests in these two files are the models page's only coverage, and three Done criteria below
run them. An Epic cannot rest on files that are not in the repository.

### Step 2/7: Add the ladder to the structural generator

- Files: `Source/models/structural_model.py` (the four levels as named constants, and
  `generate_structural(files, verbosity=FULL)`, which filters nodes by kind, edges by kind, and
  drops `params`, `decorators` and `is_async` below level 4); `tests/structural/test_verbosity.py`
  (new)
- Check: `pytest tests/structural -q` → passes, including the new case asserting that
  `write_model(generate_structural(CODE))` equals `write_model(generate_structural(CODE, verbosity=4))`
  byte for byte, and the case asserting each level's elements are a subset of the level above
- Trailer: `Step: 2/7`

Written failing first: the subset case and the byte-identity case both fail against the current
signature, which takes no keyword. Behavioral is untouched, so `generate_behavioral` keeps its one
argument and the seam gains the argument on one generator only, as `DESIGN.md` states.

### Step 3/7: Read the level from the committed scope, at both of the core's generation sites

- Files: `Source/drifter/check.py` (`generate_one(name, files, verbosity)` beside `GENERATORS`,
  holding the one fact that only structural has a ladder, so no site repeats it; `GENERATORS`
  retyped `dict[str, Callable[..., dict]]`, its entries no longer sharing one signature;
  `_regenerate(files, verbosity)` calls `generate_one`; `model_differences` calls it too, with the
  level from `sources.models["scope.json"]`, which `read_sources` has already parsed;
  `regenerate_models` reads the level from the scope it already reads; `DEFAULT_SCOPE` carries
  `verbosity`; `_scope_rule` rejects anything that is not an integer from 1 to 4 with
  `INVALID_MODELS`); `tests/drifter/test_cli.py` (a committed `scope.json` at level 1 gives a
  structural model of modules and imports only, and a `check` against it is aligned rather than
  reporting every dropped element as `REMOVED`; a level of 0, of 5, of `true` and of "high" each
  give `INVALID_MODELS`; `update` at a changed level rewrites the models and a `check` straight
  after it is aligned)
- Check: `pytest tests/drifter tests/drift tests/common tests/connector -q` → passes
- Trailer: `Step: 3/7`

`Sources` gains no field: the committed scope is already in `sources.models`. The last test is the
re-baseline the human described on 2026-11-22, and it needs no new code path: `drifter update`
already regenerates from the scope committed at the commit, so the models it writes are the new
baseline. Validation is inline because `scope.json` has no schema yet; if W3-1 lands first, this
step adds the key to `scope.schema.json` instead and the check command is unchanged.

There is no single choke point, and this step no longer claims one. The core generates a model in
two places, `_regenerate` and `model_differences` (in `Source/drifter/check.py`, which never calls
`_regenerate`), and the console's page in a third, `snapshot` (in
`Source/Frontend/model_drift.py`), which step 6 covers. `model_differences` is the site that
matters most: miss it and `drifter check` regenerates at level 4 against a level-1 committed model
and reports every element the level drops as `REMOVED`, which is why this step's tests assert an
aligned check at level 1 and not only a trimmed model.

### Step 4/7: Set the level before the first model exists

- Files: `Source/drifter/cli.py` (`init` gains `--verbosity`, an integer from 1 to 4, default 4);
  `Source/drifter/check.py` (`generate_models(reader, verbosity=FULL)` writes the level into the
  `scope.json` it writes and generates at it); `tests/drifter/test_cli.py` (`init --verbosity 1`
  writes `verbosity: 1` into `scope.json` and a `structural.json` of modules and imports only, and
  a `check` straight after it is aligned)
- Check: `pytest tests/drifter tests/connector -q` → passes
- Trailer: `Step: 4/7`

This is the human's "the change in verbosity happens before the initial model is generated": the
first baseline is at the chosen level, not at level 4 and then lowered.

The parameter is keyword with a default, as step 2's are, because `generate_models` has a second
caller: `Source/GitHub_Connector/analysis.py:132` calls `check.generate_models(cmp)` with one
argument, for `POST /system/generate`. It needs no edit, and this step's check runs
`tests/connector` to prove it.

### Step 5/7: Prove the goldens and the contract are untouched

- Files: none. A verification step with no edit; if it fails, the Epic is wrong and goes back to
  draft
- Check: `pytest tests/connector tests/behavioral -q` → passes, and
  `git diff --stat main...HEAD -- docs/contract/` → prints nothing
- Trailer: `Step: 5/7`

A step that changes nothing is here on purpose: the whole claim that this feature is safe rests on
level 4 being today's bytes, and that claim is checked before the page is touched. It has no commit
of its own if nothing changed; its result is recorded in this file instead.

**Result, 2026-11-22, at the commit of step 4.** It passed, and nothing changed.
`pytest tests/connector tests/behavioral -q` gives 82 passed, the eight golden cases of
`tests/connector/test_golden.py` among them, with one failure that is not this Epic's:
`tests/connector/test_fetch.py::test_a_skipped_batch_fails_at_once_instead_of_fetching_lazily`
fails on `main` as well, in this environment only, where Apple Git 2.39.5 raises
`CalledProcessError` from `git cat-file --batch` on a blobless clone instead of the `AnalysisError`
the test expects. CI runs ubuntu-latest's git, where it passes.
`git diff --stat main...HEAD -- docs/contract/` prints nothing, and so does the same command for
`example-models/`. The four files changed under `Source/` are `drifter/check.py`, `drifter/cli.py`,
`models/structural_model.py` and `models/structural.schema.json`.

One thing the step found that the plan did not foresee, fixed in step 3's commit:
`models/structural.schema.json` made `async`, `decorators` and `params` **required** on a function
node while `plainNode`'s `kind` enum allowed only `class` and `module`, so a level-3 model, which
names members without their signatures, matched neither variant and was refused as
`INVALID_MODELS`. Levels 1 and 2 passed, having no function nodes, and level 4 passed, being
today's shape; level 3 alone was broken. The schema gains a third variant, `memberNode`, which
keeps level 4 validated as strictly as before and is purely additive, so `schema_version` stays 1
and no committed model moves.

### Step 6/7: Put the panel on the page, and the level on the route

- Files: `Source/Frontend/model_drift.py` (`snapshot(reader, commit, verbosity=None)` passes the
  level to the structural generator, reading the commit's own `scope.json` through `_scope` when
  none is given); `Source/GitHub_Connector/api.py` (`models_view` gains
  `verbosity: int | None = None`, validated 1 to 4, passes the **same** level to both `snapshot`
  calls, at `:198` and `:201`, and hands `render` the route the page was served from so the panel's
  form has somewhere to submit, plus the committed level so the page can name both);
  `Source/Frontend/model_viewer.py` (the panel above the three model panels: a GET form with four
  radio stops, `repository` and `commit_id` as hidden inputs, read-only when there is no route; one
  note beside `_provenance` and `_compared` saying which level is drawn, which the repository
  commits, and that the drift chips compare that level with itself; a few lines of script that
  remember the stop in `localStorage`, in try and catch; the module comment at `:5`, "no server, no
  scripts, no network", reworded to what is then true); `Source/Frontend/app.css` (the panel's
  styles); `tests/frontend/test_models_view.py` (a request at level 1 draws packages and no
  classes; a request with no level draws what it draws today; a request at level 9 gives 422; the
  note names both levels when they differ and is absent when they agree; the standalone render has
  no form and says how to change the level; a preview of a repository whose two commits differ
  only below the previewed level reports no drift, which is the two snapshots taking the same
  level)
- Check: `pytest tests/frontend -q` → passes
- Trailer: `Step: 6/7`

The panel is on the page, by the human's instruction of 2026-11-22, so `Source/Frontend/index.html`
does not change: the console frames the page and the page carries its own control. The form works
with no JavaScript; only the memory needs the page's first script, which `DESIGN.md` records as a
property knowingly spent. The route stays out of the OpenAPI document, so this is not a contract
change and Team 16 agrees to nothing.

### Step 7/7: Update the models, the spec and the docs map

- Files: `docs/diagrams/model-seam.md` (the generator contract line, and one sentence that a
  parameter is committed in `/models` and never passed from a request); `docs/diagrams/models-folder.md`
  (the `scope.json` box gains `verbosity` and the ladder); `docs/base/structure.md` (line 4, the
  signature); `docs/base/specifications.md` (line 261, what `scope.json` holds; the sentence at
  lines 263 to 264 already says what an edit without regenerating does and is left as it is);
  `docs/README.md` (the lines for the two models); `docs/invariants/INVARIANTS.md` (INV-2's check
  column names verbosity among what the W0-7 ruling must cover); `docs/state/WORK-ITEMS.md` (the
  N7 row at line 240, the W0-7 row gaining verbosity under gap G4, and the Next action line 13,
  "Drafted, waiting on the human … No code", which RATIFY and this build make untrue)
- Check: `git grep -c "verbosity" -- docs/diagrams/model-seam.md docs/diagrams/models-folder.md docs/base/structure.md docs/base/specifications.md`
  → each of the four files prints 1 or more
- Trailer: `Step: 7/7`

### Step 8/10: Give `drifter update` the level, so changing it takes one commit

- Files: `Source/drifter/cli.py` (`update` gains `--verbosity`, the same choices as `init`'s and no
  default, so the flag alone decides whether the level changes; its module comment says `update`
  writes `scope.json` when and only when the flag is given); `Source/drifter/check.py`
  (`regenerate_models(reader, verbosity=None)` returns the rewritten `scope.json` beside the two
  models when a level is given, and only the two models otherwise); `tests/drifter/test_cli.py`
  (`update --verbosity 1` on a level-4 repository writes the key and regenerates at it, and a
  `check` on the single commit that carries both is aligned; `update` with no flag still leaves
  `scope.json` byte-identical)
- Check: `pytest tests/drifter -q` → passes
- Trailer: `Step: 8/10`

Found by driving the installed command on 2026-11-22, not by a test: `update` reads the scope
committed at the commit, so a level edited only in the working tree makes it regenerate at the
**old** level and leaves the repository in drift. Without this step the level can only be changed
in two commits, the first of them deliberately red. This step removes that trap rather than only
documenting it, and `docs/diagrams/models-folder.md` loses the paragraph that described it.

### Step 9/10: Cover the hosted path at a lowered level

- Files: `tests/connector/test_analyze_drift.py` (a repository committing level 1 answers
  `aligned: true` through `POST /system/analyze`, and one whose committed level and committed model
  disagree answers with the differences)
- Check: `pytest tests/connector -q` → passes, the pre-existing `test_fetch` failure of a machine
  with Apple Git aside
- Trailer: `Step: 9/10`

The level reaches three generation sites and only two of them had a test at a level below 4: the
CLI's and the console page's. `POST /system/analyze` is the one other teams and the graders call,
and it was covered by hand only.

### Step 10/10: Strip the plumbing down to a seam the next parameter plugs into

- Files: `Source/drifter/check.py` (one declaration of the generation parameters `scope.json` may
  hold, each with its default and the levels or values it allows, which `_scope_rule` validates by
  looping over instead of naming `verbosity`; `parameters_of(scope)` returns them all with their
  defaults applied, and `verbosity_of` becomes one line over it); `Source/models/structural_model.py`
  (unchanged: a generator still takes its own parameter by name, not a bag);
  `docs/diagrams/model-seam.md` (what a second parameter has to add, in four lines, without naming
  one); `tests/drifter/test_cli.py` (the declaration and the validator stay in step, so a parameter
  cannot be half-added)
- Check: `pytest tests/drifter tests/structural tests/frontend tests/connector -q` → passes
- Trailer: `Step: 10/10`

Asked for on 2026-11-22: verbosity is the first parameter, not the only one there will ever be, so
what is reusable is separated from what is verbosity's own. Deliberately small, and it names no
future parameter: the ones to come are undecided, and designing for an example nobody has chosen
would be worse than this seam. A generator keeps a named argument rather than a parameter bag,
because the seam's rule that an owner decides everything inside their model includes their
signature.

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → names
   `docs/base/specifications.md`, line 261 being made untrue by this Epic
3. No open row for this Epic: `git grep -n "E02" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines
   1 to 3 and the Epic's own lines pass.

This Epic's own:

5. Level 4 is today's bytes, so no committed model and no golden moves:
   `pytest tests/structural tests/behavioral tests/connector tests/drift tests/common tests/drifter -q` → passes,
   and `git diff --stat main...HEAD -- docs/contract/` → prints nothing
6. The ladder is a ladder: `pytest tests/structural/test_verbosity.py -q` → passes, its subset case
   asserting that every element at one level is present at the level above
7. A bad level never reaches a generator:
   `pytest tests/drifter/test_cli.py -q -k "level_outside_the_ladder"` → 8 passed, 1 deselected or
   more, levels 0, 5, `true`, `null`, a list, an object and "high" each giving `INVALID_MODELS`
   through the check, and `init` refusing one before it writes anything
8. The level is set before the first model and a change to it redefines the baseline:
   `pytest tests/drifter/test_cli.py -q -k "init_sets_the_level or baseline or default_level or leaves_the_scope_alone"`
   → 7 passed, its cases being `init --verbosity` at each of levels 1 to 3 followed by an aligned
   `check`; `init` at the default writing byte-identical files whether or not the level is asked
   for; a hand-edited level followed by a plain `update`, which takes two commits; and
   `update --verbosity`, which takes one and which a plain `update` leaves `scope.json` alone for
9. The page carries the panel and names both levels:
   `pytest tests/frontend -q` → passes, including the 422 case, the note case, the standalone case
   and the case that proves both snapshots take the previewed level, and
   `git diff --stat main...HEAD -- Source/Frontend/index.html` → prints nothing, the panel
   being on the page and not in the console
10. The models say what the code does:
    `git grep -c "verbosity" -- docs/diagrams/model-seam.md docs/diagrams/models-folder.md` → each
    prints 1 or more
11. Imports still follow the map: `PYTHONPATH=Source lint-imports` → ends
    `Contracts: 5 kept, 0 broken.`
12. The hole is named, not opened: `git grep -n "verbosity" -- docs/invariants/INVARIANTS.md docs/state/WORK-ITEMS.md`
    → INV-2's row and the W0-7 row both print, so the ruling that closes `scope.json` is on record as
    having to close verbosity with it
13. The parameter seam holds, so the next parameter plugs into it instead of editing the validator:
    `pytest tests/drifter/test_cli.py -q -k "declared_parameter or the_declaration_covers"` →
    2 passed, one walking every row of `PARAMETERS` through the reader and the validator, the other
    pinning that verbosity's allowed values are the generator's own ladder

## Open questions

Each line the draft could not answer. The reviewer settles what the code, the models or a ruling can
answer, and the rest become rows in `docs/decisions/OPEN-DECISIONS.md`.

1. **Answered by the human, 2026-11-22: approved, build it now.** Is this work approved at all, and
   where does it sit in the queue? It is a direction change with no build-order step, and the Next
   action is step 0.6b. Row E02-a in `docs/decisions/OPEN-DECISIONS.md:23` records the word; only the
   human writes `docs/decisions/RULED/`, so the row stays until they move it, and Done criterion 3
   waits for that.
2. **Answered by the human, 2026-11-22, by approving the recommendation.** Does the ladder answer
   N3, or pre-empt it? E02 lands as the opt-in and N3's question of the default grain stays open:
   the default grain does not move, no `schema_version` is bumped and no committed model changes,
   so nothing N3 decides is foreclosed. Row E02-b records it (`docs/decisions/OPEN-DECISIONS.md:24`).
3. **Answered by the human, 2026-11-22, by approving the recommendation.** Must the W0-7 ruling
   cover verbosity before this lands? No: E02 lands with the gap named in INV-2 and graded
   DEFERRED, and the W0-7 ruling covers `scope.json` and `verbosity` together, since W0-7 already
   owes `scope.json` the same fix. Row E02-c records it (`docs/decisions/OPEN-DECISIONS.md:25`).
4. Does the panel remember one level for every repository, or one per repository? **Settled by the
   design on disk: one level for every repository, one `localStorage` key, per origin** — the
   design states it and names the cost (`DESIGN.md`, "The panel's memory is per origin", and the
   per-reader preview row beside it). The memory writes to no repository and to no model
   (`Source/Frontend/model_drift.py:40-52` regenerates from the commit's files only), so the
   choice is reversible in one line and needs no row of its own. Left as step 6 builds it.
5. Does the previewed level belong on a shared link, so that two readers of one screenshot see the
   same page? **Settled by the code: no, not in this Epic.** The console frames the page in an
   iframe (`Source/Frontend/index.html:256`, and the URL it builds at `:691`), so the level lives
   in the frame's own query string, which a reader of the console neither sees nor copies. The
   note on the page is what a screenshot carries instead (`DESIGN.md`, "Two distinct things").
   A shareable link would be a change to `Source/Frontend/index.html`, which step 6 and Done
   criterion 9 both hold unchanged.
6. **Answered by the human, 2026-11-22.** Should `drifter check` warn when a push lowers the level,
   instead of reporting every dropped element as drift? No: the level is chosen before the first
   model is generated, and a change to it redefines the baseline. `drifter update` regenerates from
   the committed scope, so the new models are the baseline and nothing is reported. The one case
   left, an edit without a regeneration, is already covered by `docs/base/specifications.md` §3.2, Scope.

## Done, as run by the drafting session

Run on 2026-11-22 at the commit of step 7, in a Python 3.13 virtualenv built from
`requirements.txt`, `requirements-dev.txt` and `pip install -e .`. This is the builder's own run and
does not replace the auditor's: `.claude/agents/auditor.md` re-runs every line at HEAD, from a
session that did not build the Epic.

| Line | Result |
|---|---|
| 1. CI green | **Not run.** `gh` is not installed on this machine, and nothing is pushed, so no run exists to ask about. The human's or the auditor's, with `gh` available. |
| 2. Spec lines updated | Pass. The diff names `docs/base/specifications.md`; line 261 was made untrue and is fixed in step 7. |
| 3. No open row for E02 | **Fails by design, and must.** Rows E02-a to E02-c carry the human's approval but only the human moves a row to `docs/decisions/RULED/` (R1). It passes once they do. |
| 4. The human accepts | Theirs, after lines 1 to 3. |
| 5. Level 4 is today's bytes | Pass. The whole suite gives 368 passed, 1 failed, and the one failure is `tests/connector/test_fetch.py::test_a_skipped_batch_fails_at_once_instead_of_fetching_lazily`, which fails on `main` in this environment too: Apple Git 2.39.5 raises `CalledProcessError` from `git cat-file --batch` on a blobless clone instead of the `AnalysisError` the test expects. `git diff --stat main...HEAD -- docs/contract/` prints nothing. |
| 6. The ladder is a ladder | Pass, 9 passed. |
| 7. A bad level never reaches a generator | Pass, 8 passed, 76 deselected. |
| 8. Set before the first model, and re-baselined | Pass, 5 passed, 79 deselected. |
| 9. The panel and both levels | Pass, 40 passed, and the `Source/Frontend/index.html` diff prints nothing. |
| 10. The models say what the code does | Pass, 3 and 5. |
| 11. Imports follow the map | Pass, `Contracts: 5 kept, 0 broken.` |
| 12. The hole is named | Pass, 1 and 3. |

**Corrected after the third review, which found this paragraph untrue.** It claimed steps 8 to 10
needed no Done line of their own. Two of its three clauses were wrong: line 5 ran
`tests/structural tests/behavioral tests/connector tests/drift tests/common` and so never ran
`tests/drifter` at all, and line 8's selector matched step 3's hand-edit case but neither of step
8's own tests. Steps 8 and 10 were pinned by nothing while the Epic said they were pinned. Line 5
now runs `tests/drifter` too, line 8's selector reaches `update --verbosity` and the plain-`update`
case, and step 10 has its own line, 13. Step 9's connector tests were genuinely inside line 5 all
along. The counts in the table below are from the run after that correction.

`ruff check` passes, which is not a Done line but is half of what CI runs. Lines 7 and 8 were
corrected here on the same day: their `-k verbosity` selectors matched no test, the test names
saying "level" and not "verbosity", so as written they reported success while running nothing.

### Driven by hand, 2026-11-22

No Done line drives the installed command or the running service, so both were driven once, on a
throwaway repository of two modules, a class, an inheriting class and an async method.

- `drifter init --verbosity 1` wrote `"verbosity": 1` into `scope.json` and a `structural.json` of
  two module nodes and one imports edge. `drifter check` on the commit that carried them: `aligned:
  true`, exit 0.
- The level raised to 4 by hand and committed without regenerating: five `ADDED` differences, exit
  1, which is the spec's "editing the scope without regenerating the models shows up as drift by
  itself" (`docs/base/specifications.md` §3.2, Scope). Then `drifter update`, commit, `drifter check`:
  `aligned: true`, exit 0. That is the re-baseline.
- The service started with the Dockerfile's `uvicorn` line: `GET /system/health` 200,
  `storage: ephemeral`. `GET /models/view` with no level drew level 4 and the note "which is the
  level this repository commits"; `&verbosity=1` drew the packages with no classes and the preview
  note naming both levels; `&verbosity=2` drew the classes again. All three answered 200 with four
  stops and the right one checked. `&verbosity=9` answered 400 `INVALID_REQUEST`, in the contract's
  error shape. `POST /system/analyze` answered `aligned: true` on the level-4 repository.
- **Found by hand, and documented rather than fixed:** changing the level takes two commits.
  `drifter update` reads the scope committed at the commit, not the working tree, so a level edited
  only in the working tree makes `update` regenerate at the **old** level and leaves the repository
  in drift. Recorded in `docs/diagrams/models-folder.md`, "The verbosity ladder". A
  `drifter update --verbosity` would remove the trap and is not in this Epic.

**Not driven:** the panel has not been opened in a browser, so its layout, the stop a reader
actually clicks, and the `localStorage` memory are unverified by eye. The markup and the three note
wordings were read from the rendered HTML, and the form is a plain GET whose submission is the URL
the three fetches above already exercise, but that is not the same as having seen it work.

## Review

REVISE · design-reviewer at d0b4cef · 2026-11-22

Direction is settled: rows E02-a, E02-b and E02-c all carry the human's word of 2026-11-22
(`docs/decisions/OPEN-DECISIONS.md:23-25`), and the Epic's text matches what those rows approve.
Both of the human's corrections are reflected: the panel is on the viewer page and
`Source/Frontend/index.html` is held unchanged (step 6, Done criterion 9), and a verbosity change
happens before the first model and redefines the baseline (step 4, Done criterion 8, `DESIGN.md`
"The level is chosen before the first model exists"). The filled-copy check of
`docs/templates/README.md` prints nothing for both files. Open questions 4 and 5 are now settled
from the disk; none needs a row in `docs/decisions/OPEN-DECISIONS.md`. Seventeen of the twenty
premise rows hold as cited. What blocks RATIFY is three missed generation and caller paths, found
by checking the premises against the code:

- **Blocking. The "one choke point" premise does not hold.** A second generation site exists:
  `snapshot()` loops over `GENERATORS` itself and never calls `_regenerate`
  (`Source/Frontend/model_drift.py:40-52`, imported at `:17` under the `.importlinter` ignore line
  `Frontend.model_drift -> drifter.check`, `.importlinter:47`). Neither `EPIC.md` nor `DESIGN.md`
  mentions it. Correct the premise row (`DESIGN.md:105`) to name both sites.
- **Blocking. Step 6 cannot pass as written: its Files omit `Source/Frontend/model_drift.py`.**
  `models_view` does not regenerate through `check._regenerate`; it calls
  `model_drift.snapshot(cmp, cmp.head)` and `model_drift.snapshot(cmp, cmp.base)`
  (`Source/GitHub_Connector/api.py:198` and `:201`), and `snapshot` takes no level. The level must
  reach both calls, or the drift chips compare level 4 against the previewed level instead of
  "that level with itself" (`DESIGN.md`, "Two distinct things"). Add the file and the parameter to
  step 6, and say that both snapshots take the same level.
- **Blocking. Step 4 omits the `/system/analyze` caller of `generate_models`.** It writes
  `generate_models(reader, verbosity)`, but `Source/GitHub_Connector/analysis.py:132` calls
  `check.generate_models(cmp)` with one argument. Either make the parameter keyword-with-default,
  as step 2 does for the generators, or list `analysis.py` among step 4's files.
- **Stale citation.** `DESIGN.md:113` cites `Source/Frontend/model_viewer.py:1-6` for "runs no
  script but Mermaid today"; line 5 says "no server, no scripts, no network", which `_script()`
  (`Source/Frontend/model_viewer.py:609`) and `MERMAID` (`:48`) already make untrue. Cite
  `_script` instead, and add that comment line to step 6's Files, since the panel's memory makes
  it wronger still.
- **Off-by-one citations.** The spec sentence "Editing the scope without regenerating the models
  shows up as drift by itself" begins at `docs/base/specifications.md:263`, not `:264`
  (`DESIGN.md:104`, step 7, open question 6). `differences` is defined at
  `Source/drifter/check.py:122`, outside the range `:110-119` cited for it (`DESIGN.md:102`).
- **Step 7 misses one queue line.** `docs/state/WORK-ITEMS.md:13` still reads "Drafted, waiting on
  the human … No code", which RATIFY makes untrue; step 7 names only the N7 row (`:240`) and the
  W0-7 row.
- **Note, not a defect.** Done criterion 3 can only print nothing after the human moves rows
  E02-a to E02-c and the detail line `docs/decisions/OPEN-DECISIONS.md:19` into
  `docs/decisions/RULED/`, which only they write (R1). The Epic says so, and criterion 4 sits
  after it.
- **Not run here.** `pytest` and `lint-imports` are not installed in this machine's interpreter,
  so every `pytest …` line and `PYTHONPATH=Source lint-imports` was checked for form, not
  executed: every test path named exists, `tests/frontend` holds the 26 tests step 1 tracks
  (14 in `test_models_view.py`, 12 in `test_behavioral_view.py`), and `.importlinter` defines the
  five contracts Done criterion 11 expects.

Verified as cited, for the record: `docs/invariants/INVARIANTS.md:16-18` (INV-1, INV-2, INV-3);
`Source/drifter/check.py:79-83`, `:110-119`, `:225-235`, `:263-270`, `:279-287`, `:290`;
`Source/drifter/cli.py:4-5`, `:57-65`; `Source/models/structural_model.py:1-2`, `:15`;
`Source/models/behavioral_model.py:17`; 29 call sites outside the two generator definitions;
`Source/GitHub_Connector/api.py:169` (`include_in_schema=False`);
`Source/Frontend/model_viewer.py:52` (`app.css` is the page's style, so step 6's file is right),
`:87`, `:102`, `:646` (`main`, the standalone render); `docs/base/structure.md:4`;
`docs/base/specifications.md:213`, `:261`; `docs/diagrams/models-folder.md:27`, `:35`
("open: JSON Schema"); `docs/diagrams/model-seam.md:11`, `:32` ("One check");
`docs/state/WORK-ITEMS.md:108` (gap G4), `:185` (W3-1 deletes `_scope_rule`).

REVISE · design-reviewer at 455d702 · 2026-11-22

Second review, of the revision made in `455d702`; `EPIC.md` and `DESIGN.md` are byte-identical at
HEAD (`a62a39e`), so this verdict covers both. All three of the first review's blocking findings
are genuinely fixed, not merely mentioned, and every citation `455d702` touched holds on disk:
`Source/Frontend/model_drift.py:40-52` is `snapshot` exactly, it is named in step 3 and its file,
parameter and the two-snapshot case are in step 6 and in Done criterion 9;
`Source/GitHub_Connector/api.py:198` and `:201` are the two `snapshot` calls and step 6 passes the
same level to both; `generate_models(reader, verbosity=FULL)` is keyword with a default and
`Source/GitHub_Connector/analysis.py:132` is `files = check.generate_models(cmp)`, needing no edit,
with `tests/connector` now in step 4's check. The non-blocking four are fixed too: the stale
`model_viewer.py:1-6` row now cites `:609` (`_script`), `:48` (`MERMAID`) and the module comment at
`:5`, all three correct; the spec sentence does begin at `docs/base/specifications.md:263` and end
at `:264`; `differences` at `Source/drifter/check.py:122` is inside the new range `:110-136`, which
ends on its `return found`; and step 7 now names `docs/state/WORK-ITEMS.md:13`, which still reads
"Drafted, waiting on the human … No code". **The drafting session's correction is right and the
first review was wrong:** `analysis.py:132` sits in `generate()`, which `post_generate`
(`Source/GitHub_Connector/api.py:112-115`) serves as `POST /system/generate`; `/system/analyze`
reaches `check.answer`, not `generate_models`. The filled-copy check of `docs/templates/README.md`
prints nothing for both files. Run here, not merely read: `PYTHONPATH=Source lint-imports` ends
`Contracts: 5 kept, 0 broken.`, `pytest tests/frontend tests/structural tests/drifter -q` gives
125 passed, `git status --porcelain tests/frontend` prints nothing, and `tests/frontend` holds the
26 tests step 1 tracks. What blocks RATIFY is one generation site that both reviews missed:

- **Blocking. There is a third generation site, so "two sites" and "one choke point" are both
  still untrue.** `model_differences` does not pass through `_regenerate`: it takes the generator
  out of `GENERATORS` and calls it itself (`Source/drifter/check.py:112` and `:116`). So the sites
  are `_regenerate` (`:290`, for `init`, `update` and `POST /system/generate`), `model_differences`
  (`:116`, for the check itself) and `snapshot` (`Source/Frontend/model_drift.py:51`). Fix the
  claim in three places: the `DESIGN.md` heading "Two generation sites take the level, not one" and
  its item 1, "`_regenerate` … which every path of the tool proper passes through: … and
  `model_differences` for the check itself" (`DESIGN.md:52-61`); the premise row that repeats it
  and is marked "yes" (`DESIGN.md:126`); and step 3's title, "through the one choke point". Step 3
  does list `model_differences` among its edits, so the build is covered, but it says only that it
  "reads" the level — say that it passes the level to the structural generator itself, as step 3
  says of `_regenerate` and step 6 says of `snapshot`. Without that, the check regenerates at level
  4 against a level-1 committed model and reports every dropped element as `REMOVED`.
- **Non-blocking, but say it somewhere.** All three sites call their generator through
  `GENERATORS`, typed `dict[str, Callable[[dict[str, str]], dict]]`
  (`Source/drifter/check.py:103`), and behavioral keeps its one argument (step 2), so each site has
  to single out the structural generator and that annotation stops being true of one entry. No
  check catches it: CI runs `ruff`, not a type checker. Name the annotation in step 2's or step 3's
  files, or say that the level is applied per generator at each site.
- **Nit.** `DESIGN.md:128` cites `Source/Frontend/model_drift.py:80-88` for `_scope`, which runs to
  `:89`; the premise itself holds.
- **Unchanged from the first review, and still true.** Done criterion 3 can print nothing only
  after the human moves rows E02-a to E02-c and `docs/decisions/OPEN-DECISIONS.md:19` into
  `docs/decisions/RULED/`, which only they write (R1). Direction is settled and was not re-opened:
  `docs/decisions/OPEN-DECISIONS.md:23-25` carry the human's word of 2026-11-22.
- **Outside this verdict, for the human.** Code for this Epic is already on the branch while its
  Status is `draft`: `a62a39e` committed step 1, and `Source/models/structural_model.py` carries an
  uncommitted step 2. R7 starts code after RATIFY, from a live Epic (`CLAUDE.md`, R7;
  `docs/epics/README.md`).

REVISE · design-reviewer at eae122b · 2026-11-22

Third review, of the ten-step revision, at `eae122b`; HEAD moved twice while this review ran
(`0b198e8` → `b569cc5` → `eae122b`), and the verdict covers `eae122b`. **Direction is not re-opened:**
rows E02-a to E02-c carry the human's word (`docs/decisions/OPEN-DECISIONS.md:23-25`) and the human
ratified by word. Steps 8, 9 and 10 are genuinely built, read from the code and not from the commit
messages: `update --verbosity` exists with no default so the flag alone changes the level
(`Source/drifter/cli.py:51-55`), `regenerate_models(reader, verbosity=None)` writes `scope.json`
back only when a level is given (`Source/drifter/check.py:335-353`), `tests/connector/test_analyze_drift.py:223-262`
covers `POST /system/analyze` at every level and pins the route against `drifter check` byte for
byte, and step 10's seam is real: `PARAMETERS` (`Source/drifter/check.py:116`), `parameters_of`
(`:121`), `_scope_rule` validating by looping over it and naming no parameter (`:456-463`), and
`verbosity_of` one line over the reader (`:141-144`). Step 10 names no future parameter, here or in
`docs/diagrams/model-seam.md:38-40`. Run here, not read: the whole suite gives 368 passed with only
the pre-existing Apple-Git `test_fetch` failure, `ruff check` passes, `PYTHONPATH=Source lint-imports`
ends `Contracts: 5 kept, 0 broken.`, and Done lines 2, 3, 5 to 12 each produce exactly the output
the table now records (8 passed / 76 deselected, 5 passed / 79 deselected, 3 and 5, 1 and 3). The
filled-copy check of `docs/templates/README.md` prints nothing for both files. The six open
questions each end in a sourced answer and none needs a new row. What blocks RATIFY is one Done
gap and two claims the last three commits made untrue:

- **Blocking. No Done line runs the tests of steps 8 and 10, and the Epic now claims otherwise.**
  Line 5 runs `tests/structural tests/behavioral tests/connector tests/drift tests/common`, which
  is not `tests/drifter`; lines 7 and 8 are `-k` selections of `test_cli.py`. Collected here, line
  8's selector picks `test_update_at_a_changed_level_redefines_the_baseline` (step 3's hand-edit
  case) and not step 8's `test_update_with_a_level_changes_it_and_rebaselines_in_one_commit`
  (`tests/drifter/test_cli.py:816`) or `test_update_without_a_level_leaves_the_scope_alone` (`:836`),
  and step 10's two seam tests (`:746`, `:764`) are in `tests/drifter` as well. So the new paragraph
  "step 8's behaviour is pinned by line 8's selector … step 10's by the two seam tests inside line
  5" is untrue in two of its three clauses. Widen line 8's selector, or add `tests/drifter` to a
  line, so a ten-step Epic's auditor runs what steps 8 and 10 built.
- **Blocking. `DESIGN.md`'s "What is missing" still says the registry was deliberately not built.**
  "**One parameter, not a set.** … a parameter registry would be the shape for the second and third
  parameter, and designing it now would be designing for one example" (`DESIGN.md:180-182`) is what
  step 10 then built: `PARAMETERS` is that registry (`Source/drifter/check.py:113-138`). A fresh
  reader is told the opposite of the code. Reword the bullet to what is still missing (a
  per-generator namespace, a schema, a second parameter) and say the declaration exists.
- **Blocking. `DESIGN.md`'s second generation site now describes the wrong mechanism.** "It takes
  the generator out of `GENERATORS` at `:112` and calls it at `:116` without going through
  `_regenerate`" (`DESIGN.md:59-61`, and the premise row at `:142`) is no longer how
  `model_differences` works: it calls `generate_one(name, sources.files, verbosity_of(...))`
  (`Source/drifter/check.py:166`), which is what the design's own "what the three sites share"
  paragraph requires. Say that, so the design and the code agree on the one site that matters most.
- **Blocking as a set, mechanical to fix: the build moved almost every line `DESIGN.md` cites, and
  `DESIGN.md` has not been re-anchored since `4a6f0d3`.** Current locations: `_regenerate` `:356`,
  called at `:321` and `:349` (cited `:290`, `:267`, `:287`); `model_differences` `:158-169` and
  `differences` `:172-186` (cited `:110-119`, `:110-136`); `_scope_rule` called at `:280` and `:342`,
  defined at `:447` (cited `:230`, `:285`); `GENERATORS` `:107` (cited `:103`); `generate_models`
  `:313-326` (cited `:263-270`); `init`'s flag `cli.py:43-47` and `_init` `:72-80` (cited
  `cli.py:57-65`); `generate_structural` `structural_model.py:33` (cited `:15`); `snapshot`
  `model_drift.py:40-56` with its generator call at `:54` (cited `:40-52`, `:51`) and `_scope`
  `:84-93` (cited `:80-88`, `:80-89`); the two `snapshot` calls `api.py:212` and `:216` (cited
  `:198`, `:201`) and `include_in_schema=False` `:170` (cited `:169`); `MERMAID`
  `model_viewer.py:63`, `_script` `:756`, `main` `:793`, `_compared` `:137`, `_provenance` `:249`,
  `app.css` read at `:66-67` (cited `:48`, `:609`, `:646`, `:87`, `:102`, `:52`).
- **Blocking, same kind, inside `EPIC.md`.** Step 3 cites `Source/drifter/check.py:116` for
  `model_differences`, which is now `PARAMETERS`; step 6 cites `Source/GitHub_Connector/api.py:198`
  and `:201` for the two `snapshot` calls, now `:212` and `:216`; step 7 and open question 6 cite
  `docs/base/specifications.md:263-264` for "Editing the scope without regenerating …", which step
  7's own edit pushed to `:268-269`, while `:263-264` now hold the verbosity sentence. Done
  criterion 2's `:261` still holds.
- **Non-blocking. The queue has not caught up with steps 8 to 10.** `docs/state/WORK-ITEMS.md:13`
  and `:240` both say "all seven steps", and `:240` still describes a level change as "a hand edit
  plus `drifter update`", which step 8 replaced and which `docs/diagrams/models-folder.md:57` and
  `docs/base/specifications.md:265` now contradict. `docs/README.md:97` still calls this "the draft
  Epic … No code until it is ratified". The Epic outranks all three (`CLAUDE.md`, authority order),
  so they are the lines to fix.
- **Non-blocking. The seam's cost claim is a little better than the code.** "A second parameter is
  therefore one row there, the generator argument it feeds, and that generator's own choice of how
  to use it" (`docs/diagrams/model-seam.md:40`, and step 10 here) leaves out `generate_one`
  (`Source/drifter/check.py:147-153`), which names `verbosity` and `"structural"` by hand, and the
  three sites that pass it positionally. Reading and validating a parameter are genuinely
  generalised, which is the expensive half; threading a second one is still four edits. Say which
  half the seam covers.
- **Non-blocking. One generation path the level cannot reach, by design but unnamed.**
  `POST /system/generate` calls `check.generate_models(cmp)` with the reader alone
  (`Source/GitHub_Connector/analysis.py:132`) and `generate_models` always writes `DEFAULT_SCOPE`
  (`Source/drifter/check.py:320-325`), so the hosted `init` can only propose level 4 and a
  verbosity field in the request would be a contract change (level 2). That is the right call;
  `DESIGN.md`'s "What is missing" should name it beside the reporter.
- **Nit.** Step 7's heading reads `Step 7/10` while its trailer and the headings of steps 1 to 6
  read `/7`. The revision note explains the trailers, so nothing is wrong on disk; make the
  headings agree with the trailers the commits carry (`Step: 1/7` … `Step: 7/7`, then `8/10` to
  `10/10`, which is what `git log` shows).
- **Unchanged and still true.** Done criterion 3 prints nothing only after the human moves rows
  E02-a to E02-c and `docs/decisions/OPEN-DECISIONS.md:19` into `docs/decisions/RULED/`, which only
  they write (R1). Criterion 4 sits after it.

REVISE · design-reviewer at fd70387 · 2026-11-22

Fourth review, of `fd70387`, which fixes the third review's findings in docs only; no file under
`Source/` or `tests/` has changed since the third review ran, so every run recorded there still
stands. **All five blocking findings are genuinely addressed, and the citation fix is better than
what was asked for:** code references in `DESIGN.md` and in the drafter's parts of `EPIC.md` are now
file plus symbol, which cannot rot with a line number, and line numbers are kept only where a
reader counts rows (`docs/invariants/INVARIANTS.md:16` and `:17` are INV-1 and INV-2, as cited).
Every symbol the rewritten premise table names exists on disk: `_regenerate`, `model_differences`,
`generate_one`, `generate_models`, `regenerate_models`, `read_sources`, `Sources`, `_scope_rule`,
`GENERATORS` and `PARAMETERS` in `Source/drifter/check.py`; `snapshot` and `_scope` in
`Source/Frontend/model_drift.py`; `models_view` with its `include_in_schema=False` in
`Source/GitHub_Connector/api.py`; `generate`, which holds `check.generate_models(cmp)`, in
`Source/GitHub_Connector/analysis.py`; `_init` in `Source/drifter/cli.py`; `_script`, `MERMAID`,
`main`, `_provenance` and `_compared` in `Source/Frontend/model_viewer.py`; and
`test_update_with_a_level_changes_it_and_rebaselines_in_one_commit`. No premise changed meaning in
the rewrite, and two are now more accurate for being in the past tense (the old `GENERATORS`
annotation, and the 29 invocations). Done line 5 now runs `tests/drifter`, so steps 8 and 10 are
pinned; run here, line 8 gives exactly `7 passed, 77 deselected`, the new line 13 gives exactly
`2 passed, 82 deselected`, and line 5's command gives 254 passed with only the known Apple-Git
`test_fetch` failure. The filled-copy check prints nothing for both files, step 7's heading now
matches its trailer, and the headings of steps 8 to 10 match the trailers `git log` shows. What
blocks RATIFY is three lines, each a one-line fix, and nothing else:

- **Blocking. The Done-run table was not re-run with the lines it now has.** Row 8 records
  `Pass, 5 passed, 79 deselected`, which is the old selector's output; the new line 8 gives
  `7 passed, 77 deselected`. There is no row 13, so the one line that pins step 10 has no recorded
  result. And the correction paragraph says "The counts in the table below are from the run after
  that correction" while the table sits **above** it and holds the counts from before. A reader of
  that table still cannot tell that steps 8 and 10 were run, which is the defect the paragraph was
  written to close. Refresh row 8, add row 13, and point the sentence at the table above it.
- **Blocking. One spec citation was left behind at the old line.** `DESIGN.md`, in the prose above
  the premise table, still cites `docs/base/specifications.md:263-264` for "Editing the scope
  without regenerating the models shows up as drift by itself". That sentence is now at `:268-269`;
  `:263-264` hold the verbosity sentence step 7 inserted. The premise row for the same fact was
  correctly changed to `§3.2, Scope` — make the prose match it.
- **Blocking. Step 6's Files still cite the pre-build line numbers.** "passes the **same** level to
  both `snapshot` calls, at `:198` and `:201`" — those calls are now in `models_view` at `:212` and
  `:216`. Name them by symbol, as the design's premise row now does. (The module comment cited at
  `:5` is still the right line, and `Source/Frontend/index.html:256` and `:691` in open question 5
  both still hold.)
- **Non-blocking.** The revision note and open question 4 still cite
  `Source/Frontend/model_drift.py:40-52` for `snapshot`, which now runs to `:56`, so the range stops
  just before the `generate_one` line it is cited for. Drop the range.
- **Addressed, for the record.** The seam now says which half is general and spells the cost of a
  second parameter as a row plus a line in `generate_one` plus its generator argument plus three
  call sites (`docs/diagrams/model-seam.md`, "Adding the next parameter"); `DESIGN.md`'s "What is
  missing" names what step 10 built, what is still verbosity's own, and the hosted `init`'s level-4
  limit; `docs/state/WORK-ITEMS.md:13` and `:240` and `docs/README.md` say ten steps and name
  `drifter update --verbosity`.
- **Unchanged and still true.** Done criterion 3 prints nothing only after the human moves rows
  E02-a to E02-c and `docs/decisions/OPEN-DECISIONS.md:19` into `docs/decisions/RULED/`, which only
  they write (R1). Criterion 4 sits after it. Direction was not re-opened.

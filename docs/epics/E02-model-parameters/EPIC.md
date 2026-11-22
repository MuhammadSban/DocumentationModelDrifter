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

### Step 3/7: Read the level from the committed scope, through the one choke point

- Files: `Source/drifter/check.py` (`_regenerate(files, verbosity)` passes the level to the
  structural generator; `model_differences` reads it from `sources.models["scope.json"]`, which
  `read_sources` has already parsed; `regenerate_models` reads it from the scope it already reads;
  `_scope_rule` rejects anything that is not an integer from 1 to 4 with `INVALID_MODELS`);
  `tests/drifter/test_cli.py` (a committed `scope.json` at level 1 gives a structural model of
  modules and imports only; a level of 0, of 5 and of "high" each give `INVALID_MODELS`; `update`
  at a changed level rewrites the models and a `check` straight after it is aligned)
- Check: `pytest tests/drifter tests/drift tests/common -q` → passes
- Trailer: `Step: 3/7`

`Sources` gains no field: the committed scope is already in `sources.models`. The last test is the
re-baseline the human described on 2026-11-22, and it needs no new code path: `drifter update`
already regenerates from the scope committed at the commit, so the models it writes are the new
baseline. Validation is inline because `scope.json` has no schema yet; if W3-1 lands first, this
step adds the key to `scope.schema.json` instead and the check command is unchanged.

`_regenerate` is not the only generation site, and this step does not pretend it is: the console's
page has its own loop over `GENERATORS` in `Source/Frontend/model_drift.py:40-52`, which step 6
covers. This step is the tool proper.

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
   `pytest tests/structural tests/behavioral tests/connector tests/drift tests/common -q` → passes,
   and `git diff --stat main...HEAD -- docs/contract/` → prints nothing
6. The ladder is a ladder: `pytest tests/structural/test_verbosity.py -q` → passes, its subset case
   asserting that every element at one level is present at the level above
7. A bad level never reaches a generator:
   `pytest tests/drifter/test_cli.py -q -k verbosity` → passes, levels 0, 5 and "high" each giving
   `INVALID_MODELS`
8. The level is set before the first model and a change to it redefines the baseline:
   `pytest tests/drifter/test_cli.py -q -k "verbosity and (init or update)"` → passes, its two cases
   being `init --verbosity 1` followed by an aligned `check`, and a hand-edited level followed by
   `update` and an aligned `check`
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
   left, an edit without a regeneration, is already covered by `docs/base/specifications.md:263-264`.

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

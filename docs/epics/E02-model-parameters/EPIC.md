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

### Step 4/7: Set the level before the first model exists

- Files: `Source/drifter/cli.py` (`init` gains `--verbosity`, an integer from 1 to 4, default 4);
  `Source/drifter/check.py` (`generate_models(reader, verbosity)` writes the level into the
  `scope.json` it writes and generates at it); `tests/drifter/test_cli.py` (`init --verbosity 1`
  writes `verbosity: 1` into `scope.json` and a `structural.json` of modules and imports only, and
  a `check` straight after it is aligned)
- Check: `pytest tests/drifter -q` → passes
- Trailer: `Step: 4/7`

This is the human's "the change in verbosity happens before the initial model is generated": the
first baseline is at the chosen level, not at level 4 and then lowered.

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

- Files: `Source/GitHub_Connector/api.py` (`models_view` gains `verbosity: int | None = None`,
  validated 1 to 4, passes it to the regeneration, and hands `render` the route the page was served
  from so the panel's form has somewhere to submit); `Source/Frontend/model_viewer.py` (the panel
  above the three model panels: a GET form with four radio stops, `repository` and `commit_id` as
  hidden inputs, read-only when there is no route; one note beside `_provenance` and `_compared`
  saying which level is drawn, which the repository commits, and that the drift chips compare that
  level with itself; a few lines of script that remember the stop in `localStorage`, in try and
  catch); `Source/Frontend/app.css` (the panel's styles); `tests/frontend/test_models_view.py` (a
  request at level 1 draws packages and no classes; a request with no level draws what it draws
  today; a request at level 9 gives 422; the note names both levels when they differ and is absent
  when they agree; the standalone render has no form and says how to change the level)
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
  signature); `docs/base/specifications.md` (line 261, what `scope.json` holds; line 264 already
  says what an edit without regenerating does and is left as it is); `docs/README.md` (the lines
  for the two models); `docs/invariants/INVARIANTS.md` (INV-2's check column names verbosity among
  what the W0-7 ruling must cover); `docs/state/WORK-ITEMS.md` (the N7 row, and the W0-7 row gains
  verbosity under gap G4)
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
   `pytest tests/frontend -q` → passes, including the 422 case, the note case and the standalone
   case, and `git diff --stat main...HEAD -- Source/Frontend/index.html` → prints nothing, the panel
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

1. Is this work approved at all, and where does it sit in the queue? It is a direction change with
   no build-order step, and the Next action is step 0.6b. The human's call: row E02-a in
   `docs/decisions/OPEN-DECISIONS.md`.
2. Does the ladder answer N3, or pre-empt it? N3 asks which grain the structural model has and
   lists "finer grain as an opt-in in `scope.json`" among its options, which is this Epic's shape.
   The human's call: row N3, and row E02-b for whether E02 may land before N3 is ruled.
3. Must the W0-7 ruling cover verbosity before this lands, or may the Epic land with the hole
   named and DEFERRED? Lowering the level and regenerating in one push hides every drift the level
   drops, which is gap G4 in a new place. The human's call: row E02-c.
4. Does the panel remember one level for every repository, or one per repository? One level for
   every repository is what step 6 builds, being the smaller thing. Settled by the human in the
   panel's first use, or left as it is.
5. Does the previewed level belong on a shared link, so that two readers of one screenshot see the
   same page? The level is in the page's own URL, which a reader of the framed console does not
   see or copy. Left out of this Epic.
6. **Answered by the human, 2026-11-22.** Should `drifter check` warn when a push lowers the level,
   instead of reporting every dropped element as drift? No: the level is chosen before the first
   model is generated, and a change to it redefines the baseline. `drifter update` regenerates from
   the committed scope, so the new models are the baseline and nothing is reported. The one case
   left, an edit without a regeneration, is already covered by `docs/base/specifications.md:264`.

## Review

Not yet reviewed. The design reviewer runs as a fresh subagent, never in the session that drafted
this Epic, and writes RATIFY or REVISE here with its findings. Status stays `draft` until it does,
and no step above may start. The human's answers to open questions 1 to 3 are needed before a
review can settle anything: all three are direction and none can be read off the disk.

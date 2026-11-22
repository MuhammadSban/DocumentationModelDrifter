# E02: Model generation parameters, and verbosity as the first one

Status: draft · Owner: Kaan

W-row: N7 in `docs/state/WORK-ITEMS.md` · Branch: `E02-model-parameters`

## Goal

`models/scope.json` gains one key, `verbosity`, an integer from 1 to 4 that says how much of the
code the structural model describes: level 1 is the packages and the imports between them, level 4
is every function and method with its signature. Level 4 is the default and is byte-identical to
what the generators write today, so a repository that commits no key sees no change at all. The two
generators take it as a keyword argument, and the core passes it the value it read from the
committed `scope.json`. The console's Models view gains a parameters panel that previews the models
at any level, remembers the reader's choice in their own browser, and says on the page which level
it is showing and which level the repository committed. The design, and what is deliberately left
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

- Models: `docs/diagrams/model-seam.md`, changes (the generator contract gains a keyword argument).
  `docs/diagrams/models-folder.md`, changes (the `scope.json` box gains the key and the ladder).
  `docs/diagrams/dependency.md`, reads (no import crosses a new boundary; the panel is console-side).
  `docs/diagrams/behavioral-model.md`, reads (unchanged: behavioral has no ladder in this Epic).
- Rulings: none. `docs/decisions/RULED/` holds only its README, so no ruling exists to read. This
  Epic needs two written, for N3 and for E02 itself.
- Invariants: INV-1, reads (its wording already covers a parameter committed in `/models`, and the
  default keeps today's bytes). INV-2, reads (its wording already covers the scope rules, so
  verbosity inherits gap G4 of W0-7 and whichever fix closes it). INV-3, reads (the import
  contracts are unchanged).
- Rows: W3-1, which adds `scope.schema.json` and would own this key's validation. W0-7, whose
  ruling must name verbosity. N3, the structural grain, which this Epic partly answers. N2, the
  behavioral grain, which is why behavioral gets no ladder here.

## Steps

One commit per step, made after the step's check passes. No step starts before RATIFY.

### Step 1/7: Track the console's own tests

- Files: `tests/frontend/test_models_view.py` and `tests/frontend/test_behavioral_view.py`, both
  untracked on `main` today and both covering the view this Epic changes; `tests/frontend/__pycache__`
  stays ignored
- Check: `git status --porcelain tests/frontend` → prints nothing
- Trailer: `Step: 1/7`

The 26 tests in these two files are the Models view's only coverage, and four Done criteria below
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
signature, which takes no keyword. Behavioral is untouched; `generate_behavioral` keeps its one
argument, so the seam gains the argument on one generator only, which `DESIGN.md` states.

### Step 3/7: Read the key from the committed scope and pass it through

- Files: `Source/drifter/check.py` (read `verbosity` where `include` and `exclude` are read, default
  4, reject anything that is not an integer from 1 to 4 with `INVALID_MODELS`; pass it to the
  structural generator through the `GENERATORS` map); `tests/drifter/test_cli.py` (a committed
  `scope.json` at level 1 gives a structural model of modules and imports only; a level of 0, of 5
  and of "high" each give `INVALID_MODELS`)
- Check: `pytest tests/drifter tests/drift tests/common -q` → passes
- Trailer: `Step: 3/7`

Inline validation, not a schema: `scope.json` has none yet, and W3-1 is the row that adds
`scope.schema.json`. If W3-1 lands first, this step adds the key to that schema instead and the
check command is unchanged.

### Step 4/7: Prove the goldens and the contract are untouched

- Files: none. A verification step with no edit; if it fails, the Epic is wrong and goes back to
  draft
- Check: `pytest tests/connector tests/behavioral -q` → passes, with no change to
  `docs/contract/model-golden-outputs.json` or `docs/contract/golden-outputs.json`
- Trailer: `Step: 4/7`

A step that changes nothing is here on purpose: the whole claim that this feature is safe rests on
level 4 being today's bytes, and that claim is checked before the console is touched. It has no
commit of its own if nothing changed; its result is recorded in the Epic's Review section instead.

### Step 5/7: Take the level on the console's route and say so on the page

- Files: `Source/GitHub_Connector/api.py` (`models_view` gains `verbosity: int | None = None`,
  validated 1 to 4, and passes it to the regeneration; the committed level is read too, so the page
  can name both); `Source/Frontend/model_viewer.py` (one note beside `_provenance` and `_compared`,
  saying which level is drawn, which the repository commits, and that the drift chips compare that
  level with itself); `tests/frontend/test_models_view.py` (a request at level 1 draws packages and
  no classes; a request with no level draws what it draws today; a request at level 9 gives 422; the
  note names both levels when they differ and is absent when they agree)
- Check: `pytest tests/frontend -q` → passes
- Trailer: `Step: 5/7`

The route stays out of the OpenAPI document, so this is not a contract change and Team 16 agrees to
nothing. The page gains a note and no script: `model_viewer.py` renders no script but Mermaid, and
this Epic does not end that.

### Step 6/7: Add the panel to the console

- Files: `Source/Frontend/index.html` (a parameters panel above the models frame: four stops named
  Overview, Types, Members and Full, a reset to the committed level, the level put on the frame's
  URL, and the choice kept in the existing `localStorage` store beside the watchlist); its inline
  styles in the same file
- Check: `pytest tests/frontend -q` → passes, and the panel is driven by hand once against a real
  repository, with the three results written into this step: the level survives a reload, a reset
  returns to the committed level, and a blocked `localStorage` leaves the panel working in memory
- Trailer: `Step: 6/7`

The hand-driven result is written into this file, not asserted in a test: the console has no browser
test harness, and inventing one is not this Epic's work.

### Step 7/7: Update the models, the spec and the docs map

- Files: `docs/diagrams/model-seam.md` (the generator contract line, and one sentence that a
  parameter is committed in `/models` and never passed from a request); `docs/diagrams/models-folder.md`
  (the `scope.json` box gains `verbosity` and the ladder); `docs/base/structure.md` (line 4, the
  signature); `docs/base/specifications.md` (line 261, what `scope.json` holds); `docs/README.md`
  (the lines for the two models); `docs/invariants/INVARIANTS.md` (INV-2's check column names
  verbosity among what the W0-7 ruling must cover); `docs/state/WORK-ITEMS.md` (the N7 row, and
  the W0-7 row gains verbosity under gap G4)
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
8. The console previews a level and names it:
   `pytest tests/frontend -q` → passes, including the 422 case and the note case
9. The models say what the code does:
   `git grep -c "verbosity" -- docs/diagrams/model-seam.md docs/diagrams/models-folder.md` → each
   prints 1 or more
10. Imports still follow the map: `PYTHONPATH=Source lint-imports` → ends
    `Contracts: 5 kept, 0 broken.`
11. The hole is named, not opened: `git grep -n "verbosity" -- docs/invariants/INVARIANTS.md docs/state/WORK-ITEMS.md`
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
   named and DEFERRED? Lowering the level hides every drift it drops, which is gap G4 in a new
   place. The human's call: row E02-c.
4. Does the panel remember one level for every repository, or one per repository? One global level
   is what step 6 builds, being the smaller thing. Settled by the human in the panel's first use,
   or left as it is.
5. Does the reader's previewed level belong on a shared link, so that two readers of one screenshot
   see the same page? Today the level is in the frame's URL, which no reader sees or copies. Left
   out of this Epic.
6. Should `drifter check` warn when a push lowers the committed level, instead of reporting every
   dropped element as REMOVED? Left out of this Epic; it is the first line of the "what is missing"
   list in `DESIGN.md`.

## Review

Not yet reviewed. The design reviewer runs as a fresh subagent, never in the session that drafted
this Epic, and writes RATIFY or REVISE here with its findings. Status stays `draft` until it does,
and no step above may start. The human's answers to open questions 1 to 3 are needed before a
review can settle anything: all three are direction and none can be read off the disk.

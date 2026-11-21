# E02: The data-flow and behavior models

Status: draft · Owner: Kaan

W-row: none. Build order step 0.6b has no W-row; `docs/state/WORK-ITEMS.md` names it by its step number under Next action · Branch: `E02-system-models`

## Goal

When this Epic closes, `docs/diagrams/` holds five models, a README and `render.py`, and nothing else. Two of the models are the system models this step adds beside `dependency.md`: `data-flow.md`, new, answers "if I change this step, what sees it downstream?", and `behavior.md`, which is `behavioral-model.md` renamed and extended, answers "what can happen to a request, and what does the user see?". `README.md`, new, says what each model answers, how to read it, and that every model in the folder is level 6 of the authority order, below the spec. The three kept models (`dependency.md`, `models-folder.md`, `model-seam.md`) are reviewed for stale lines. The seven other diagram files are gone: what was still true in six of them is in the models, and `research-evidence.md` is in `docs/research/`. No live file cites a deleted one. Whoever changes a step of a check, or an ending of a request, needs these two models to see what the change reaches (R6).

Every behaviour the two models draw is taken from the code. Each state, status code and limit has a row in the model's own "Premises, verified" table that names its source line. Where the code and the build order's wording disagree, the code wins; `DESIGN.md` lists the six disagreements found while planning.

No model names who owns a file or folder. No new CI check is added. Each file holds one Mermaid block, as `tests/docs/test_diagrams.py` requires.

Decided by the human on 2026-11-21, before the draft:

- **Dated records stay as written.** `docs/closed/`, `docs/history/`, `.claude/permissions-checklist.md` and `docs/state/WORK-ITEMS.md` keep the names of deleted files where they record what was true on a date. Every other reference is fixed. In `WORK-ITEMS.md` the open rows that name a deleted file as something to touch are repointed (step 6).
- **`research-evidence.md` moves whole** to `docs/research/research-evidence.md` with `git mv`. It is a table of evidence, not a model.
- **The tester's side is dropped, not moved.** What `cross-team-test.md` and `four-field-answer.md` draw (the test session, the feature skip, how T-26 is graded) is stated in `docs/contract/pod-contract.md`, which ranks higher. The README points there. `behavior.md` keeps only what the system does to a request.
- **`model-seam.md` loses the role word "owner".** Each use is reworded to the part it means: the generator, its schema, the core.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/dependency.md`, reads and changes (its boxes are named by `data-flow.md`, not redrawn; reviewed for stale lines in step 5). `docs/diagrams/behavioral-model.md`, changes (renamed `behavior.md`, then extended). `docs/diagrams/models-folder.md`, changes (stale lines). `docs/diagrams/model-seam.md`, changes (stale lines and the role word). `docs/diagrams/data-flow.md` and `docs/diagrams/README.md`, new. Deleted in step 6: `comparison.md`, `cross-team-test.md`, `file-fetch.md`, `four-field-answer.md`, `init.md`, `one-check.md`. Moved in step 6: `research-evidence.md`.
- Rulings: none. `docs/decisions/RULED/` holds only its README.
- Invariants: none read or changed. The Epic changes no code and no check, so INV-1, INV-2 and INV-3 hold as before; `data-flow.md` names INV-3's module map and does not restate it.

## Steps

One commit per step, made after the step's check passes. Before each model is written, its full text is shown to the human. `data-flow.md`, `behavior.md` and `model-seam.md` are on ask in `.claude/settings.json`, so the permission prompt is where the human approves each of them. Step 6 starts only after the human has approved `data-flow.md`, `behavior.md` and `README.md`.

### Step 1/6: Write the data-flow model

- Files: `docs/diagrams/data-flow.md` (new: the question, one Mermaid flowchart, a table of what each step reads and writes and what sees it downstream, and "Premises, verified")
- Check: `python -m pytest tests/docs -q -k data-flow` → `1 passed`
- Trailer: `Step: 1/6`

The content is `DESIGN.md`, "data-flow.md". The file names the boxes of `dependency.md` and does not redraw them. It takes over what is still true in `file-fetch.md`, `init.md`, `one-check.md` and `comparison.md` (`DESIGN.md`, "Where the content of each deleted file goes").

### Step 2/6: Rename the behavior model and fix every reference to the old name

- Files: `docs/diagrams/behavioral-model.md` to `docs/diagrams/behavior.md` with `git mv`, its content untouched; `CLAUDE.md` (the level 6 line: `behavioral-model.md` becomes `behavior.md`, and `data-flow.md` is added to the list); `docs/base/specifications.md` (line 294, the file name only); `docs/README.md` (the path only); `docs/diagrams/init.md` (line 7, the file name only)
- Check: `git grep -n "behavioral-model" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/closed" ":!docs/history" ":!docs/epics/E02-system-models"` → prints nothing
- Trailer: `Step: 2/6`

The model's own content does not change in this commit, so git records a pure rename. The reference fixes ride in the same commit, as in step 1 of `docs/closed/E01-module-map/EPIC.md`, so that no commit on the branch cites a file that is not there.

### Step 3/6: Extend the behavior model with the states of one analyze run

- Files: `docs/diagrams/behavior.md` (the lifecycle kept and corrected, the states of one `POST /system/analyze` run nested in it, a table of every ending with what the caller sees and what is saved, and "Premises, verified"); `docs/README.md` (the line that describes the file); `docs/base/specifications.md` (line 294 to 296, only if the corrected lifecycle makes the sentence untrue, R2)
- Check: `python -m pytest tests/docs -q -k behavior` → `1 passed`
- Trailer: `Step: 3/6`

The content is `DESIGN.md`, "behavior.md". The file keeps exactly one Mermaid block: one state diagram, with the run as a composite state inside the lifecycle.

### Step 4/6: Write the folder's README

- Files: `docs/diagrams/README.md` (new: one row per model with the question it answers and how to read it; that every model in the folder is level 6 of the authority order in `CLAUDE.md`, below the spec; that the cross-team test session is defined in `docs/contract/pod-contract.md`; how to render a PNG)
- Check: `git grep -c -E "dependency\.md|data-flow\.md|behavior\.md|models-folder\.md|model-seam\.md" -- docs/diagrams/README.md` → `docs/diagrams/README.md:5` or more, and `python -m pytest tests/docs -q -k README` → `1 passed`
- Trailer: `Step: 4/6`

The README holds no Mermaid block. `tests/docs/test_diagrams.py:18-19` and `docs/diagrams/render.py:25-27` both pass over a page without one.

### Step 5/6: Review the three kept models for stale lines

- Files: `docs/diagrams/dependency.md`, `docs/diagrams/models-folder.md`, `docs/diagrams/model-seam.md`; `docs/README.md` (the three lines that describe them, where a line changes)
- Check: `git grep -n -i -E "\(owner\)|each owner|owners write|model owner|open: JSON Schema" -- docs/diagrams/dependency.md docs/diagrams/models-folder.md docs/diagrams/model-seam.md` → prints nothing
- Trailer: `Step: 5/6`

Each line of the three files is read against the code. The findings are listed for the human before any edit, each with the source line that makes it stale. Known before the review starts: `models-folder.md` says "open: JSON Schema" for structural and behavioral, and both schemas exist (`Source/models/structural.schema.json`, `Source/models/behavioral.schema.json`); `model-seam.md` carries the role word "owner" and two version notes that have passed ("written by the core in v1.1", "before plugging in at v1.2"). The words `owners` and `ownership` stay where they name the field of `ownership.json` or the model.

### Step 6/6: Delete the other diagram files and fix every reference to them

- Files: deleted with `git rm`: `docs/diagrams/comparison.md`, `cross-team-test.md`, `file-fetch.md`, `four-field-answer.md`, `init.md`, `one-check.md`. Moved with `git mv`: `docs/diagrams/research-evidence.md` to `docs/research/research-evidence.md`. References: `docs/README.md` (the `diagrams/` section rewritten for the files that remain, the moved file listed under `research/`); `docs/base/phase4.md` (line 132, D11: the citation becomes `data-flow.md` and the row gains the two measured times it lacks, a full clone at 26 s on pytest and 155 s on Django; line 172: "one-check diagram" becomes `docs/diagrams/behavior.md`); `docs/state/tracker-gaps.md` (row 3); `docs/proposals/init/init.md` (line 59); `docs/proposals/language-engine/04-one-template.md` (line 307), `06-init.md` (lines 3 and 13) and `research-multi-language.md` (line 5); `tests/ownership/test_ownership_model.py` (line 1, the comment only); `docs/state/WORK-ITEMS.md` (the open rows W0-6, W0-7 in detail, W3-5 and W5-3, where they name a deleted file as something to touch)
- Check: `git grep -n -E "(behavioral-model|comparison|cross-team-test|file-fetch|four-field-answer|one-check)\.(md|png)|diagrams/(init|research-evidence)\.md" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/closed" ":!docs/history" ":!.claude/permissions-checklist.md" ":!docs/epics/E02-system-models"` → prints nothing
- Trailer: `Step: 6/6`

One commit holds the deletions, the move and every reference fix. Before it, each deleted file is read once more against the three models, so that nothing still true is lost.

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`. The branch is pushed only on the human's word, so this line can pass only after that.
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → `docs/base/specifications.md` is in the diff: line 294 names `behavior.md`.
3. No open row for this Epic: `git grep -n "E02" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass. It includes the human's approval of `data-flow.md`, `behavior.md` and `README.md`.

This Epic's own:

5. The folder holds the five models, the README and the renderer, and nothing else: `git ls-files docs/diagrams` → exactly seven lines: `docs/diagrams/README.md`, `docs/diagrams/behavior.md`, `docs/diagrams/data-flow.md`, `docs/diagrams/dependency.md`, `docs/diagrams/model-seam.md`, `docs/diagrams/models-folder.md`, `docs/diagrams/render.py`
6. Each file holds at most one Mermaid block, with `accTitle` and `accDescr`: `python -m pytest tests/docs -q` → `6 passed`
7. No live file cites a deleted one: the check command of step 6 → prints nothing
8. Both new models name their sources: `git grep -c "^## Premises, verified" -- docs/diagrams/data-flow.md docs/diagrams/behavior.md` → `docs/diagrams/behavior.md:1` and `docs/diagrams/data-flow.md:1`
9. The rename is a rename: `git log -M --diff-filter=R --name-status --format= main..HEAD -- docs/diagrams/` → has the line `R100`, `docs/diagrams/behavioral-model.md`, `docs/diagrams/behavior.md`
10. No model carries the role word or a known stale line: the check command of step 5 → prints nothing
11. The research table moved: `git ls-files docs/research/research-evidence.md` → `docs/research/research-evidence.md`
12. No new CI check and no code change: `git diff --stat main...HEAD -- .github .importlinter Source requirements.txt requirements-dev.txt pyproject.toml` → prints nothing
13. The docs map lists every file in the folder: `for f in $(git ls-files docs/diagrams); do git grep -q "diagrams/$(basename $f)" -- docs/README.md || echo $f; done` → prints nothing
14. The level 6 line names the five models: `git grep -c -E "dependency\.md.*data-flow\.md.*behavior\.md.*models-folder\.md.*model-seam\.md" -- CLAUDE.md` → `CLAUDE.md:1`

## Open questions

None the draft could not answer. The four calls that were the human's were asked and answered on 2026-11-21 and are recorded under Goal. The six places where the code and the build order's wording disagree are in `DESIGN.md`, "Where the code and the build order disagree"; in each the code wins, as the human asked, so none is an open question.

## Review

Not reviewed yet. The design reviewer writes RATIFY or REVISE here.

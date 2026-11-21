# E02: The data-flow and behavior models

Status: ratified · Owner: Kaan

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

- Files: `docs/diagrams/data-flow.md` (new: the question, one Mermaid flowchart, a table of what each step reads and writes and what sees it downstream, and "Premises, verified"); `docs/README.md` (its entry in the `diagrams/` section)
- Check: `git grep -c -E "^(.{3}mermaid|## Premises, verified)" -- docs/diagrams/data-flow.md` → `docs/diagrams/data-flow.md:2`: one Mermaid fence and the premises heading. The step also runs `python -m pytest tests/docs -q`, which must end with a line beginning `12 passed`.
- Trailer: `Step: 1/6`

The content is `DESIGN.md`, "data-flow.md". The file names the boxes of `dependency.md` and does not redraw them. It takes over what is still true in `file-fetch.md`, `init.md`, `one-check.md` and `comparison.md` (`DESIGN.md`, "Where the content of each deleted file goes").

### Step 2/6: Rename the behavior model and fix every reference to the old name

- Files: `docs/diagrams/behavioral-model.md` to `docs/diagrams/behavior.md` with `git mv`, its content untouched; `CLAUDE.md` (the level 6 line, which becomes: "6. The models in `docs/diagrams/`: `dependency.md`, `data-flow.md`, `behavior.md`, `models-folder.md` and `model-seam.md`. Every other diagram ranks at level 8."); `docs/base/specifications.md` (line 294, the file name only); `docs/README.md` (the path only); `docs/diagrams/init.md` (line 7, the file name only)
- Check: `git grep -n "behavioral-model" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/closed" ":!docs/history" ":!docs/epics/E02-system-models"` → prints nothing
- Trailer: `Step: 2/6`

The model's own content does not change in this commit, so git records a pure rename. The reference fixes ride in the same commit, as in step 1 of `docs/closed/E01-module-map/EPIC.md`, so that no commit on the branch cites a file that is not there.

### Step 3/6: Extend the behavior model with the states of one analyze run

- Files: `docs/diagrams/behavior.md` (the lifecycle kept and corrected, the states of one `POST /system/analyze` run nested in it, a table of every ending with what the caller sees and what is saved, and "Premises, verified"); `docs/README.md` (the line that describes the file); `docs/base/specifications.md` (line 294 to 296, only if the corrected lifecycle makes the sentence untrue, R2)
- Check: `git grep -c -E "^(.{3}mermaid|## Every ending|## Premises, verified)" -- docs/diagrams/behavior.md` → `docs/diagrams/behavior.md:3`: one Mermaid fence, the endings table's heading and the premises heading. Before this step the same command prints `:1`.
- Trailer: `Step: 3/6`

The content is `DESIGN.md`, "behavior.md". The file keeps exactly one Mermaid block: one state diagram, with the run as a composite state inside the lifecycle.

### Step 4/6: Write the folder's README

- Files: `docs/diagrams/README.md` (new: one row per model with the question it answers and how to read it; that every model in the folder is level 6 of the authority order in `CLAUDE.md`, below the spec; that the cross-team test session is defined in `docs/contract/pod-contract.md`; how to render a PNG); `docs/README.md` (its entry in the `diagrams/` section)
- Check: `git grep -c -E "^\| .(dependency|data-flow|behavior|models-folder|model-seam)\.md. \|" -- docs/diagrams/README.md` → `docs/diagrams/README.md:5`: one table row per model
- Trailer: `Step: 4/6`

The README holds no Mermaid block. `tests/docs/test_diagrams.py:18-19` and `docs/diagrams/render.py:25-27` both pass over a page without one.

### Step 5/6: Review the three kept models for stale lines

- Files: `docs/diagrams/dependency.md`, `docs/diagrams/models-folder.md`, `docs/diagrams/model-seam.md`; `docs/README.md` (line 42, which describes `model-seam.md` with "the three model owners" and "an owner's model", is reworded; the lines for the other two where a line changes)
- Check: `git grep -n -i -w -E "owner|in v1\.1|at v1\.2|open: JSON Schema" -- docs/diagrams/dependency.md docs/diagrams/models-folder.md docs/diagrams/model-seam.md` → prints nothing. With `-w`, `owner` matches "owner" and "owner's" and not "owners" or "ownership"; at `01c2ab2` the command prints lines of `model-seam.md` and `models-folder.md` only.
- Trailer: `Step: 5/6`

Each line of the three files is read against the code. The findings are listed for the human before any edit, each with the source line that makes it stale. Known before the review starts: `models-folder.md` says "open: JSON Schema" for structural and behavioral, and both schemas exist (`Source/models/structural.schema.json`, `Source/models/behavioral.schema.json`); `model-seam.md` carries the role word "owner" and two version notes that have passed ("written by the core in v1.1", "before plugging in at v1.2"). The words `owners` and `ownership` stay where they name the field of `ownership.json` or the model.

### Step 6/6: Delete the other diagram files and fix every reference to them

- Files: deleted with `git rm`: `docs/diagrams/comparison.md`, `cross-team-test.md`, `file-fetch.md`, `four-field-answer.md`, `init.md`, `one-check.md`. Moved with `git mv`: `docs/diagrams/research-evidence.md` to `docs/research/research-evidence.md`. References: `docs/README.md` (the `diagrams/` section rewritten for the files that remain, the moved file listed under `research/`); `docs/base/phase4.md` (line 132, D11: the citation becomes `data-flow.md` and the row gains the three measured figures it lacks: a full clone at 26 s on pytest and 155 s on Django, and file by file on Django, 81 files read in 90 s; line 172: "one-check diagram" becomes `docs/diagrams/behavior.md`); `docs/state/tracker-gaps.md` (row 3); `docs/proposals/init/init.md` (line 59); `docs/proposals/language-engine/04-one-template.md` (line 307), `06-init.md` (lines 3 and 13) and `research-multi-language.md` (line 5); `tests/ownership/test_ownership_model.py` (line 1, the comment only); `docs/state/WORK-ITEMS.md` (the open rows W0-6, W0-7 in detail, W3-5 and W5-3, where they name a deleted file as something to touch)
- Check: `git grep -n -E "(behavioral-model|comparison|cross-team-test|file-fetch|four-field-answer|one-check)\.(md|png)|diagrams/(init|research-evidence)\.md" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/closed" ":!docs/history" ":!.claude/permissions-checklist.md" ":!docs/epics/E02-system-models"` → prints nothing
- Trailer: `Step: 6/6`

One commit holds the deletions, the move and every reference fix. Before it, each deleted file is read once more against the three models, so that nothing still true is lost.

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`. The branch is pushed only on the human's word, so this line can pass only after that.
2. Spec lines updated: `git grep -n "diagrams/behavior.md" -- docs/base/specifications.md` → one line, `docs/base/specifications.md:294`, and `git diff --stat main...HEAD -- docs/base/specifications.md` lists the file
3. No open row for this Epic: `git grep -n "E02" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass. It includes the human's approval of `data-flow.md`, `behavior.md` and `README.md`.

This Epic's own:

5. The folder holds the five models, the README and the renderer, and nothing else: `git ls-files docs/diagrams` → exactly seven lines: `docs/diagrams/README.md`, `docs/diagrams/behavior.md`, `docs/diagrams/data-flow.md`, `docs/diagrams/dependency.md`, `docs/diagrams/model-seam.md`, `docs/diagrams/models-folder.md`, `docs/diagrams/render.py`
6. Each file holds at most one Mermaid block, with `accTitle` and `accDescr`: `python -m pytest tests/docs -q` → ends with a line beginning `6 passed`
7. No live file cites a deleted one: the check command of step 6 → prints nothing
8. Both new models hold exactly one Mermaid block and name their sources: `git grep -c -E "^(.{3}mermaid|## Every ending|## Premises, verified)" -- docs/diagrams/data-flow.md docs/diagrams/behavior.md` → `docs/diagrams/behavior.md:3` and `docs/diagrams/data-flow.md:2`
9. The rename is a rename: `git log -M --diff-filter=R --name-status --format= main..HEAD -- docs/diagrams/` → has the line `R100`, `docs/diagrams/behavioral-model.md`, `docs/diagrams/behavior.md`
10. No page in the folder carries the role word or a known stale line: `git grep -n -i -w -E "owner|in v1\.1|at v1\.2|open: JSON Schema" -- docs/diagrams/` → prints nothing
11. The research table moved: `git ls-files docs/research/research-evidence.md` → `docs/research/research-evidence.md`
12. No new CI check and no code change: `git diff --stat main...HEAD -- .github .importlinter Source requirements.txt requirements-dev.txt pyproject.toml` → prints nothing
13. The docs map has an entry for every file in the folder: ``for f in $(git ls-files docs/diagrams); do git grep -q "^- \`diagrams/$(basename $f)\` " -- docs/README.md || echo $f; done`` → prints nothing
14. The level 6 line names the five models: `git grep -c -E "dependency\.md.*data-flow\.md.*behavior\.md.*models-folder\.md.*model-seam\.md" -- CLAUDE.md` → `CLAUDE.md:1`

Closing. This Epic has no W-row to mark done. Its closing commit, `Step: close`, moves the folder to `docs/closed/`, sets `Status: closed`, and in `docs/state/WORK-ITEMS.md` rewrites the Next action lines: step 0.6b becomes a Done line with the closed path, and the next step is named. It also moves the two `epics/E02-system-models/` entries of `docs/README.md` under `closed/`.

## Open questions

None the draft could not answer for its own work. One question found while planning is the human's and is not this Epic's to settle: whether the CLI's exit 1 with a traceback on a git failure is a defect. It has row CLI-1 in `docs/decisions/OPEN-DECISIONS.md`. The models draw the behaviour as it is today, so the row does not block this Epic.

For the rest: The four calls that were the human's were asked and answered on 2026-11-21 and are recorded under Goal. The six places where the code and the build order's wording disagree are in `DESIGN.md`, "Where the code and the build order disagree"; in each the code wins, as the human asked, so none is an open question.

## Review

RATIFY · design-reviewer at 2230f2d · 2026-11-21

- Every `file:line` cited by `DESIGN.md` holds at `2230f2d`. `git diff --stat 21e7921 HEAD -- Source tests docs/diagrams docs/contract .claude` prints nothing, and each cited line was reread: `analysis.py:36-121`, `:66-67`, `:72-90`, `:83`, `:93-98`, `:117-120`, `:132`, `:143-146`; `check.py:36`, `:94-99`, `:122-136`, `:167-205`, `:211-213`, `:216-250`, `:223`, `:224`, `:232`, `:244`, `:263-287`, `:349`, `:412`, `:455`; `cli.py:43-65`; `fetch.py:64-133`, `:101-107`, `:256-291`; `settings.py:30`, `:39-43`, `:50-54`, `:68-71`; `runs.py:27-44`; `api.py:33-40`, `:77-91`, `:169-206`; `common.py:14`, `:33`; `mapping-v1.1.yaml:78`; `.claude/settings.json:13-14`; `test_diagrams.py:18-20`; `render.py:25-27`; `specifications.md:294`, `:342-346`; `phase4.md:132`, `:172`; `file-fetch.md:30-32` (seven figures, four of them in D11).
- The commands the premises name hold. `python -m pytest tests/docs -q` prints `11 passed`. `PYTHONPATH=Source python -m drifter.cli check` prints `MODELS_NOT_FOUND` and exits 2. `check 0000000` ends in `subprocess.CalledProcessError` and exits 1. The three schemas exist. `.github/workflows` holds only `ci.yml`. `git ls-files docs/diagrams` lists eleven `.md` files and `render.py`.
- The third draft's answer to the second review holds. The checks of steps 1 and 3 and Done 8 no longer use `$`. On this CRLF clone, `git grep -c -E "^(.{3}mermaid|## Every ending|## Premises, verified)" -- docs/diagrams/` prints `behavioral-model.md:1` today. Steps 1 and 4 now list `docs/README.md`.
- Each check was simulated in a CRLF clone in the scratchpad (`core.autocrlf=true`), and none passes before its step is done. Step 2's `git mv` with its reference fixes gives `R100 docs/diagrams/behavioral-model.md docs/diagrams/behavior.md` (Done 9). After that commit, step 3's check prints `behavior.md:1`, and `specifications.md:294` is the one line for Done 2. A CRLF `data-flow.md` with one fence and the premises heading prints `:2` for step 1. A CRLF README with five rows prints `:5` for step 4. After step 6's `git rm` and `git mv`, Done 5 lists exactly the seven files, Done 11 prints the moved path, Done 6 prints `6 passed`, and Done 9 still shows the R100 line. Step 1's `12 passed` follows from 11 pages plus one.
- Step 2's grep prints exactly the four files step 2 lists: `CLAUDE.md:14`, `docs/README.md:38`, `specifications.md:294` and `diagrams/init.md:7`. Step 6's grep prints exactly the files step 6 lists. `phase4.md:172` ("one-check diagram") cannot match the pattern and is listed by name. A wider search finds no other live file that names a deleted diagram: the `init.md` hits in `owner-approval.md`, `mage_take.md` and `language-engine/README.md` are `proposals/init/init.md` or the proposal's own `06-init.md`. The `WORK-ITEMS.md` rows step 6 names are W0-6 (line 91), the W0-7 detail (line 122), W3-5 (line 188) and W5-3 (line 221). Lines 59, 60 and 86 are dated records.
- Step 5's check and Done 10 print `model-seam.md:3, 5, 12, 34, 39, 43, 45, 52, 54, 63, 67` and `models-folder.md:27, 35` today, so each fails until the review is done. Done 3, 12 and 14 print nothing today. Done 13 prints nothing today and would print `data-flow.md` or `README.md` if either entry were missing.
- The filled-copy check prints nothing for `EPIC.md` or `DESIGN.md`. Every step names its files, one check with its output, and its trailer. Every Done line is a command, except line 4, the human's acceptance. `DESIGN.md` exists, as the Epic changes models in `docs/diagrams/` (`docs/epics/README.md:12`). Nothing contradicts a higher level: the spec, the contract and INV-1 to INV-3 are untouched, and `RULED/` holds only its README. The one human question has row CLI-1 (`docs/decisions/OPEN-DECISIONS.md:23`), and no row names `E02`.
- Minor, not needed for RATIFY: Done 10 searches the whole folder with `-w owner`, so the new `behavior.md` fails it if it quotes the request format "owner/name" (`analysis.py:31`, `:42`; old `one-check.md:13`). Name the format some other way, or narrow the pattern. Step 5's note "at `01c2ab2` the command prints" is still true at `2230f2d`. Step 6's check excludes `WORK-ITEMS.md`, so the repointing of rows W0-6, W0-7, W3-5 and W5-3 is confirmed by reading those rows, not by the command.

REVISE · design-reviewer at babb82f · 2026-11-21

Holding, checked at `babb82f`: each `file:line` that `DESIGN.md` cites says what it claims (`analysis.py:36-121`, `:66-67`, `:83`, `:93-98`, `:117-120`, `:132`, `:143-146`; `check.py:36`, `:94-99`, `:122-136`, `:167-205`, `:216-250`, `:263-287`, `:455`; `cli.py:43-65`; `fetch.py:64-133`, `:107`, `:256-291`; `settings.py:30`, `:39-43`, `:50-54`, `:68-71`; `runs.py:27-44`; `api.py:33-40`, `:77-91`, `:169-206`; `common.py:14`, `:33`; `mapping-v1.1.yaml:78`; `.claude/settings.json:13-14`; `test_diagrams.py:18-20`; `render.py:25-27`). `python -m pytest tests/docs -q` prints `11 passed`. `PYTHONPATH=Source python -m drifter.cli check` prints `MODELS_NOT_FOUND`, exit 2; `check 0000000` ends in `subprocess.CalledProcessError`, exit 1. The three schemas exist; `.github/workflows` holds only `ci.yml`. The step 2 and step 6 greps match exactly the files those steps list (`phase4.md:172`, which they cannot match, is listed by name). The filled-copy check prints nothing for both files. No `E02` in `OPEN-DECISIONS.md`; row CLI-1 exists, so the one open question has its row (R1). Of the nine first-review findings, seven are answered on disk: step 5 and Done 10 now print `model-seam.md:3, 5, 12, 34, 39, 43, 45, 52, 54, 63, 67` and `models-folder.md:27, 35` today; `docs/README.md:42` is named; Done 13 is anchored and prints `data-flow.md` and `README.md` when they lack an entry; step 2 writes the level 6 line in Done 14's order; Done 2 is a `git grep`; `file-fetch.md:26-32` holds seven figures and `phase4.md:132` four, so the three carried over are right; the pytest lines say "a line beginning"; the Closing paragraph replaces the W-row. The first two (the checks of steps 1 and 3, and a Done line for one block in each new model) are answered with commands that do not work on this clone. This is the one change needed for RATIFY:

- The checks of step 1, step 3 and Done 8 search the working tree with a `$` anchor, and this clone checks files out with CRLF (`core.autocrlf` is `true`; `git ls-files --eol docs/diagrams` shows `i/lf w/crlf`). On a CRLF line, `$` does not match after `mermaid`, so the result depends on how the file was written, not on what it says. Today `git grep -c -E "^(.{3}mermaid|## Every ending|## Premises, verified)" -- docs/diagrams/` prints only `docs/diagrams/file-fetch.md:1`, the one LF file, although every page has a fence. So step 3's claim "Before this step the same command prints `:1`" fails: after the `git mv` of step 2, `behavior.md` is still CRLF and the command prints nothing. And Done 8 cannot print `behavior.md:3` on any CRLF checkout, the auditor's included. Fix: search the index or the commit, not the working tree. For steps 1 and 3, after `git add`: `git grep --cached -c -E "…$" -- docs/diagrams/data-flow.md` (step 1), the same for `behavior.md` (step 3). For Done 8: `git grep -c -E "…$" HEAD -- …`, which prints `HEAD:docs/diagrams/behavior.md:3` and `HEAD:docs/diagrams/data-flow.md:2`. Or drop the trailing `$`. Both forms print `behavioral-model.md:1` today. Then restate each expected output (EPIC.md:37, :53, :98; DESIGN.md "Must stay true", "The code is the source").
- Minor, not needed for RATIFY: steps 1 and 4 add a file to `docs/diagrams/` without its line in `docs/README.md`, which asks that the map be kept current when a file is added (`docs/README.md:7`). Step 6 adds both lines. If the map should be right at every commit, add each line in the step that creates the file.

**Third draft, 2026-11-21.** The second review's one finding is fixed: the checks of steps 1 and 3 and Done 8 no longer end their pattern with `$`, which never matched in a working copy with CRLF line endings. Without it the command prints `docs/diagrams/behavioral-model.md:1` today. Its minor point is taken too: steps 1 and 4 add their file's entry to `docs/README.md`.

**Second draft, 2026-11-21.** The first review, kept below, asked for nine changes, and each is made: the checks of steps 1, 3, 4 and 5 and Done 2, 6, 8, 10 and 13 are rewritten so that none passes before its work is done; step 2 writes out the level 6 line; step 5 names `docs/README.md:42`; the D11 count in `DESIGN.md` is corrected and the third figure is carried over; the CLI question has row CLI-1 in `docs/decisions/OPEN-DECISIONS.md`; and a Closing paragraph says what the closing commit updates in place of a W-row.

### First review

REVISE · design-reviewer at 01c2ab2 · 2026-11-21

Holding: every `file:line` in `DESIGN.md` says what it claims (`analysis.py`, `check.py`, `cli.py`, `fetch.py`, `settings.py`, `runs.py`, `api.py`, `common.py`, `mapping-v1.1.yaml:78`, `.claude/settings.json:13-14`, `test_diagrams.py:18-20`, `render.py:25-27`); `pytest tests/docs -q` prints `11 passed`; `PYTHONPATH=Source python -m drifter.cli check` prints `MODELS_NOT_FOUND` and exits 2; `check 0000000` ends in `CalledProcessError` and exits 1; the three schemas exist; `.github/workflows` holds only `ci.yml`; the step 2 grep today matches exactly the four files step 2 lists, and the step 6 grep matches exactly the files step 6 lists plus the excluded dated records; the filled-copy check prints nothing for both files; no `E02` row in `OPEN-DECISIONS.md`. Must change for RATIFY:

- Step 3's check does not mean done: `python -m pytest tests/docs -q -k behavior` prints `1 passed, 10 deselected` today (it matches `behavioral-model.md`) and after step 2, before step 3 starts. Use a check only the extended file passes, e.g. `git grep -c -E "^## Premises, verified|CHANGE_LIMIT_EXCEEDED|^\`\`\`mermaid" -- docs/diagrams/behavior.md` with its count, beside the pytest line (`tests/docs/test_diagrams.py:14`, substring `-k`).
- Step 1's check passes on a `data-flow.md` that has no diagram, since the test returns early on a page without a block (`tests/docs/test_diagrams.py:18-19`). Add a count of the Mermaid fence and the "Premises, verified" heading. The same gap leaves Done 6 unable to show that `data-flow.md` and `behavior.md` each hold one block; add a Done line for it.
- Step 5's check (and Done 10) prints nothing while the role word stays: it misses "element lists of the owner's choice" (`docs/diagrams/model-seam.md:12`) and "the owner's generator", "the owner's schema", "the owner's propose function" (`model-seam.md:39`), and the known stale line "written by the core in v1.1" (`model-seam.md:67`). Use e.g. `git grep -n -i -w "owner" -- docs/diagrams/` (matches "owner" and "owner's", not "owners" or "ownership") plus a pattern for the version notes. Step 5 also leaves `docs/README.md:42` ("the three model owners", "an owner's model") optional; name it as a file to fix.
- Done 13 already passes for `behavior.md` and `data-flow.md` through `docs/README.md:97`, the E02 Epic's own line, which stays after close. Anchor the grep to the `diagrams/` section entries, e.g. ``git grep -q -E "^- \`diagrams/$(basename $f)\` " -- docs/README.md``.
- Done 14's regex fixes the order dependency, data-flow, behavior, models-folder, model-seam, but step 2 does not say where `data-flow.md` goes in the level 6 line (`CLAUDE.md:14`). Write the new line in step 2, or make the check order-free.
- Done 2's command, `git diff --stat`, cannot print that line 294 names `behavior.md`. Use `git grep -n "diagrams/behavior.md" -- docs/base/specifications.md` → `docs/base/specifications.md:294:...`.
- DESIGN.md, the file-fetch row, fails: "D11 already holds three of the five". `docs/base/phase4.md:132` holds four figures (fixture, pytest batch, Django batch, pytest blob by blob); `docs/diagrams/file-fetch.md:30-32` holds seven. "Django: 81 files read in 90 s" (`file-fetch.md:32`) is neither carried to D11 nor listed under "Not carried over". Correct the count, and say where that figure goes or that it is dropped.
- A human's call has no row (R1): DESIGN.md:80 leaves open whether the CLI's exit 1 with a traceback for an unknown commit (`cli.py:43-54`, `check.py:455`, the same code as drift) is a defect. The spec says an unknown commit is a 404 with a message, and a no-verdict check is exit 2 (`docs/base/specifications.md:342-346`). Add a row to `docs/decisions/OPEN-DECISIONS.md` and cite it from DESIGN.md.
- Minor: the step checks print `1 passed, N deselected in …s`, not `1 passed`. State the expected line as "a line beginning `1 passed`". There is no W-row, and the close step in `docs/epics/README.md:23` marks one done, so say what the closing commit updates instead (the Next action line of `WORK-ITEMS.md`).

# The data-flow and behavior models

Epic: `docs/epics/E02-system-models/EPIC.md`

## Intended structure

`docs/diagrams/` ends with seven files. No model names who owns a file or folder.

| File | Kind | The question it answers | Mermaid block |
|---|---|---|---|
| `README.md` | index, new | which model answers my question, and how do I read it? | none |
| `dependency.md` | system model, kept | who reaches the core, through which entry point, and which module may import which? | one flowchart, unchanged |
| `data-flow.md` | system model, new | if I change this step, what sees it downstream? | one flowchart |
| `behavior.md` | system model, renamed from `behavioral-model.md` | what can happen to a request, and what does the user see? | one state diagram |
| `models-folder.md` | format model, kept | which four files does `/models` hold, and what does each contain? | one class diagram, stale lines fixed |
| `model-seam.md` | format model, kept | what does each generator write, and what does the core do with it? | one flowchart, the role word removed |
| `render.py` | tool, kept | none | none |

### data-flow.md

One flowchart, top to bottom. It names the boxes of `dependency.md` (the CLI, the hosted `/system`, the git readers, the generators, the ownership check, the comparison, the result store) and does not redraw who calls whom.

- **Two ways in to one check.** Hosted: `POST /system/analyze` goes through `GitHub_Connector.analysis` and `GitHub_Connector.fetch`, which make a fresh blobless clone without a checkout and read the files of one commit from it. CLI: `drifter check` reads a local checkout through `LocalReader`. Both hand a reader to `drifter.check.read_sources`, and both call `drifter.check.answer`. That is where they meet.
- **Inside the check.** `read_sources` reads the four `/models` files, validates them, picks the in-scope files with `scope.json`, reads and parses them, and reads the commits base..head. `answer` regenerates structural and behavioral and diffs each by id against the committed model, and judges the commits against `ownership.json`.
- **What is regenerated and what is only read.** A check regenerates structural and behavioral in memory and writes nothing. `ownership.json` and `scope.json` are only read by a check and by `drifter update`. The writers are drawn as their own, smaller flow: `drifter init` writes all four files, `drifter update` writes structural and behavioral only, and a person edits ownership and scope by hand.
- **What only the hosted way adds.** Change detection (`changes`, `skipped`, `unmapped`) is computed from the clone's diff and the mapping file and does not pass through `drifter.check`. `GitHub_Connector.runs` saves the result as one file in the run store. The CLI saves nothing.
- **The other callers of the same steps,** named in one table and not drawn: `POST /system/generate` (`check.generate_models` on a clone, returns four files, saves nothing) and `GET /models/view` (the console's page).
- **Below the diagram,** one table: each step, what it reads, what it writes, and what sees a change to it downstream. Then "Premises, verified", one row per arrow, store and limit, with its source line.

### behavior.md

One state diagram. The lifecycle of a repository stays: No models, Proposed, Baselined, a check, and its endings. The check is a composite state that holds the states of one `POST /system/analyze` run, in the order the code reaches them: validate, wait for a slot, clone, resolve the commits, detect changes, check drift, save, answer.

Below the diagram, one table of every ending. Each row gives the HTTP status, the error code or the fields that tell the endings apart, what the caller sees, and whether a run file is saved. The rows, from the code:

| Ending | HTTP | Saved? |
|---|---|---|
| aligned | 200, `drift.aligned` true | yes |
| drift | 200, `drift.aligned` false | yes |
| no verdict: `MODELS_NOT_FOUND`, `INVALID_MODELS`, `FILE_TOO_LARGE`, `PARSE_FAILED` | 200, `drift` null and a `drift_error` | yes |
| over the change limit: `CHANGE_LIMIT_EXCEEDED` | 200, `status` ERROR, the three change lists empty; `drift` or `drift_error` is still filled | yes |
| `INVALID_REQUEST` | 400 | no |
| `REPOSITORY_NOT_FOUND`, `COMMIT_NOT_FOUND` | 404 | no |
| `ANALYSIS_FAILED`: the 80 s deadline, a git call over 60 s, a failed batch download, or any crash | 500 | no |
| `STORAGE_FAILED` | 500 | no |

A second, shorter table gives the same endings for `drifter check` as exit codes, and `GET /system/analysis/{id}` with its one 404. Then "Premises, verified", one row per state, status code and limit.

The lifecycle is corrected where the code disagrees with the old drawing: a fetch error is a 500 with nothing saved, not a no-verdict ending.

### README.md

A table, one row per model: the question it answers, and how to read it (what a box, an arrow or a state stands for). One paragraph on the authority order: every model in the folder is level 6 in `CLAUDE.md`, below the spec, and a model that disagrees with the spec is fixed. One line that the cross-team test session and the grading of a drift test are defined in `docs/contract/pod-contract.md`. One line on `render.py`.

### Where the content of each deleted file goes

| File | Still true, by the code | Goes to | Not carried over |
|---|---|---|---|
| `one-check.md` | The order of one check and the code each step can end with (`Source/GitHub_Connector/analysis.py:36-121`, `Source/drifter/check.py:216-250`). The two kinds of stop: an HTTP error saves nothing; no verdict keeps 200. The 80 s deadline. | The steps to `data-flow.md`. The stops and codes to `behavior.md`. | "pinned CPython ast": the code calls `ast.parse` of whichever Python runs it (`Source/models/common.py:33`). The PR check box: the Action is not built, and `dependency.md` already draws it dashed. |
| `init.md` | `drifter init` writes four files and refuses with exit 1 when one exists and `--force` is absent (`Source/drifter/cli.py:57-65`). Structural and behavioral from the in-scope files with the default scope, ownership proposed from all history (`Source/drifter/check.py:263-276`). `drifter update` rewrites two files from the committed scope (`check.py:279-287`). `/system/generate` runs the same `generate_models`. | The writers' flow and the read and write table of `data-flow.md`. The exit 1 refusal to the lifecycle text of `behavior.md`. | The table of what to type: `drifter init --help` says it. The mining constants (10 commits, 50 files): `model-seam.md` already has them. |
| `file-fetch.md` | The four steps: a blobless clone without checkout, `ls-tree`, a batched download, reads with lazy fetching off; two batches per check; a missing blob ends in 500 `ANALYSIS_FAILED`; the clone is deleted (`Source/GitHub_Connector/fetch.py:64-133`, `256-291`). | The hosted way in of `data-flow.md`. The measured times to row D11 of `docs/base/phase4.md`, which already holds three of the five. | "to be measured again on Railway (v1.1)" and "about 10 lines in the file reader (v1.1)": dated notes. The "left out" list: none of it is built. |
| `comparison.md` | ADDED, REMOVED, MODIFIED by element id (`check.py:122-136`). A violation per path of a non-merge commit, first matching rule wins, no rule means anyone, a rename is judged at its old path (`check.py:167-205`). | Already in `model-seam.md`, whose diagram draws both. `data-flow.md` names the two steps and points there. | Nothing. |
| `four-field-answer.md` | The four fields of the answer: `aligned`, `structural`, `behavioral`, `ownership` (`check.py:94-99`). | The endings table of `behavior.md`. | How a tester grades T-26: dropped by the human's decision, the contract states it. |
| `cross-team-test.md` | The system's side of a session is in `Source/GitHub_Connector/course.py`. | Nothing moves. The README points to `docs/contract/pod-contract.md`. | The whole session flow: dropped by the human's decision. One line was stale besides: "T-24 to T-33: skip until the model fixture exists", and `docs/contract/model-golden-outputs.json` exists. |
| `research-evidence.md` | A table of tool research. | `docs/research/research-evidence.md`, moved whole. | Nothing. |

### Where the code and the build order disagree

The build order's text for step 0.6b, as the human gave it, against the code. The code wins in each.

| The build order says | The code says | Source |
|---|---|---|
| The hosted `/system/analyze` clones one commit. | It clones the repository blobless and without a checkout: every commit and folder listing, no file contents. Files are then downloaded for one commit, in two batches. | `fetch.py:282-285`, `fetch.py:101-104`, `check.py:224` and `check.py:232` |
| `runs.py` stores runs on the volume. | It stores them in `runs_dir`. That is the Railway volume when one is mounted, and otherwise a local `runs` folder that a redeploy wipes. On Railway the app refuses to start without a volume. The CLI never saves a run. | `settings.py:30`, `settings.py:50-54`, `settings.py:68-71`, `runs.py:27-44` |
| Ownership and scope are edited by hand and only read. | A check and `drifter update` only read them. `drifter init` writes both, and `--force` replaces a hand-edited copy. | `check.py:263-270`, `cli.py:57-65`, `check.py:282-287` |
| The endings are aligned, drift, no verdict, and the 400, 404 and 500 cases. | There is one more: 200 with `status` ERROR and `CHANGE_LIMIT_EXCEEDED`, when more than 2000 files changed. It is saved, and it carries a drift answer or a drift error as well, because drift is checked before the limit. | `analysis.py:83`, `analysis.py:93-98`, `docs/contract/mapping-v1.1.yaml:78` |
| Both ways in meet at `drifter.check`. | True for the drift answer. The hosted answer also carries change detection, which never passes through `drifter.check`. Two more routes reach the same core: `/system/generate` and `/models/view`. | `analysis.py:72-90`, `analysis.py:144`, `cli.py:49`, `analysis.py:132`, `api.py:169-206` |
| A failed check ends with exit 2 and no verdict (the lifecycle in `behavioral-model.md`: "Failed: fetch error"). | Hosted, a fetch error is a 404 or a 500 and nothing is saved; even a failed download inside the drift check is a 500, not a no-verdict answer. In the CLI, a git failure such as an unknown commit is an uncaught error: a traceback and exit 1, the same exit code as drift. | `fetch.py:107`, `analysis.py:143-146`, `cli.py:43-54`, `check.py:455` |

The last row's CLI behaviour is drawn as it is. Whether exit 1 for an unknown commit is a defect to fix is not this Epic's call: it changes no code.

## Premises, verified

Every fact the structure rests on, checked against the disk on 2026-11-21 at `21e7921`. Each model carries its own, longer table, written in steps 1 and 3.

| Premise | How verified | Holds? |
|---|---|---|
| `docs/diagrams/` holds eleven `.md` files and `render.py`. | `git ls-files docs/diagrams` | yes |
| The docs test passes today and allows a page with no Mermaid block. | `python -m pytest tests/docs -q` printed `11 passed`; `tests/docs/test_diagrams.py:18-19` returns when a page has no block | yes |
| The docs test fails a page with two blocks, so `behavior.md` must draw the lifecycle and the run in one. | `tests/docs/test_diagrams.py:20` | yes |
| `render.py` passes over a page with no block. | `docs/diagrams/render.py:25-27` | yes |
| `data-flow.md`, `behavior.md` and `model-seam.md` prompt the human on Edit; `README.md` and `models-folder.md` do not. | `.claude/settings.json:13-14` lists `dependency.md`, `data-flow.md`, `behavior.md` and `model-seam.md` | yes |
| Both ways in call `read_sources` and `answer` of `drifter.check`. | `Source/GitHub_Connector/analysis.py:144`; `Source/drifter/cli.py:49` with `Source/drifter/check.py:211-213` | yes |
| The four no-verdict codes are raised in `drifter.check` and caught as a 200. | `check.py:223`, `check.py:244`, `check.py:349`, `check.py:357-412`, `Source/models/common.py:14`; caught at `analysis.py:145-146` | yes |
| The status of each error code is in one table. | `Source/GitHub_Connector/api.py:33-40`: 400, 404, 404, 404, 500, 500 | yes |
| A request FastAPI rejects is a 400, never a 422. | `api.py:85-91` | yes |
| An unexpected failure is a 500 `ANALYSIS_FAILED`. | `api.py:77-82` | yes |
| A run is saved once, after the clone is deleted, and a failed save is a 500 `STORAGE_FAILED`. | `analysis.py:117-120`; `Source/GitHub_Connector/runs.py:32-44` | yes |
| An HTTP error saves nothing: every one is raised before `runs.save`, or by it. | `analysis.py:65`, `analysis.py:72`, `analysis.py:118` | yes |
| The limits: 80 s per analysis, 60 s per git call, 2 analyses at once, 1 MB per in-scope file, 2000 changed files. | `Source/GitHub_Connector/settings.py:39-43`; `check.py:36`; `docs/contract/mapping-v1.1.yaml:78` | yes |
| The deadline starts once a slot is free, and the wait for a slot has no limit. | `analysis.py:66-67` | yes |
| The CLI exits 0 when aligned, 1 on drift, 2 with no verdict. | `cli.py:50-54`; `python -m drifter.cli check` on this repository printed `MODELS_NOT_FOUND` and exited 2 | yes |
| An unknown commit makes the CLI exit 1 with a traceback. | `python -m drifter.cli check 0000000` ended in `subprocess.CalledProcessError` and exit 1 | yes |
| The JSON Schemas that `models-folder.md` calls open exist. | `Source/models/structural.schema.json`, `Source/models/behavioral.schema.json`, `Source/models/ownership.schema.json` | yes |
| The GitHub Action that `dependency.md` draws dashed is still not built. | `.github/workflows` holds only `ci.yml` | yes |
| The live files that cite a file this Epic deletes, moves or renames are the ones steps 2 and 6 list. | `git grep -n -E "(behavioral-model\|comparison\|cross-team-test\|file-fetch\|four-field-answer\|one-check)\.(md\|png)\|diagrams/(init\|research-evidence)\.md"` over the repository, less the dated records | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| One block per page | Each page in `docs/diagrams/` holds at most one Mermaid block, with `accTitle` and `accDescr`. | `python -m pytest tests/docs -q` → all pass; it already runs in CI with `pytest` |
| No owners | No model names who owns a file or folder, and none uses "owner" as a role. | The check command of step 5 of the Epic prints nothing; beyond those patterns, guidance only: the human's review at each prompt |
| The code is the source | Every state, status code and limit drawn in `data-flow.md` and `behavior.md` has a row in that file's "Premises, verified" with its source line. | `git grep -c "^## Premises, verified" -- docs/diagrams/data-flow.md docs/diagrams/behavior.md` → one each; that each row is right is guidance only: the human's review at each prompt. No CI check is added, by the human's decision. |
| Level 6 is the folder | The level 6 line of `CLAUDE.md` names the five models the folder holds. | Done criterion 14 of the Epic |
| INV-1, INV-3 | The answer's bytes and the import map do not change. | `git diff --stat main...HEAD -- Source .importlinter` → prints nothing |

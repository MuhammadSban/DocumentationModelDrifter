# E07: Who writes /models

Status: ratified · Owner: Kaan

W-row: W0-6 (build order step 1.1) in `docs/state/WORK-ITEMS.md` · Branch: `E07-who-writes-models`

## Goal

Both models of `/models` say who may write each of its four files. When this Epic closes, `docs/diagrams/models-folder.md` carries the "## Who writes /models" table that `docs/diagrams/data-flow.md:71-79` has carried since E02. The two tables are identical. In both, the last row says what a hand edit to `structural.json` or `behavioral.json` does since volatility arrived (PR #61): every check lists it, and it is drift at the default volatility, 1 (Exact). A new test in `tests/drifter/test_cli.py` guards the behavioral half of that row. The structural half is already guarded by golden case L7. The team needs it because `models-folder.md` is the model a reader opens to learn what `/models` holds, and today it does not say that two of its files are written only by `drifter init` and `drifter update` (`docs/proposals/init/init.md:59`, fix 4). No route, answer or generator changes.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/models-folder.md` changes: it gains the table. `docs/diagrams/data-flow.md` changes: its last table row, `:79`, gains the volatility qualifier, so the two copies stay identical (decided by the human, W0-6 row). Neither drawing changes, and no part, flow or run state changes. `DESIGN.md` sits beside this file because the Epic changes two models in `docs/diagrams/` (decided by the human, W0-6 row).
- Rulings: none. `docs/decisions/RULED/` holds only its README. The W0-6 row carries the calls marked "Decided by the human, 2026-11-22".
- Invariants: INV-2 is read, not changed: the table repeats that ownership and scope are edited by hand, and it says nothing about who may edit them, which INV-2 and row W0-7 leave open. INV-1 and INV-3 are not touched: no file under `Source/` changes.
- Other sources: `docs/contract/pod-contract.md:132` (L7 is "a hand edit removes an `inherits` edge from `structural.json` that the code still makes"); `docs/contract/model-golden-outputs.json` case L7 (`aligned` false, one structural `ADDED` `inherits:store:OrderStore->store:Store`); `Source/Tester/pod_tests.py:359` (T-31); `tests/connector/test_model_golden.py:23` (L7 exits 1); `Source/drifter/check.py:91-107` (`answer`, with volatility) and `:119-131` (`EXACT`, `TOLERATED`); `Source/drifter/check.py:199-209` (ADDED means in the code but not in the model).

### Facts this Epic rests on, checked at `18c69ff`

- `origin/main` is `18c69ff`, the merge of PR #61, two commits after `bb9d840`. PR #61 (`ea3b270`) added `volatility` to `scope.json`, with levels 1 to 4 tolerating 0, 3, 9 and 29 changed elements per model (`Source/drifter/check.py:119-131`). The default is 1, Exact. `drifter init` writes no `volatility` key, so a freshly initialised repository is at Exact. No file under `docs/` names volatility: `grep -rni volatil docs` finds only one unrelated research line.
- `data-flow.md:71` is `## Who writes /models`. Its table, `:73-79`, has five writer rows: `drifter check` and `POST /system/analyze`, `drifter init`, `drifter update`, `POST /system/generate`, and a person. The columns are `structural.json, behavioral.json` and `ownership.json, scope.json`. The last row, `:79`, says "not by hand: a hand edit that does not match the code shows as drift on the next check". Since PR #61 that holds at volatility 1 only. At 2 to 4 the edit is still listed, but `aligned` stays true while the model carries no more changes than the level tolerates (`check.py:97-107`).
- `models-folder.md` has two headings, `# The /models folder` and `## The verbosity ladder`, and no table of writers. It ends with the ladder's closing paragraph.
- On Windows the checked-out docs have CRLF line ends (`core.autocrlf` is `true`), so a check that anchors a line end with `$` finds nothing here and finds the line on CI's Linux runner. The checks below do not anchor line ends, and they strip `\r` where they compare lines.
- `git grep -c "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` prints `docs/diagrams/data-flow.md:1` today, and nothing for `models-folder.md`.
- L7 is the structural proof: `pod-contract.md:132` and the golden case above; T-31 replays it against a system (`pod_tests.py:359`) and `test_model_golden.py` against ours.
- No test hand-edits `behavioral.json` and then checks for drift. `git grep -n "behavioral.json" -- tests` finds tests that write a broken or empty one (INVALID_MODELS cases, `_repo`'s default) or regenerate it (`test_update_regenerates_behavioral_as_init_writes_it`), and none that removes an element and runs `check`.
- `tests/drifter/test_cli.py` already has the fixtures the new test needs: `MACHINE` (`src/order.py`, `self.status` `'open'` to `'paid'`), `_code_repo`, `_run`, `_commit` and `_check`. `test_a_new_elif_state_is_one_added_state_and_one_added_transition` shows the shape of a behavioral answer. The behavioral miner finds 0 states in this repository's own 30 non-test `.py` files, so the test builds its own repository.
- The behavioral schema checks each transition's fields, not that its `source` and `target` name a state that exists (`Source/models/behavioral.schema.json`), and `_element_rule` checks ids, kinds and files only (`check.py`). So removing one state by hand leaves a valid model.
- CI is green on `18c69ff`: run 45100999452, `465 passed, 1 warning`, then ruff `All checks passed!`. A local run on Windows, Python 3.13, also gave `465 passed`.
- E07 is the next free number: `docs/closed/` ends at E06 and `docs/epics/` holds only its README.

## Steps

One commit per step, made after the step's check passes.

### Step 1/2: guard that a hand edit to behavioral.json is drift

- Files: `tests/drifter/test_cli.py`
- What: one test, `test_a_hand_edit_to_behavioral_json_is_drift`, placed after `test_a_new_elif_state_is_one_added_state_and_one_added_transition`. It is a guard: it passes at once, because `check` already treats a hand edit as drift at the default volatility. Its seam is the drifter CLI's `main()` on a temporary git repository, as for the tests around it. It runs `_code_repo(tmp_path, MACHINE)`, then `drifter init`, then commits. It removes the state whose `value` is `"paid"` from `models/behavioral.json` and writes it back with `write_model`. It commits again and runs `drifter check`. It asserts exit code 1, `aligned` false, empty `structural` and `ownership`, and `behavioral` equal to exactly one difference: `{"change": "ADDED", "file": "src/order.py", "id": the removed state's id, "kind": "state"}`. That is ADDED because the state is in the code and not in the model (`check.py:199-209`). Its comment names the "a person" row of "Who writes /models" and the default volatility.
- Check: `python -m pytest tests/drifter/test_cli.py -q -k hand_edit_to_behavioral` → the summary line starts with `1 passed` and has no `failed`
- Trailer: `Step: 1/2`

### Step 2/2: the table in models-folder.md, its qualifier in both, and the W0-6 row

- Files: `docs/diagrams/models-folder.md`, `docs/diagrams/data-flow.md` (line 79 only; the file is on ask, so the edit stops for the human's approval), `docs/state/WORK-ITEMS.md` (Next action)
- What:
  - In `data-flow.md:79`, the last row becomes: `| a person | not by hand: a hand edit that does not match the code is listed on every check, and is drift at the default volatility, 1 (Exact); at a higher volatility it is drift only once the model carries more changes than that level tolerates | edited by hand |`. No other line of the file changes.
  - Append to `models-folder.md`, after the ladder's last paragraph, a blank line, then `## Who writes /models`, a blank line and the table, copied from `data-flow.md` lines 73 to 79 as they stand after the edit above.
  - In `WORK-ITEMS.md`, the first sentence of the Next action line "Can run beside it: W0-6 (step 1.1)." becomes "Built: W0-6 (step 1.1), Epic E07, waiting for its audit." Its second sentence, "W1-6 also unblocks W3-1 and W4-3 …", stays as it is. The W0-6 row is left as drafting wrote it.
- Check: `git grep -c "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → exactly two lines, `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`. Today it prints only the first (see Facts).
- Trailer: `Step: 2/2`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD. Lines 2 and 9 compare with `origin/main`, so run `git fetch` first: the local `main` of this checkout is stale (`ff79932`, 63 commits behind `18c69ff`).

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat origin/main...HEAD -- docs/base/specifications.md` → empty. The Epic changes no behavior, and no spec line says what a hand edit to `structural.json` or `behavioral.json` does in general (`docs/base/specifications.md:245`, `:398` and `:503` are the only lines with "by hand" or "hand edit", and each stays true)
3. No open row for this Epic: `git grep -n "E07" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The guard passes: `python -m pytest tests/drifter/test_cli.py -q -k hand_edit_to_behavioral` → the summary line starts with `1 passed` and has no `failed`
6. Both models carry the heading once: `git grep -c "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`
7. The two tables are identical: `git grep -h -A8 "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md | tr -d '\r' | grep -vx -- "--" | sort | uniq -u` → prints nothing. Each heading is followed by a blank line and the 7-line table, so `-A8` takes the table and stops before the next blank line. Today the command prints data-flow.md's heading, blank line and table, because the second copy is missing.
8. The qualifier is in both: `git grep -c "is drift at the default volatility, 1 (Exact)" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`
9. Only the one line of data-flow.md changed: `git diff --numstat origin/main...HEAD -- docs/diagrams/data-flow.md` → `1	1	docs/diagrams/data-flow.md`
10. The whole suite on CI counts the new test: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --log | grep -o "[0-9]* passed[^=]*"` → `466 passed` and no `failed`. If `tests/connector/test_golden.py` cannot reach GitHub, its tests show as skipped, and passed plus skipped is 466.

## Open questions

None: the human answered the three proposals in the W0-6 row (2026-11-22), and every fact the steps rest on was checked against the disk at `18c69ff`.

## Review

RATIFY · design-reviewer at e7efef0 · 2026-11-22

- The first finding at `b2019e8` is fixed. The Goal cites `docs/proposals/init/init.md:59` (fix 4) and no longer says E02 deleted it. `git cat-file -t HEAD:docs/proposals/init/init.md` prints `blob`. The W0-6 row (`docs/state/WORK-ITEMS.md:100`) now says only "since E02".
- The second finding is fixed. Done lines 2 and 9, and the INV-2 check in `DESIGN.md:34`, compare with `origin/main...HEAD` after `git fetch`.
- The filled-copy check in `docs/templates/README.md:14` prints nothing for `EPIC.md` or for `DESIGN.md`. Each step names its files, one check command with its output and its trailer. Done lines 1 to 3 and 5 to 10 are commands with expected output, and line 4 is the human's acceptance. Both drafting commits carry `Step: plan`.
- Step 1's prediction holds at `e7efef0`. I ran the step's body as a scratch test, since deleted: `init`, commit, remove the `"paid"` state, write it back with `write_model`, commit, then `check`. Result: exit 1, `aligned` false, empty `structural` and `ownership`, and one behavioral `ADDED` `state` in `src/order.py`, so `1 passed`. `-k hand_edit_to_behavioral` selects nothing today ("97 deselected"). The fixtures it names exist: `test_cli.py:44`, `:51`, `:500`, `:510`, `:599`, `:613`. `write_model` returns text (`Source/models/common.py:42`), so "writes it back with `write_model`" means writing that text to the file.
- These citations hold:
  - `check.py:91-107`: `answer`, tolerance and `drifted`.
  - `check.py:127` and `:131`: `EXACT`, and `TOLERATED` {0, 3, 9, 29}.
  - `check.py:198-211`: ADDED means in the code and not in the model.
  - `behavioral.schema.json:34-42`: `source` and `target` are plain strings.
  - `data-flow.md:71` and `:73-79`, with `:79` worded as quoted.
  - `models-folder.md` has the headings `:1` and `:55` only.
  - `pod-contract.md:132` (L7), `pod_tests.py:359` (T-31) and `test_model_golden.py:23` (L7 exits 1).
  - `test_cli.py:517`: init writes a `scope.json` without `volatility`.
  - `test_cli.py:815`: the volatility test.
  - `data-flow.md:130-134`: its premise rows for init, update and generate.
  - `.claude/settings.json:13`: `data-flow.md` is on ask, and `models-folder.md` is not.
  - The spec's only "by hand" lines are `:245`, `:398` and `:503`.
  - `OPEN-DECISIONS.md` has no `E07`, `RULED/` holds only its README, and `docs/closed/` ends at E06.
  - There are 30 tracked non-test `.py` files.
  - Done 6 and Done 7 print today what the Epic says they print.
- Authority order: nothing here contradicts the contract, a ruling, INV-2 or the spec. The qualifier adds volatility, which the spec does not mention, to the two models, and it agrees with `check.py:91-107`. `DESIGN.md` is present, as it must be, because two models in `docs/diagrams/` change.
- Open questions: none to settle. The human's four calls in the W0-6 row map onto the Epic as follows: the base `18c69ff` is in Facts, the copied and qualified table is in step 2, `DESIGN.md` exists, and the guard is step 1. No row in `OPEN-DECISIONS.md` is needed.
- Not blocking: `origin/main` has moved since drafting. It is now `a88e519`, after PR #62 and PR #63, so the Fact "`origin/main` is `18c69ff`" is dated. `git diff --stat 18c69ff a88e519` touches only `Source/Frontend/model_viewer.py` and `docs/invariants/INVARIANTS.md` (−3, which removes the duplicate INV rows the last review noted). It adds no test, so Done 10's `466` still holds. Done 9 and the INV-2 check still hold, because three-dot diffs compare from the merge base whether or not the branch takes `a88e519`.
- Not blocking: the Next action line in step 2 is in bold markup (`**Can run beside it:** W0-6 (step 1.1).`). Keep the bold label pattern when rewriting it.

Revised after the verdict below, on its two findings at `b2019e8`: the Goal cites `docs/proposals/init/init.md:59` and no longer says E02 deleted it, and the W0-6 row's own sentence is fixed in the same commit; Done lines 2 and 9 and `DESIGN.md`'s INV-2 check compare with `origin/main` after `git fetch`. Also from its non-blocking notes: step 2 says the second sentence of the Next action line stays, and `DESIGN.md` marks "in a reviewed commit" as what `data-flow.md` draws, not something enforced. The next reviewer writes its verdict above this paragraph.

REVISE · design-reviewer at b2019e8 · 2026-11-22

Must change for RATIFY:

- Goal: "(`proposals/init/init.md` fix 4, which E02 deleted)" does not hold. The file is still there: `git cat-file -t HEAD:docs/proposals/init/init.md` prints `blob`, and `docs/proposals/init/init.md:59` is fix 4. Drop "which E02 deleted", or say what E02 actually did. The W0-6 row's own text (`docs/state/WORK-ITEMS.md:100`, "since E02, which deleted `init.md`") has the same error. Its decided lines are not affected, so step 2 can fix that sentence, or the Epic can say why it leaves it.
- Done line 2 and line 9, and the INV-2 check in `DESIGN.md`, compare against the local `main`. On this checkout the local `main` is `ff79932`, 63 commits behind `origin/main` (`git log --oneline main..origin/main | wc -l` → 63). Before any step, `git diff --stat main...HEAD -- docs/base/specifications.md` already prints `9 +++++++--`, and `-- docs/invariants/` prints `INVARIANTS.md | 3 +++`. So line 2 and E07's INV-2 check fail for reasons that have nothing to do with E07. Name the base: either use `origin/main...HEAD` after `git fetch`, or add a line before the Done list that says the local `main` must equal `origin/main` (at `18c69ff` or later).

Checked and holding:

- `check.py:91` `answer`, `:100-101` tolerance and `drifted`, `:127` `EXACT`, `:131` `TOLERATED` {0,3,9,29}, `:198-211` `differences` (ADDED means in the code, not in the model), and `:221-223` the four-key difference.
- `behavioral.schema.json` and `_element_rule` (`check.py:444-457`) do not check that a transition's states exist.
- `data-flow.md:71` and `:73-79`, with `:79` worded as quoted. `data-flow.md` is on ask (`.claude/settings.json:13`). `models-folder.md` has two headings and no table. The heading `git grep` prints only `data-flow.md:1` today, and Done 7 today prints exactly what the Epic predicts.
- `pod-contract.md:132`, golden L7 (one structural ADDED `inherits:store:OrderStore->store:Store`), `pod_tests.py:359` T-31, `test_model_golden.py:23` L7→1.
- `origin/main` is `18c69ff`, two commits after `bb9d840`. CI run 45100999452 ran on `18c69ff`, ended `success` and logged `465 passed, 1 warning` and `All checks passed!`.
- There are 30 non-test `.py` files and the miner finds 0 states in them. `-k hand_edit_to_behavioral` selects nothing today. The only "by hand" lines in the spec are `:245`, `:398` and `:503`. No doc names volatility outside the research file.
- The fixtures and tests the Epic names exist (`test_cli.py:44`, `:51`, `:500`, `:510`, `:517`, `:599`, `:613`, `:635`, `:815`).
- Step 1's prediction holds. I ran the step's test body as a scratch test at HEAD (since deleted). It gave exit 1, `aligned` false, empty `structural` and `ownership`, and `behavioral` equal to one `ADDED` `state` with id `state:["src/order.py","order:Order","self.status","paid"]`: `1 passed`.
- Open questions: none. Each of the human's four calls in the W0-6 row is carried into the steps. No row in `OPEN-DECISIONS.md` is needed.

Not blocking:

- Step 2 rewrites the Next action line `WORK-ITEMS.md:20`. That line has a second sentence ("W1-6 also unblocks W3-1 and W4-3 …"). Say whether it stays.
- `DESIGN.md` says ownership and scope are edited "in a reviewed commit". The table only says "edited by hand", and nothing enforces a review while INV-2 is DEFERRED. Align the wording, or mark that phrase as the intended rule.
- Outside E07, for the human: `models-folder.md`'s `scope.json` class lists `verbosity` but not `volatility`, an R6 gap left by PR #61. `docs/invariants/INVARIANTS.md:16-21` holds INV-1 to INV-3 twice, with different text, which looks like a merge artifact. `docs/proposals/init/init.md:30` still says any hand edit "shows up as drift".

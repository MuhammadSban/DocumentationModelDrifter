# E07: Who writes /models

Status: draft · Owner: Kaan

W-row: W0-6 (build order step 1.1) in `docs/state/WORK-ITEMS.md` · Branch: `E07-who-writes-models`

## Goal

Both models of `/models` say who may write each of its four files. When this Epic closes, `docs/diagrams/models-folder.md` carries the "## Who writes /models" table that `docs/diagrams/data-flow.md:71-79` has carried since E02. The two tables are identical. In both, the last row says what a hand edit to `structural.json` or `behavioral.json` does since volatility arrived (PR #61): every check lists it, and it is drift at the default volatility, 1 (Exact). A new test in `tests/drifter/test_cli.py` guards the behavioral half of that row. The structural half is already guarded by golden case L7. The team needs it because `models-folder.md` is the model a reader opens to learn what `/models` holds, and today it does not say that two of its files are written only by `drifter init` and `drifter update` (`proposals/init/init.md` fix 4, which E02 deleted). No route, answer or generator changes.

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

- Files: `docs/diagrams/models-folder.md`, `docs/diagrams/data-flow.md` (line 79 only; the file is on ask, so the edit stops for the human's approval), `docs/state/WORK-ITEMS.md` (the W0-6 row and Next action)
- What:
  - In `data-flow.md:79`, the last row becomes: `| a person | not by hand: a hand edit that does not match the code is listed on every check, and is drift at the default volatility, 1 (Exact); at a higher volatility it is drift only once the model carries more changes than that level tolerates | edited by hand |`. No other line of the file changes.
  - Append to `models-folder.md`, after the ladder's last paragraph, a blank line, then `## Who writes /models`, a blank line and the table, copied from `data-flow.md` lines 73 to 79 as they stand after the edit above.
  - In `WORK-ITEMS.md`, the Next action line "Can run beside it: W0-6 (step 1.1)" becomes a line saying that W0-6 is built in Epic E07 and waits for its audit. The W0-6 row is left as drafting wrote it.
- Check: `git grep -c "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → exactly two lines, `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`. Today it prints only the first (see Facts).
- Trailer: `Step: 2/2`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → empty. The Epic changes no behavior, and no spec line says what a hand edit to `structural.json` or `behavioral.json` does in general (`docs/base/specifications.md:245`, `:398` and `:503` are the only lines with "by hand" or "hand edit", and each stays true)
3. No open row for this Epic: `git grep -n "E07" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The guard passes: `python -m pytest tests/drifter/test_cli.py -q -k hand_edit_to_behavioral` → the summary line starts with `1 passed` and has no `failed`
6. Both models carry the heading once: `git grep -c "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`
7. The two tables are identical: `git grep -h -A8 "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md | tr -d '\r' | grep -vx -- "--" | sort | uniq -u` → prints nothing. Each heading is followed by a blank line and the 7-line table, so `-A8` takes the table and stops before the next blank line. Today the command prints data-flow.md's heading, blank line and table, because the second copy is missing.
8. The qualifier is in both: `git grep -c "is drift at the default volatility, 1 (Exact)" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md` → `docs/diagrams/data-flow.md:1` and `docs/diagrams/models-folder.md:1`
9. Only the one line of data-flow.md changed: `git diff --numstat main...HEAD -- docs/diagrams/data-flow.md` → `1	1	docs/diagrams/data-flow.md`
10. The whole suite on CI counts the new test: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --log | grep -o "[0-9]* passed[^=]*"` → `466 passed` and no `failed`. If `tests/connector/test_golden.py` cannot reach GitHub, its tests show as skipped, and passed plus skipped is 466.

## Open questions

None: the human answered the three proposals in the W0-6 row (2026-11-22), and every fact the steps rest on was checked against the disk at `18c69ff`.

## Review

<Written by the design reviewer: RATIFY or REVISE · reviewer · date, then the findings, each citing its source.>

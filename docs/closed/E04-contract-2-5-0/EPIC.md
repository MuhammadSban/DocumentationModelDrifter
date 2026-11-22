# E04: Contract 2.5.0, system coverage from evaluated tests, and T-21, T-22 and T-23 run

Status: closed · Owner: Kaan

W-row: W4-9, W4-5 and W4-10 in `docs/state/WORK-ITEMS.md` (build order steps C.4, C.5, 5.6 and 5.7) · Branch: `E04-contract-2-5-0`

## Goal

Our tester's `coverage.system` counts a criterion only when a test that lists it ended `pass` or `fail`; `coverage.component` keeps today's rule (`pass`, `fail`, or `error` with source `system`, from a test the target answered). The pod contract becomes version 2.5.0 and states both rules, what "in scope" means for system coverage (AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10), and how a tester knows a target is its own system. The decision is the human's, in the W4-9 row of `docs/state/WORK-ITEMS.md` ("Decided by the human, 2026-11-22": "evaluated" means a test that ended pass or fail; the course PDF leaves the rule to the pod, and the stricter reading makes the report explicit about what was really checked). Team 16's tester and system see this change, so it is a ⚠ CONTRACT CHANGE: it applies once Team 16 agrees (contract §10).

Revised 2026-11-22 to hold build order steps 5.7 and 5.6 as well (W4-10 and W4-5), by the human's ruling on E04-1 (option 2, recorded in the W4-9 row). When this Epic closes, T-21, T-22 and T-23 run, and no longer skip, on a system that lists `model_drift`, in our tester and in the contract text, still version 2.5.0:

- T-21 has a model version: `POST /analyze` for case L2 twice, and both answers equal L2's expected answer by T-26's rule. The prose version runs when the system lists `prose_detector`, also when it lists both features; the model version when it lists `model_drift` only; with neither, T-21 is `skip`.
- T-22: case L5 must come back aligned (the authorized change) and case L6 with its one ownership violation (the unauthorized change), both by the drift comparison T-24 to T-31 use. Without `model_drift` it is `skip`.
- T-23: case L8 of `docs/contract/model-golden-outputs.json` must equal its expected answer. L8 is a commit whose code would hang, fail or write a file if it were imported or run. Without `model_drift` it is `skip`, until Team 16 publishes a case of their own.

The components and criteria of the three tests do not change. On our own system, which lists `model_drift` only, `coverage.system` becomes 10 of 10 and `coverage.model` 7 of 7. The human sends contract 2.5.0 to Team 16 when this Epic is merged. The credential check of step 5.6 is not in this Epic (Out of scope).

Steps 1 to 7 are built, and Team 16's agreement is recorded (step 7). Steps 8 to 13 are this revision. The one pull request is opened when step 13 is committed, before the audit, and the Epic merges through it.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: none in `docs/diagrams/` describes the suite report or the contract's coverage rules, so none is read or changed. `docs/diagrams/dependency.md` reads: rule A4 holds, since no import changes. The seam is `run_suite`'s returned report and nothing below it, so no `DESIGN.md` (see open question 1).
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W4-9 row's "Decided by the human, 2026-11-22" line is the decision. The W4-8 row's five decisions say what "our own system" is, which section 5's new paragraph restates.
- Invariants: none read or changed.
- Other sources:
  - The course PDF, "Coverage fields" (p. 5): system coverage counts "how many acceptance criteria from the shared pod specification the suite evaluated out of all criteria in scope", using "the pod's criterion IDs and stated evaluation rules".
  - `docs/contract/pod-contract.md`: §1 (Team 16's tester's changes, the line "It counts coverage only from tests the target answered (section 5)"), §3 (the open box "Bump the version (section 10)"), §4 (each test's criteria; no file in `docs/contract/` names AC-11), §5 ("What counts"), §8 (the registry URLs at tag `contract-2.4.0`), §10 (agreement and version).
  - `docs/contract/pod-tester.openapi.yml`: `SuiteReport.coverage` (`system` description "Criteria AC-01 to AC-10 exercised by a test the target answered"; no `model` entry; no `additionalProperties: false`), `SetupRequest.target_url` (a string with the pattern `^https?://[^\s?#@]+$`, `pod-tester.openapi.yml:101-104`), `info.version`.
  - `docs/contract/pod-contract.openapi.yml`: `info.version`.
  - `Source/Tester/pod_tests.py`: `run_suite` (one `answered and (pass or fail or source system)` rule feeds both `components` and `criteria`; the basis strings say "exercised by a test the target answered"); `Result.answered`; `_run_one`.
  - `Source/Tester/own_system.py`: `REGISTRY_SYSTEM_URL`, `normalise`, `is_own`.
  - `Source/Tester/api.py`: `TARGET_URL`, the pattern a `target_url` must match.
  - `Source/Tester/page.html:223`: the label "Contract 2.4.0".
  - `tests/tester/test_pod_tests.py`: the `fake` and `closed_url` fixtures, `test_5xx_is_a_system_error_that_still_counts_as_answered`, `test_target_meeting_the_contract_passes_everything_it_runs` (system 8 today), `test_run_limit_ends_the_test_in_progress_and_skips_the_rest`.
  - `docs/base/specifications.md`: lines 73, 409, 709 and 716 name version 2.4.0; lines 73, 409 and 716 also say it is agreed. Lines 360-362: AC-11 is this system's own, and the pod's coverage reports count it as AC-02 (T-30 lists AC-02).
  - `docs/adr/0001-one-acceptance-criteria-list.md`: AC-11 stays ours and counts as AC-02, with no contract change.
  - `docs/closed/E03-model-coverage/EPIC.md`: the form of a ratified Epic here.
- Added by the revision of 2026-11-22, read at `d41a1c3` (the merge of `main`, which brought E05, build order steps 2.2 and 2.3):
  - Rulings: still none in `docs/decisions/RULED/`. The human's rulings for steps 8 to 13 are the "Decided by the human, 2026-11-22" lines of the W4-9, W4-5 and W4-10 rows of `docs/state/WORK-ITEMS.md`.
  - Models and invariants: none read or changed. `git grep -n -E "T-2[123]" -- docs/diagrams docs/invariants` prints nothing, and no import changes, so no `DESIGN.md` (open question 1).
  - `Source/Tester/pod_tests.py`: T-21's row is `pending_review` with `**PROSE`, the feature `prose_detector` (`:312`). T-22 and T-23 carry the fixed skips "Phase 5" and "checked by inspection" (`:313-314`). `drift(case)` compares one case of the model fixture (`:188-206`). `_run_one` decides a fixed skip before it looks at the features (`:371-380`). `catalog()` gives each test's `feature` and `skip` to the page (`:483-486`).
  - `Source/Tester/page.html:406-411`: `plannedLabel` says "runs only when /health lists" a test's one feature, or "skips:" with a fixed skip's message.
  - `tests/tester/conftest.py`: `MODEL_BY_COMMIT` (`:16`) makes the fake answer every case of `model-golden-outputs.json` that has a `drift`, so a new case needs no change there. `break_drift_case` (`:29`, `:68-71`) reverses `drift.behavioral`, which is empty for L2, L5, L6 and L8, so it changes nothing for them.
  - `docs/contract/model-golden-outputs.json`: cases L-pre, L0, L0-generate and L1 to L7. No L8.
  - `scripts/model_fixture.py`: builds the model fixture from nothing with fixed authors and dates, one commit a day from 2026-01-01, and tags each case. `tests/connector/test_model_golden.py` builds it and replays every case of the golden file: `EXIT` (`:23`) lists L-pre to L7, `test_the_golden_file_has_every_case_and_the_l0_generate_case` compares the file's cases with it, and three tests are parametrized over the cases. So a case added to the golden file must also be built by the script and named in `EXIT`. The file collects 29 tests today.
  - The fixture repository `kaan-kanadasi/doc-tracker-model-fixtures`: it carries the tags L-pre and L0 to L7 at the SHAs of contract §3. Its `main` was at L7, `d288268468df65602e9f4b348a95ff561ddd67bd`, when the revision was drafted. The human pushed L8 on 2026-11-22, a fast-forward: `main` and the tag L8 are at `c8058c2e8a52b5b1e86710e0821b94437fc438e1` (`git ls-remote`, 2026-11-22).
  - L8, prepared outside this repository on 2026-11-22 in `C:/Users/kaank/Documents/documentationDrifter2/t23-fixture/`. `model_fixture_l8.py` there is `scripts/model_fixture.py` plus three texts and one entry, with one more difference: its `SOURCE` line (line 13) points at `drifter-src/Source`, an export of this checkout beside it, and is not copied back (step 10). Its build gives L-pre to L7 at their published SHAs and L8 at `c8058c2e8a52b5b1e86710e0821b94437fc438e1`. `drifter check` on L8, run twice with this checkout's CLI, gave the same bytes both times (aligned, three empty lists) with exit 0, in 0.33 s and 0.34 s, and left `git status --short` empty and no planted file. `l8-case.json` there holds the case. CI does not depend on the push, because the replay test builds the fixture with the script. L8 has not been run through the service yet, only through `drifter check`; step 10's replay check does that.
  - `docs/contract/pod-contract.md`: the table of files at the top, whose cell for `model-golden-outputs.json` reads "expected answers for T-24 to T-33 (section 3)" (`:22`); §1's bullet "It reports T-22 and T-23 as `skip` with the messages in section 4" (`:40`) and its Features paragraph, which gives a skipped test the message "target does not implement" plus the feature's name (`:53-57`); §3's "Used by" column (`:102-103`), its table of commits (`:122-132`) and its two publishing groups (`:134-140`); §4's sentence on a failed `/health` (`:152-155`), its rows for T-21, T-22 and T-23 (`:184-186`) and the sentence that T-22 and T-23 are `skip` on every system (`:198-200`); §10's sentence that section 4 does not hold the three rules yet (`:339-343`). `git grep -n -E "T-2[123]" -- docs/contract/pod-tester.openapi.yml docs/contract/pod-contract.openapi.yml` prints nothing, so neither file goes stale.
  - `docs/base/specifications.md`, found by grep after the merge: `:331` (AC-04, T-21), `:334` (AC-05, "Phase 5 (T-22)"), `:351-352` (AC-09, "inspection, Phase 5; T-23"), `:368-369` (two publishing groups), the table of cases from `:378`, `:395` ("Every commit L0 to L7 except L6"), `:494-496` ("T-18 to T-21 (prose findings) are skipped") and `:748` (the cases L-pre and L0 to L7).
  - `docs/base/requirements-to-tests.md:38`: "On our system T-21, T-22 and T-23 skip today, so REQ-03 and REQ-06 stay uncovered until W4-5 and W4-10".
  - The W1-8 row's live run of 2026-11-22 against our own system: T-18 to T-21, T-22 and T-23 skip, `coverage.component` is 6 of 7, `coverage.system` 7 of 10 and `coverage.model` 5 of 7.
  - The literals of steps 8 to 11 were probed at `d41a1c3` by patching the test list in memory, with L8 added, and running `run_suite` against `FakeTarget`. Each entry gives system, component and model:
    - Today: plain fake 8, 6, 6; `model_drift` only 7, 6, 5; both features 8, 6, 6; neither feature 5, 5, 4.
    - After step 8: `model_drift` only 8, 6, 6. The rest as today.
    - After step 9: `model_drift` only 9, 7, 6; both features 9, 7, 6. Plain and neither as today.
    - After step 10: `model_drift` only 10, 7, 7; both features 10, 7, 7. Plain and neither as today.
  - `tests/tester/test_pod_tests.py` holds 31 tests, and `python -m pytest tests/tester/test_pod_tests.py --collect-only -q -k "test_t21_run_ or test_t22_run_ or test_t23_run_ or test_full_coverage_"` collects none of them, so no existing test name matches a `-k` pattern of steps 8 to 11. The whole suite collects 340 tests.

## Steps

One commit per step, made after the step's check passes. Each named test checks one behaviour, and each step's check selects its tests by name. A guard is a test expected to pass once written, because today's code already behaves as it asks; every other new or changed assertion is written first and fails before the code changes. Expected values are literals, read from contract §4.

Steps 1 to 7 are built. Their text below is kept as it was ratified at `928a0b0`: step 1 is commit `d64cd3f`, step 2 `c5b767a`, step 3 `74e9c0c`, step 4 `5b57e1b`, step 5 `182badb`, step 6 `30920fb` and step 7 `e3ef662`. Their trailers stay `Step: 1/7` to `Step: 7/7`. Steps 8 to 13 follow them and carry `Step: 8/13` to `Step: 13/13`.

### Step 1/7: system stops counting an error with source system

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`
- What: `run_suite` keeps two sets apart. `components` takes a test's components under today's rule; `criteria` takes a test's criteria only when it ended `pass` or `fail`. Test, changed first: `test_5xx_is_a_system_error_that_still_counts_as_answered` keeps `component` `covered == 6` and gains `system` `covered == 2`: with every `/analyze` answering 500, only T-15 passes, and it lists AC-06 and AC-08 (contract §4). Today that count is 8. The same commit changes `test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error`, which asserts `system` `covered == 8` for the same run: it becomes `== 2`, and its comment no longer says system coverage still counts a 5xx.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_5xx_is_a_system_error_that_still_counts_as_answered or test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error"` → `2 passed`
- Trailer: `Step: 1/7`

### Step 2/7: skip and every other error add nothing to system

- Files: `tests/tester/test_pod_tests.py`
- What: four guards, one per outcome, each asserting `coverage.system.covered` as a literal. Today's rule already leaves these out; the guards pin it under the new one.
  - `test_system_does_not_count_a_skipped_test`: the `fake` target as it is; T-22 and T-23 skip and T-24 to T-33 skip (no `model_drift`), so AC-05 and AC-09 are not covered: `covered == 8`, `total == 10`.
  - `test_system_does_not_count_an_error_from_communication`: `closed_url`; every test is `error` with source `communication`, except T-22 and T-23, which skip: `covered == 0`.
  - `test_system_does_not_count_an_error_from_the_tester`: a run limit shorter than one `/analyze` call (`fake.analyze_delay`), as `test_run_limit_ends_the_test_in_progress_and_skips_the_rest` does, so T-01 is `error` with source `tester` and the rest skip: `covered == 0`.
  - `test_system_does_not_count_an_error_when_health_fails`: `fake.health_status = 500`; T-18 to T-21 and T-24 to T-33 are `error` with source `system` because `/health` failed, and T-01 to T-17 pass: `covered == 5` (AC-01, AC-06, AC-07, AC-08, AC-10).
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_does_not_count_"` → `4 passed`
- Trailer: `Step: 2/7`

### Step 3/7: a criterion counts once

- Files: `tests/tester/test_pod_tests.py`
- What: one guard. `test_system_counts_a_criterion_listed_by_two_evaluated_tests_once`: the `fake` target with `features = ["prose_detector", "model_drift"]`, so T-01 to T-21 and T-24 to T-33 all pass; AC-01 is listed by seven passing tests (T-01 to T-07) and AC-02 by seven (T-18, T-19, T-26, T-27, T-28, T-30, T-31), yet `covered == 8` and `total == 10` (AC-05 and AC-09 come only from T-22 and T-23, which skip).
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_counts_a_criterion_listed_by_two_evaluated_tests_once"` → `1 passed`
- Trailer: `Step: 3/7`

### Step 4/7: the two basis strings

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`
- What: `system`'s basis says: criteria AC-01 to AC-10 (pod-contract.md section 5), each counted once, from tests that ended pass or fail, with AC-11 counted as AC-02 (specifications.md section 4.1). AC-11 appears only in our tester's basis, as spec §4.1 (lines 360-362) and ADR 0001 count it; the contract text does not name it (step 5). `component`'s basis keeps its wording, "components C1 to C7 exercised by a test the target answered (pod-contract.md section 5)". Tests:
  - `test_system_basis_names_pass_or_fail_and_ac_11`, written first: the basis contains "AC-01 to AC-10", "pass or fail", "AC-11", "pod-contract.md section 5" and "specifications.md section 4.1".
  - `test_component_basis_keeps_the_answered_wording`, a guard: the basis equals today's string, as a literal.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_basis_ or test_component_basis_"` → `2 passed`
- Trailer: `Step: 4/7`

### Step 5/7: the contract text

- Files: `docs/contract/pod-contract.md`, `docs/contract/pod-tester.openapi.yml`
- What:
  - §5 "What counts" gives two rules. A component is covered when a test the target answered lists it and ended `pass`, `fail`, or `error` with source `system` (today's rule). A criterion is covered only when a test that lists it ended `pass` or `fail`. One sentence says why they differ: a component that answered with a 5xx was still exercised, but a criterion is checked only when its test's answer could be judged.
  - §5 says what is in scope, in the phrase "in scope for system coverage": AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10 on every system. It does not name AC-11, which is Team 15's own (ADR 0001).
  - §5 defines "a tester's own system" as `own_system.py` decides it: after normalising `target_url` (scheme and host in lowercase, a default port dropped, a trailing slash stripped, the path compared exactly), it is the team's Railway public URL with `/system`, the system URL in the team's registry row, or `localhost`, `127.0.0.1` or `::1` on any port with the path `/system`, only when the tester is not running on Railway. Only then does the report carry `coverage.model`.
  - §5 gains one line on `target_url` and the course's `format: uri`, in the direction that holds: every system base URL that is a valid `format: uri`, starts with `http://` or `https://` in lowercase, has a non-empty host, and contains no `?`, `#` or `@` also matches our pattern (`Source/Tester/api.py` `TARGET_URL`). The line does not claim the reverse: the pattern also accepts some strings that are not URIs, such as `http://a%zz/system`, so a tester does not use it to validate a URI.
  - §1's line "It counts coverage only from tests the target answered (section 5)" says both rules.
  - `pod-tester.openapi.yml`: `coverage.system`'s description says criteria AC-01 to AC-10 from tests that ended pass or fail; `coverage` gains an optional `model` entry (`CoverageMeasure`), described as present only in a report whose tester and target belong to the same team.
- Check: `git grep -h -o -E "ended .pass. or .fail.|in scope for system coverage|a tester's own system|format: uri" -- docs/contract/pod-contract.md | sort -u` → exactly four lines, one per phrase: "a tester's own system", "ended `pass` or `fail`", "format: uri", "in scope for system coverage". Today it prints nothing. And `git grep -h -o -E "ended pass or fail|same team" -- docs/contract/pod-tester.openapi.yml | sort -u` → exactly two lines, "ended pass or fail" (the `system` description) and "same team" (the `model` description). Today it prints nothing.
- Trailer: `Step: 5/7`

### Step 6/7: the version

- Files: `docs/contract/pod-contract.md`, `docs/contract/pod-contract.openapi.yml`, `docs/contract/pod-tester.openapi.yml`, `Source/Tester/page.html`, `docs/base/specifications.md`
- What: every 2.4.0 becomes 2.5.0. In `pod-contract.md`: the top line, the two registry URLs in §8 (tag `contract-2.5.0`), and §10, where "it is the first agreed version" goes and the text says 2.5.0 is proposed and applies once Team 16 agrees. Both openapi files' `info.version`. The label in `page.html`. The four mentions in `docs/base/specifications.md` (lines 73, 409, 709, 716); while Team 16 has not agreed, those that say "agreed" say "proposed, pending Team 16's agreement" instead. Tick §3's open box "Bump the version (section 10)". Any spec line that describes how system coverage counts follows step 5; at drafting `git grep -n -i "answered" -- docs/base/specifications.md` prints nothing, so none is known.
- Check: `git grep -n "2\.4\.0" -- docs/contract docs/base/specifications.md Source` → prints nothing
- Trailer: `Step: 6/7`

### Step 7/7: record Team 16's agreement

- Files: `docs/contract/pod-contract.md` (the top line and §10), `docs/base/specifications.md` (lines 73, 409 and 716)
- What: written only once the human reports that Team 16 agreed to the 2.5.0 text, as 2.4.0's agreement was (commit `6371a3e`). The top line and §10 say 2.5.0 is agreed by Team 16, with the date the human gives; the three spec lines that step 6 made "proposed, pending Team 16's agreement" say "agreed" again.
- Check: `git grep -c -E "2\.5\.0.*agreed by Team 16|2\.5\.0 is agreed by both teams" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:2`, and `git grep -n "pending Team 16" -- docs/contract docs/base/specifications.md` → prints nothing
- Trailer: `Step: 7/7`

### Steps 8 to 13, added by the revision of 2026-11-22

What holds for all six:

- The seam is `run_suite`'s returned report against the `fake` target, as in steps 1 to 4.
- Each new test is marked "written first" (it fails before the step's code) or "guard" (it passes once written). Each existing test whose literal changes is named in the step that changes it and marked "changed first": its new literal is written, and seen to fail, before the code.
- A full test run happens in CI only, on each push. Locally a step runs its own check and then the whole of `tests/tester/test_pod_tests.py`, whose expected summary the step gives.
- Every expected pytest result reads: the summary line starts with the count given and has no `failed`.
- The build uses two checkers: one over the code steps, 8 to 11, and one over the docs steps, 12 and 13.

### Step 8/13: T-21 gets its model version

- Files: `Source/Tester/pod_tests.py`, `Source/Tester/page.html`, `tests/tester/test_pod_tests.py`, `tests/tester/conftest.py`
- What:
  - T-21's row keeps its feature `prose_detector` and its check `pending_review`, and gains a second check that needs `model_drift`: `POST /analyze` for L2 twice, each answer compared by `drift("L2")`, which is T-26's rule. `_run_one` picks the prose check when the features list `prose_detector`, also when they list both; otherwise the model check when they list `model_drift`; otherwise T-21 is `skip` with today's message, "target does not implement prose_detector" (open question 4). A failed `/health` leaves T-21 `error`, as today.
  - `catalog()` names T-21's second feature, and `plannedLabel` in `page.html` says T-21 runs when `/health` lists `prose_detector` or `model_drift`. The page's label has no test today (`tests/tester/test_api.py`, `test_page_and_catalog`, checks only the count of 33), and this step adds none.
  - `conftest.py`: `FakeTarget` gains two switches, `flip_aligned_case` (a model fixture case) and `flip_aligned_from` (default 1). From that answer of the case on, counted from 1, `drift.aligned` comes back flipped. `break_drift_case` cannot do this (Relies on).
  - New tests:
    - `test_t21_run_uses_the_model_version_with_only_model_drift`, written first: with `features = ["model_drift"]`, T-21 is `pass` and its message names L2. Today it is `skip`.
    - `test_t21_run_fails_when_the_second_answer_differs`, written first: with `features = ["model_drift"]`, `flip_aligned_case = "L2"` and `flip_aligned_from = 2`, T-21 is `fail` and its message names L2. Today it is `skip`. A check that read only the first answer would pass, so this test pins the second.
    - `test_t21_run_keeps_the_prose_version_with_prose_detector`, guard: the `fake` as it is, T-21 is `pass` with the message "all 3 findings start PENDING_REVIEW".
    - `test_t21_run_keeps_the_prose_version_with_both_features`, guard: with both features, the same outcome and message.
    - `test_t21_run_skips_with_neither_feature`, guard: with `features = []`, T-21 is `skip` with the message "target does not implement prose_detector".
  - Existing tests:
    - `test_missing_feature_is_skipped_not_failed`, changed first: with `features = ["model_drift"]` it asserts that T-18 to T-21 skip. It becomes T-18 to T-20, and gains the assertion that T-21 is `pass`, which fails before the code.
    - `test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error`, changed in this step, not first: its first half asserts `model` `covered == 5` with `features = ["model_drift"]`. That literal would move to 6 here and to 7 in step 10, where nothing is left uncovered. Its first half becomes `features = []` with `covered == 4` (REQ-01, REQ-04, REQ-05 and REQ-07; REQ-02, REQ-03 and REQ-06 are dropped), and the comment says so. 4 holds before and after the code (Relies on, the probe), so this change cannot fail first; the two written-first tests above carry the new behaviour.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_t21_run_"` → the summary line starts with `5 passed` and has no `failed`. Then the whole file: `python -m pytest tests/tester/test_pod_tests.py -q` → starts with `36 passed`, no `failed`.
- Trailer: `Step: 8/13`

### Step 9/13: T-22 runs

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`; `tests/tester/conftest.py` only if step 8's switch needs a change, and none is expected
- What:
  - T-22's row loses its fixed skip "Phase 5" and gets the feature `model_drift` and a check: `drift("L5")`, which must come back aligned (the authorized change), then `drift("L6")`, with its one ownership violation (the unauthorized change). Its components and criteria stay C7 and AC-05. Without `model_drift` it is `skip` with the message "target does not implement model_drift"; when `/health` fails it is `error`, like every test that needs a feature.
  - New tests:
    - `test_t22_run_passes_with_model_drift`, written first: with `features = ["model_drift"]`, T-22 is `pass`. Today it is `skip`.
    - `test_t22_run_fails_when_the_unauthorized_change_is_not_flagged`, written first: with `features = ["model_drift"]` and `flip_aligned_case = "L6"`, so L6 comes back aligned, T-22 is `fail` and its message names L6.
    - `test_t22_run_fails_when_the_authorized_change_is_flagged`, written first: with `features = ["model_drift"]` and `flip_aligned_case = "L5"`, so L5 comes back not aligned, T-22 is `fail` and its message names L5.
    - `test_t22_run_skips_without_model_drift`, guard: the `fake` as it is, T-22's outcome is `skip`. It asserts the outcome only, since the message changes in this step.
  - Existing tests, both changed first:
    - `test_target_meeting_the_contract_passes_everything_it_runs`: T-22's entry has the message "Phase 5". It becomes "target does not implement model_drift". Its `component` 6 and `system` 8 stay.
    - `test_system_counts_a_criterion_listed_by_two_evaluated_tests_once`: with both features, `(8, 10)` becomes `(9, 10)`, and the tests asserted to pass become T-01 to T-22 and T-24 to T-33.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_t22_run_"` → the summary line starts with `4 passed` and has no `failed`. Then the whole file: `python -m pytest tests/tester/test_pod_tests.py -q` → starts with `40 passed`, no `failed`.
- Trailer: `Step: 9/13`

### Step 10/13: T-23 runs

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`, `docs/contract/model-golden-outputs.json`, `scripts/model_fixture.py`, `tests/connector/test_model_golden.py`; `tests/tester/conftest.py` only if step 8's switch needs a change, and none is expected
- What:
  - `model-golden-outputs.json` gains case L8 after L7, byte for byte as `C:/Users/kaank/Documents/documentationDrifter2/t23-fixture/l8-case.json` holds it: `case` "L8", `request` with the fixture repository and `commit_id` `c8058c2e8a52b5b1e86710e0821b94437fc438e1`, and `expected` with `drift` (`aligned: true`, and `behavioral`, `ownership` and `structural` empty) and `drift_error: null`.
  - `scripts/model_fixture.py` gains the texts `HANGS`, `RAISES` and `WRITES` and the entry L8 after L7, as `t23-fixture/model_fixture_l8.py` holds them; that file's `SOURCE` line is not copied, and the script's own stays. The owner adds `src/hangs.py` (its top level loops forever), `src/raises.py` (it raises at import) and `src/writes.py` (it writes a file beside itself), with `update` folded into the commit. The build then gives L8 at the SHA above (Relies on).
  - `tests/connector/test_model_golden.py`: `EXIT` gains `"L8": 0`. Its three parametrized tests each gain an L8 case.
  - T-23's row loses its fixed skip "checked by inspection" and gets the feature `model_drift` and the check `drift("L8")`. Its components and criteria stay C2 and AC-09. Without `model_drift` it is `skip` with the message "target does not implement model_drift".
  - New tests:
    - `test_t23_run_passes_with_model_drift`, written first: with `features = ["model_drift"]`, T-23 is `pass` with the message "L8 matches the expected answer". Today it is `skip`.
    - `test_t23_run_fails_when_the_answer_differs`, written first: with `features = ["model_drift"]` and `flip_aligned_case = "L8"`, T-23 is `fail` and its message names L8.
    - `test_t23_run_skips_without_model_drift`, guard: the `fake` as it is, T-23's outcome is `skip`. It asserts the outcome only.
  - Existing tests:
    - `test_target_meeting_the_contract_passes_everything_it_runs`, changed first: T-23's message "checked by inspection" becomes "target does not implement model_drift".
    - `test_system_counts_a_criterion_listed_by_two_evaluated_tests_once`, changed first: `(9, 10)` becomes `(10, 10)`, and all of T-01 to T-33 are asserted to pass.
    - `test_the_golden_file_has_every_case_and_the_l0_generate_case` in `tests/connector/test_model_golden.py`, changed first through `EXIT`: with `"L8": 0` in `EXIT` and no L8 in the golden file it fails.
    - `test_model_counts_a_requirement_with_no_evaluated_test_in_total`: its literal `(6, 7)` stays; its comment "always skips" becomes "skips without model_drift".
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_t23_run_"` → the summary line starts with `3 passed` and has no `failed`. Then the whole file: `python -m pytest tests/tester/test_pod_tests.py -q` → starts with `43 passed`, no `failed`. Then the replay: `python -m pytest tests/connector/test_model_golden.py -q` → starts with `32 passed`, no `failed` (29 today, plus L8 in three parametrized tests).
- Trailer: `Step: 10/13`

### Step 11/13: coverage is full on a system that lists model_drift

- Files: `tests/tester/test_pod_tests.py`. `Source/Tester/pod_tests.py` is not touched: both basis strings stay true (`:351-355`).
- What: two guards. After step 10 the code already gives both literals (Relies on, the probe), so neither can fail first (open question 5).
  - `test_full_coverage_system_is_10_of_10_with_model_drift`: with `features = ["model_drift"]`, `coverage.system` is `(10, 10)`. From contract §4: AC-01 by T-01, AC-02 by T-26, AC-03 by T-24, AC-04 by T-21's model version, AC-05 by T-22, AC-06 by T-14, AC-07 by T-08, AC-08 by T-12, AC-09 by T-23 and AC-10 by T-17. T-18 to T-20 skip, and they are the only tests that do.
  - `test_full_coverage_model_is_7_of_7_on_our_own_system`: with `features = ["model_drift"]` and `own=True`, `coverage.model` is `(7, 7)`. From `docs/base/requirements-to-tests.md`: REQ-03 by T-21 and T-22, REQ-06 by T-23, and the other five as today.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_full_coverage_"` → the summary line starts with `2 passed` and has no `failed`. Then the whole file: `python -m pytest tests/tester/test_pod_tests.py -q` → starts with `45 passed`, no `failed`.
- Trailer: `Step: 11/13`

### Step 12/13: the contract text, still version 2.5.0

- Files: `docs/contract/pod-contract.md`. `docs/contract/pod-tester.openapi.yml` and `docs/contract/pod-contract.openapi.yml` are not touched: neither names T-21, T-22 or T-23 (Relies on).
- What:
  - The table of files at the top: the cell "expected answers for T-24 to T-33 (section 3)" for `model-golden-outputs.json` becomes "expected answers for T-21 (model version) and T-22 to T-33 (section 3)".
  - §1: the bullet "It reports T-22 and T-23 as `skip` with the messages in section 4" becomes "It runs T-22 and T-23, and T-21's model version, against `model-golden-outputs.json` on a system that lists `model_drift` (section 4)". The count of seven changes stays.
  - §3: the model fixture's "Used by" cell becomes "T-21 (model version), T-22 to T-33". The table of commits gains the row L8 with its SHA. "published in two groups" becomes "published in three groups", and the table of groups gains row 3: T-21 (model version), T-22 and T-23, using L2, L5, L6 and L8. One sentence under the checklist says that group 3 is published within version 2.5.0, with no further bump, as section 10 states.
  - §4: in the sentence on a failed `/health`, "(T-18 to T-21, T-24 to T-33)" becomes "(T-18 to T-33)".
  - §4, the three rows, with components and criteria as they are. T-21: the case cell adds "model version: L2, twice", and the cell for a system without `prose_detector` says it runs the model version with `model_drift` and skips otherwise. T-22: the case cell is "model fixture: L5 and L6", with "runs" and "skip" in the last two cells. T-23: the case cell is "model fixture: L8", with "runs" and "skip".
  - §4: the sentence "T-22 and T-23 are `skip` on every system, with the messages ..." goes. In its place: T-22 and T-23 need `model_drift`, and "T-21 runs on either feature".
  - §4 gains "Rules for T-21, T-22 and T-23", one paragraph each, starting `- **T-21.**`, `- **T-22.**` and `- **T-23.**`, with the rules as the Goal gives them. T-21's paragraph also says that a system listing neither feature gets `skip` with the message for `prose_detector`. T-23's paragraph says what L8 is, and that without `model_drift` it is `skip` until Team 16 publishes a case of their own.
  - §10: the two sentences from "Section 4 does not hold those three rules yet" to "before this version is merged" become "Section 4 holds all three rules." The sentence "Version 2.5.0 is agreed by both teams" stays, so step 7's check still counts 2.
- Check: each of the eleven greps below, on `docs/contract/pod-contract.md`, with its output. A `grep -z` reads the file as one line and `\s+` matches a line break, so a phrase split across lines is still found. A `git grep` is used only for table rows and list items, which are one line each.
  1. §1's bullet: `grep -z -c -E "It\s+runs\s+T-22\s+and\s+T-23" docs/contract/pod-contract.md` → `1`. Today `0`.
  2. §3's "Used by" cell: `git grep -c -F "| Team 15 | T-21 (model version), T-22 to T-33 |" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:1`. Today nothing.
  3. §3's rows for L8 and group 3: `git grep -c -E "^\| L8 \|.*c8058c2e8a52b5b1e86710e0821b94437fc438e1|^\| 3 \| T-21 \(model version\), T-22, T-23 \|" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:2`. Today nothing.
  4. §4's `/health` sentence: `grep -z -c -E "\(T-18\s+to\s+T-33\)" docs/contract/pod-contract.md` → `1`. Today `0`.
  5. §4's three rows: `git grep -c -E "^\| T-21 \|.*L2, twice.*\| runs \||^\| T-22 \|.*L5 and L6.*\| runs \| skip \||^\| T-23 \|.*L8.*\| runs \| skip \|" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:3`. Today nothing.
  6. §4's replaced sentence: `grep -z -c -E "T-21\s+runs\s+on\s+either\s+feature" docs/contract/pod-contract.md` → `1`. Today `0`.
  7. §4's rules, the heading and the three paragraphs: `grep -z -c -E "Rules\s+for\s+T-21,\s+T-22\s+and\s+T-23" docs/contract/pod-contract.md` → `1`, today `0`; and `git grep -c -E "^- \*\*T-2[123]\.\*\*" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:3`, today nothing.
  8. §10: `grep -z -c -E "Section\s+4\s+holds\s+all\s+three\s+rules" docs/contract/pod-contract.md` → `1`. Today `0`.
  9. The old sentences are gone: `grep -z -c -E "It\s+reports\s+T-22\s+and\s+T-23\s+as|published\s+in\s+two\s+groups|\(T-18\s+to\s+T-21,\s+T-24\s+to\s+T-33\)|T-22\s+and\s+T-23\s+are\s+.skip.\s+on\s+every\s+system|checked\s+by\s+inspection|does\s+not\s+hold\s+those\s+three\s+rules" docs/contract/pod-contract.md` → `0`. Today `1`, and each of the six phrases alone gives `1` today.
  10. The old rows are gone: `git grep -c -E "^\| T-21 \|.*\| skip \| runs \||^\| T-22 \|.*\| Phase 5 \||^\| T-23 \|.*\| inspection \||\| Team 15 \| T-24 to T-33 \|" -- docs/contract/pod-contract.md` → prints nothing. Today `docs/contract/pod-contract.md:4`.
  11. The table of files: `grep -z -c -E "expected\s+answers\s+for\s+T-24\s+to\s+T-33" docs/contract/pod-contract.md` → `0`, today `1`; and `grep -z -c -E "expected\s+answers\s+for\s+T-21\s+\(model\s+version\)\s+and\s+T-22\s+to\s+T-33" docs/contract/pod-contract.md` → `1`, today `0`.
- Trailer: `Step: 12/13`

### Step 13/13: the spec, the map and the queue

- Files: `docs/base/specifications.md`, `docs/base/requirements-to-tests.md`, `docs/state/WORK-ITEMS.md`. `Source/Tester/page.html` is not touched here: it states no skip of its own, and its one stale label is fixed in step 8.
- What:
  - `docs/base/specifications.md`, the lines Relies on lists. `:331` names T-21's model version for this system. `:334` loses "Phase 5" and names L5 and L6. `:351-352` loses "inspection, Phase 5" for the parts T-23 now checks, names L8, and keeps the credentials part as checked by inspection. `:368-369` says three groups and names the third. The table of cases gains the row L8, expected true. `:395` and `:748` say L0 to L8. `:494-496` says that against this system T-18 to T-20 skip, T-21 runs its model version, and T-22 and T-23 run. Any other line the change makes untrue follows (R2).
  - `docs/base/requirements-to-tests.md`: the last sentence says that on our system T-21 runs its model version and T-22 and T-23 run, so all seven requirements can be covered. The version line stays 1, since no pair changes.
  - `docs/state/WORK-ITEMS.md`: the W4-10 and W4-5 rows say what steps 8 to 13 built, and carry the builder's run against the service on localhost (Out of scope). The credential check stays open in the W4-5 row. Next action follows. The rows are marked done by the closing commit, not here.
- Check: `grep -z -l -E "T-18\s+to\s+T-21\s+\(prose\s+findings\)\s+are\s+skipped|review\s+decisions,\s+Phase\s+5\s+\(T-22\)|Phase\s+5;\s+T-23|T-23\s+skip\s+today|in\s+two\s+groups|L0\s+to\s+L7\s+except\s+L6" docs/base/specifications.md docs/base/requirements-to-tests.md` → prints nothing. Today it prints both file names. Then `python -m pytest tests/tester/test_pod_tests.py -q` → the summary line starts with `45 passed` and has no `failed`.
- Trailer: `Step: 13/13`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → every spec line this Epic made wrong is in the diff; empty when the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E04" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The branch is pushed: `git rev-parse HEAD origin/E04-contract-2-5-0` → the same SHA twice (line 1 then shows CI on that HEAD)
6. The tester's tests pass: `python -m pytest tests/tester -q` → ends with `passed`, no `failed`
7. The named tests pass: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_5xx_is_a_system_error_that_still_counts_as_answered or test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error or test_system_does_not_count_ or test_system_counts_a_criterion_listed_by_two_evaluated_tests_once or test_system_basis_ or test_component_basis_"` → `9 passed`
8. No old version left: `git grep -n "2\.4\.0" -- docs/contract docs/base/specifications.md Source` → prints nothing
9. No open box in §3: `git grep -n -F -- "- [ ]" docs/contract/pod-contract.md` → prints nothing
10. Imports still follow the map: `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`
11. Team 16's agreement is recorded (step 7): `git grep -c -E "2\.5\.0.*agreed by Team 16|2\.5\.0 is agreed by both teams" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:2`
12. The tests of steps 8 to 11 pass: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_t21_run_ or test_t22_run_ or test_t23_run_ or test_full_coverage_"` → the summary line starts with `14 passed` and has no `failed`
13. CI ran the whole suite on the pushed HEAD: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --log | grep -oE "[0-9]+ passed" | head -1` → `357 passed` (340 at `d41a1c3`, plus 14, plus L8 in the three parametrized tests of `tests/connector/test_model_golden.py`). An empty answer means a run is still in progress.
14. Lint is clean: `ruff check` → `All checks passed!`
15. The contract holds the three rules: the eleven greps of step 12, each with the output step 12 gives
16. No old claim is left in the spec or the map: `grep -z -l -E "T-18\s+to\s+T-21\s+\(prose\s+findings\)\s+are\s+skipped|review\s+decisions,\s+Phase\s+5\s+\(T-22\)|Phase\s+5;\s+T-23|T-23\s+skip\s+today|in\s+two\s+groups|L0\s+to\s+L7\s+except\s+L6" docs/base/specifications.md docs/base/requirements-to-tests.md` → prints nothing

Line 12 replaces the line that waited for steps 5.6 and 5.7 to arrive on this branch: they are steps 8 to 13 now. Lines 6 and 7 still hold as written; line 10 is the import check.

## Out of scope

- The credential check of step 5.6: running the hosted service with a fake credential and searching every response and the logs for it. By the human's ruling it stays open in the W4-5 row, as a follow-up after the tag.
- Pushing L8 and its tag to `kaan-kanadasi/doc-tracker-model-fixtures`: the human's, and done on 2026-11-22 (Relies on). No step of this Epic writes to that repository.
- Team 16's tester and system. Their tester takes the three rules from the contract text. Their system lists no `model_drift`, so T-22 and T-23 skip on it and T-21 runs its prose version.
- A case of Team 16's own for T-23 on a system without `model_drift`.
- The `/tester` page showing `coverage.model` and an end-to-end `test_run` test (left over from E03, `docs/state/WORK-ITEMS.md` Next action).

Not a Done line, recorded in the W4-5 and W4-10 rows by the builder: one run of our tester against the service on localhost, showing T-21, T-22 and T-23 as `pass`, `coverage.system` 10 of 10 and `coverage.model` 7 of 7.

After the merge, and not part of Done, the human tags the merge commit `contract-2.5.0` and points both teams' registry rows to it.

## Open questions

1. Does a change to the pod contract count as a boundary change that needs a `DESIGN.md` beside this Epic (`docs/epics/README.md`, Naming)? The draft reads "boundary" as a module boundary or a model in `docs/diagrams/`, neither of which changes, and treats the contract as the boundary's own document, edited directly. Answered: no `DESIGN.md`. A boundary here is a module boundary, "what calls what, and who owns which file" (`docs/templates/DESIGN.md:7`; INV-3, `docs/invariants/INVARIANTS.md:18`), and no import or module changes (`docs/diagrams/dependency.md:79`, rule A4). No model in `docs/diagrams/` describes the suite report or its coverage rules (`git grep -n -i -E "coverage|suite"` over the five models prints nothing). E03 changed the same report's `coverage` object without a `DESIGN.md` and was ratified (`docs/closed/E03-model-coverage/EPIC.md`, Review, second finding).
2. Who writes Team 16's agreement into §10, and does recording it need its own commit on this branch before the pull request opens (Done line 11)? Answered: its own commit, written once the human reports Team 16's agreement, as 2.4.0's was (commit `6371a3e`, "Record Team 16's agreement to contract 2.4.0"). On this branch every agent commit needs `Step: i/N`, `plan` or `close` (`.claude/hooks/step-trailer.py:12`; R7), and none of steps 1 to 6 records the agreement, so the Epic needs a step for it (Review, finding 5).
3. Added by the design reviewer: how do the code and commits of W4-5 and W4-10 reach this branch and its one pull request, when R7 and `docs/epics/README.md` ("Build only from a live, ratified Epic"; Naming, Branch: "All work on the Epic happens on it") give each Epic its own branch and `Step:` lines? Not answered by the code, a model or a ruling: row E04-1 in `docs/decisions/OPEN-DECISIONS.md`. Ruled by the human on 2026-11-22: option 2, this Epic is revised to hold their steps (the W4-9 row of `docs/state/WORK-ITEMS.md`). The row and its section are removed from `docs/decisions/OPEN-DECISIONS.md`.
4. Added by the revision: which message does T-21 give on a system that lists neither feature? The draft keeps today's, "target does not implement prose_detector": T-21's row still needs `prose_detector` first, and contract §1 gives a skipped test the message that names the feature it lacks (`docs/contract/pod-contract.md:53-57`). Step 12 writes this into §4.
5. Added by the revision: where does the disk disagree with the human's outline of steps 8 to 13? In three places, and the draft follows the disk in each. Step 10 also touches `scripts/model_fixture.py` and `tests/connector/test_model_golden.py`, because the replay test builds and checks every case of the golden file (Relies on). The CI total is therefore 357, not 354: L8 adds a case to each of three parametrized tests. The two tests of step 11 are guards, not written first: after step 10 the code already gives both literals (Relies on, the probe).

## Review

REVISE · design-reviewer at ee04eb4 · 2026-11-22

What holds:

- The filled-copy check prints nothing for this file, and no `DESIGN.md` is needed (open question 1).
- No conflict with a level above. The course PDF defines `fail` as "the response can be evaluated" and `error` as a problem that "prevents evaluation", and asks system coverage to count the criteria "the suite evaluated" (`docs/base/student-facing-spec.docx.pdf`, outcomes and "Coverage fields"), so pass-or-fail fits it. The human's decision is the W4-9 row (`docs/state/WORK-ITEMS.md:215`). `RULED/` holds only its README.
- The literal counts hold against contract §4 (`docs/contract/pod-contract.md:159-191`) and the fake target (`tests/tester/conftest.py`), checked by running today's `run_suite` against `FakeTarget`. The plain fake gives system 8 of 10 and component 6. With every `/analyze` at 500, only T-15 passes (AC-06, AC-08), so Step 1's 2 is right. Today that run gives 8, so Step 1's new assertion fails first, as it should. With `/health` at 500, system is 5 today. A limit shorter than one `/analyze` gives T-01 `error`/`tester` and 0. `closed_url` gives 0. Step 2's four guards and Step 3's guard pass today.
- Step 4's written-first test fails today, because the basis lacks "pass or fail" and "AC-11" (`Source/Tester/pod_tests.py:353-354`). Its component guard passes today (`:351-352`).
- Done line 7's 8 = 1 + 4 + 1 + 2, and no existing test name matches the new prefixes: the `-k` run selects only the 5xx test, `1 passed, 23 deselected`. Done line 9: `- [ ]` appears only at `docs/contract/pod-contract.md:145`. Step 6's grep today lists exactly the eleven lines the step names. `.importlinter` holds 5 contracts. `lint-imports` is not installed in this checkout, so Done line 10 was not run.

What must change for RATIFY:

1. Step 1 turns an existing test red. `test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error` asserts `system` `covered == 8` with every `/analyze` at 500, and its comment says system coverage "still counts" a 5xx (`tests/tester/test_pod_tests.py:184-190`). After Step 1 that value is 2. Step 1 must name this change, 8 to 2 with the comment fixed. Its check selects only the 5xx test, so the step's commit would leave `tests/tester` red, and Done line 6 would fail. The check should also select this test, or run the whole file.
2. Step 5's new §5 line is false today. It says our `target_url` pattern accepts only values that are valid under `format: uri`. `^https?://[^\s?#@]+$` (`Source/Tester/api.py:22`, `docs/contract/pod-tester.openapi.yml:104`) matches `http://a<b/system`, `http://a%zz/system` and `http://[::1/system` (checked with Python `re`), and none of these is a URI under RFC 3986: `<` is not an allowed character, `%` needs two hex digits, and the IP literal is not closed. Drop the line, or add a step that tightens the pattern, with a written-first test. Relies on also calls `SetupRequest.target_url` "a plain string", but it carries that pattern (`pod-tester.openapi.yml:101-104`).
3. AC-11 is cited to the wrong source and enters the shared contract. Relies on says contract §4 has "T-30 lists AC-02 for AC-11", but no file in `docs/contract/` names AC-11 (`git grep -n "AC-11" -- docs/contract` prints nothing). The pairing is in the spec (`docs/base/specifications.md:360-362`). The course PDF says to use "the pod's criterion IDs" (p. 5). ADR 0001 keeps AC-11 as ours and needed no contract change (`docs/adr/0001-one-acceptance-criteria-list.md:3`). Fix the citation, and either drop AC-11 from Step 5's §5 text, Step 4's basis and its test, or name the source that puts a Team 15 criterion into the pod's text.
4. Done lines 11 to 14 are four more lines in the human's words. The template allows one such line, line 4 (`docs/templates/EPIC.md`, Done criteria). Make 11 and 12 commands with expected outputs: a `git grep` on `pod-contract.md` for the 2.5.0 agreement with its date, and a `git grep` on `docs/state/WORK-ITEMS.md` for W4-5 and W4-10 marked done. Line 13 is a sequencing rule, not a check, so move it to the Goal. Line 14 can only hold after the merge, after the audit, so move it out of Done, for example to a follow-up line under Out of scope.
5. No step records Team 16's agreement (open question 2), and nothing turns step 6's "proposed, pending Team 16's agreement" back into "agreed". Add a step that names its files (the top line and §10 of `pod-contract.md`, and spec lines 73, 409 and 716), a `git grep` check with its literal output, and its trailer. On this branch every agent commit needs one (`.claude/hooks/step-trailer.py:12`).
6. Open question 3, how W4-5's and W4-10's work reaches this branch under R7, is the human's call: row E04-1 in `docs/decisions/OPEN-DECISIONS.md`. The Goal, Out of scope and Done line 12 rest on the answer.

Notes, not blocking:

- Step 2's communication guard says "every test is `error` with source `communication`", but T-22 and T-23 skip, because a fixed skip is decided before the `/health` failure (`Source/Tester/pod_tests.py:370-377`; checked by running it). The literal 0 holds.
- Relies on says spec line 709 says 2.4.0 "is agreed". It only names the version (`docs/base/specifications.md:709`).
- Step 3's guard runs the same fake with the same assertion, 8 of 10, as Step 2's skip guard and `tests/tester/test_pod_tests.py:55`, so it cannot fail on its own. Consider a setup that only "counts once" would change.
- Step 5's expected output "`:4` or more" is a range, not a literal. The regex also matches weak phrases such as "in scope".

Revised by the author after this review: findings 1 to 5 and the four notes are addressed in the steps, Relies on, Goal, Done and Out of scope; finding 6 stays open as row E04-1.

REVISE · design-reviewer at 33cd766 · 2026-11-22

What holds:

- The filled-copy check prints nothing for this file. No `DESIGN.md` is needed (open question 1): no import changes (`docs/diagrams/dependency.md:79`, A4), and no model describes the coverage rules.
- No conflict with a level above. The decision is the W4-9 row (`docs/state/WORK-ITEMS.md:215`). `RULED/` holds only its README. AC-11 now stays out of the contract text (step 5), and `git grep -n "AC-11" -- docs/contract` prints nothing.
- The counts in steps 1 to 3 were checked by running today's `run_suite` against `FakeTarget` (`tests/tester/conftest.py`). For each setup the test computed today's `system`, and also the set of criteria from pass-or-fail tests only:
  - Plain fake: 8 of 10, component 6.
  - Every `/analyze` at 500: today 8, pass-or-fail 2. Only T-15 passes, with AC-06 and AC-08. So step 1's new assertion and its changed `== 2` in `test_model_does_not_cover_...` (`tests/tester/test_pod_tests.py:190`) both fail first. Step 1's check selects both tests: `--co` gives `2/24 tests collected`.
  - `closed_url`: 0. T-22 and T-23 skip; the other 31 are `error`/`communication`.
  - A limit of 0.2 with `analyze_delay = 0.4`: T-01 is `error`/`tester`, the other 32 skip, 0.
  - `/health` at 500: 5 (AC-01, AC-06, AC-07, AC-08, AC-10). T-01 to T-17 pass; T-18 to T-21 and T-24 to T-33 are `error`/`system` with `answered=False` (`Source/Tester/pod_tests.py:375-377`).
  - `features = ["prose_detector", "model_drift"]`: T-01 to T-21 and T-24 to T-33 pass, and system is 8 of 10.
  - So step 2's four guards and step 3's guard pass today.
- Step 4: the system basis today is "criteria AC-01 to AC-10 exercised by a test the target answered (pod-contract.md section 5)". It lacks "pass or fail" and "AC-11", so the written-first test fails today. The component guard's string equals today's (`Source/Tester/pod_tests.py:351-354`).
- Done line 7's 9 = 2 + 4 + 1 + 2. Today its `-k` collects only the two existing tests.
- Step 6's grep lists exactly the eleven lines the step names. Step 5's grep prints nothing today. Step 7's pattern, run with 2.4.0 in place of 2.5.0, prints `docs/contract/pod-contract.md:2`, so the form is right. Done line 12's pattern matches the form of done rows (`docs/state/WORK-ITEMS.md:214`).
- The own-system text in step 5 matches `Source/Tester/own_system.py:15-39`. `target_url`'s pattern is at `pod-tester.openapi.yml:101-104` and `Source/Tester/api.py:22`. Spec lines 73, 409, 709, 716 and 360-362 say what Relies on claims.
- Done lines 1 to 12 are commands with outputs, except line 4. Every step names its files, one check and its trailer.
- `lint-imports` is not installed in this checkout, so Done line 10 was not run.

What must change for RATIFY:

1. Step 5's `format: uri` line is still false as written. `format: uri` is an RFC 3986 URI, and its `hier-part` may be `path-rootless`, `path-absolute`, or `//` with an empty authority. So `http:foo/system`, `http:/system` and `http://` are valid `format: uri` values with a lowercase `http` scheme and no `?`, `#` or `@`, yet none matches `^https?://[^\s?#@]+$` (checked with Python `re`; `Source/Tester/api.py:22`). Limit the line to URIs that start with `http://` or `https://` and have a non-empty host. Under that limit the claim holds, because the authority and path characters of RFC 3986 include no whitespace, and `?`, `#` and `@` are excluded by name.
2. Step 3 says AC-02 is listed by "more than ten" passing tests. It is listed by seven: T-18, T-19, T-26, T-27, T-28, T-30 and T-31 (`docs/contract/pod-contract.md:180-181, 188-190, 192-193`; the probe's count among passing tests is `AC-02: 7`). Write seven. The literal `covered == 8` is unaffected.
3. Open question 1 says `git grep -n -i "coverage\|suite"` over the five models "prints only `data-flow.md:97`". It prints nothing, also with `-E "coverage|suite"`, and `docs/diagrams/data-flow.md:97` contains neither word. Correct the line. Its answer, no `DESIGN.md`, still stands.

Notes, not blocking:

- Step 4's system basis ends "with AC-11 counted as AC-02 (pod-contract.md section 5)". That cites section 5 for a pairing the contract will not contain (`docs/base/specifications.md:360-362` is its source). Consider putting the section 5 citation before the AC-11 clause, or citing spec §4.1 for it.
- Step 5's check reads only `pod-contract.md`. The `pod-tester.openapi.yml` edits (the `system` description and the optional `model` entry) have no check of their own. `test_model_report_validates_against_the_pod_tester_openapi` passes with or without them, because `coverage` sets no `additionalProperties`.
- Open question 3 remains the human's call: row E04-1 in `docs/decisions/OPEN-DECISIONS.md`. No new row is needed.

Revised by the author after the second review: findings 1 to 3 and both notes are addressed in steps 3, 4 and 5 and open question 1.

RATIFY · design-reviewer at 928a0b0 · 2026-11-22

- The filled-copy check in `docs/templates/README.md` prints nothing for this file (exit 1). There is no `DESIGN.md`, and none is needed (open question 1): no import changes (`docs/diagrams/dependency.md:79`, A4), and `git grep -n -i -E "coverage|suite"` over the five models prints nothing.
- No conflict with a level above. The course PDF, p. 5, asks system coverage to count the criteria "the suite evaluated out of all criteria in scope", "each criterion once", and defines `fail` as "can be evaluated" and `error` as what "prevents evaluation" (`docs/base/student-facing-spec.docx.pdf`, checked with `pdftotext`). Its OpenAPI gives `target_url` `format: uri`. The decision is the W4-9 row (`docs/state/WORK-ITEMS.md:215`). `RULED/` holds only its README. `git grep -n "AC-11" -- docs/contract` prints nothing, and step 5 keeps it out.
- The counts in steps 1 to 3 hold. Checked by running today's `run_suite` against `FakeTarget` (`tests/tester/conftest.py`), with today's `system` and the set of criteria from pass-or-fail tests side by side:
  - Plain fake: 8 of 10, component 6. T-22 to T-33 skip.
  - Every `/analyze` at 500: today 8, pass-or-fail 2 (AC-06, AC-08). Only T-15 passes. So step 1's new assertion and its `== 2` at `tests/tester/test_pod_tests.py:190` both fail today. Its check collects 2 of 24 tests today.
  - `closed_url`: 0. That is 31 `error`/`communication`, with T-22 and T-23 skipped.
  - Limit 0.2 with `analyze_delay = 0.4`: T-01 `error`/`tester`, 32 skip, 0.
  - `/health` at 500: 5 (AC-01, AC-06, AC-07, AC-08, AC-10). T-01 to T-17 pass, and 14 are `error`/`system`.
  - Both features: 31 pass and system is 8. AC-01 and AC-02 are each listed by 7 passing tests.
  - So step 2's four guards and step 3's guard pass today.
- Step 4: today's system basis lacks "pass or fail" and "AC-11", so its written-first test fails. The component guard's string equals `Source/Tester/pod_tests.py:351-352`. Spec §4.1 starts at `docs/base/specifications.md:311` and holds the AC-11 line at `:360-362`.
- Step 5's `format: uri` line holds under its stated limits. Under RFC 3986, a URI that starts with `http://` or `https://` is `"//" authority path-abempty`. Its characters are unreserved, pct-encoded, sub-delims, `:`, `@`, `/`, `[` and `]`, none of them whitespace. With a non-empty host and no `?`, `#` or `@`, it matches `^https?://[^\s?#@]+$` (`Source/Tester/api.py:22`). The reverse example `http://a%zz/system` matches the pattern (Python `re`). The own-system text matches `Source/Tester/own_system.py:15-39` and the W4-8 decisions (`docs/state/WORK-ITEMS.md:214`).
- Checks and Done lines:
  - Step 5's two greps print nothing today.
  - Step 7's pattern, with 2.4.0 in place of 2.5.0, prints `docs/contract/pod-contract.md:2` today.
  - Step 6's grep lists exactly the eleven lines the step names, and `git grep -n -i "answered" -- docs/base/specifications.md` prints nothing. Outside `docs/closed` and `docs/epics`, the only other 2.4.0 mentions are history (`docs/base/phase4.md`, `docs/README.md:105`, `docs/decisions/contract-contradictions.md`).
  - `- [ ]` appears only at `docs/contract/pod-contract.md:145`.
  - Done line 7's 9 = 2 + 4 + 1 + 2, and its `-k` collects only the two existing tests today.
  - `.importlinter` holds 5 contracts.
  - `python -m pytest tests/tester -q` gives `53 passed` today.
  - Every step names its files, one check with its output and its trailer. Every Done line but line 4 is a command with an output.
- Relies on holds: `pod-tester.openapi.yml:101-104` (pattern), `:130`, `:133` (descriptions, no `model`, no `additionalProperties`), `page.html:223`, spec lines 73, 409, 709 and 716, ADR 0001, commit `6371a3e`, `.claude/hooks/step-trailer.py:12`, and the PDF quote on p. 5.
- Open questions: 1 and 2 have sourced answers. 3 is row E04-1 in `docs/decisions/OPEN-DECISIONS.md`, which blocks Done lines 3 and 12 and the pull request, not the steps. No new row is needed.

Notes, not blocking:

- Step 6 lists the top line of `pod-contract.md` only among the places where 2.4.0 becomes 2.5.0. That line also says "agreed by Team 16 (recorded 2026-11-05) … the first agreed version" (`docs/contract/pod-contract.md:3`). If only the number changes, the 2.5.0 text claims an agreement that does not exist yet, and no check catches it. Step 7's grep would then pass on the old date. When building step 6, make the top line say proposed and pending, as §10 does. A cheap guard to add to step 6's check: `git grep -n -E "agreed by Team 16|is agreed by both teams|first agreed version" -- docs/contract/pod-contract.md` prints nothing.
- Done line 6 says the output "ends with `passed`". pytest's last line reads `53 passed in 63.15s (0:01:03)`, so the auditor should read it as "the summary line says `passed` and no `failed`".
- Step 5 defines "a tester's own system" for both teams in terms of Railway, which is how Team 15 hosts. Team 16 may host elsewhere. Their agreement (step 7) covers it, but the wording could say "the team's deployed URL".
- Done line 3 needs more than ruling E04-1. The "Contract 2.5.0" section intro in `docs/decisions/OPEN-DECISIONS.md` also names E04, so it must go with the row.
- `lint-imports` is not installed in this checkout, so Done line 10 was not run.

Revised by the author on 2026-11-22, after the ruling on E04-1: the Status is `draft` again, and steps 8 to 13 are added for build order steps 5.7 and 5.6. The Goal, Relies on, Done criteria, Out of scope and Open questions follow them. Steps 1 to 7 and the three reviews above are unchanged. A new review follows.

REVISE · design-reviewer at 5c7a2e4 · 2026-11-22

Scope: steps 8 to 13 and every section the revision changed (`git diff 928a0b0 5c7a2e4` removes only the old title, W-row, Goal paragraph, Done line 12, Out of scope paragraph and open question 3; steps 1 to 7 and the three reviews are untouched).

What holds:

- The filled-copy check prints nothing (exit 1). No `DESIGN.md` is needed: `git grep -n -E "T-2[123]" -- docs/diagrams docs/invariants` prints nothing, no import changes, and INV-1 only cites `model-golden-outputs.json` as a source.
- No conflict with a level above. Steps 8 to 13 follow the human's lines in the W4-9, W4-5 and W4-10 rows (`docs/state/WORK-ITEMS.md:212`, `:217`, `:218`). Keeping 2.5.0 is what contract §10 says (`docs/contract/pod-contract.md:339-343`). §5's AC table keeps "Phase 5" and "inspection", rightly, since it is a word-for-word copy of `docs/contract/spec-v1.1.md:180`, `:184`. `RULED/` holds only its README.
- Relies on holds at the cited lines: `Source/Tester/pod_tests.py:188-206`, `:312-314`, `:351-355`, `:371-380`, `:483-486`; `Source/Tester/page.html:406-411`; `tests/tester/conftest.py:16`, `:29`, `:68-71`; `tests/connector/test_model_golden.py:23`; contract `:40`, `:53-57`, `:102-103`, `:122-140`, `:152-155`, `:184-186`, `:198-200`, `:339-343`; spec `:331`, `:334`, `:351-352`, `:368-369`, `:395`, `:494-496`, `:748`; `docs/base/requirements-to-tests.md:38`; the W1-8 live run. L2, L5 and L6 have empty `behavioral` in the golden file. c8 and c1 give 3 findings, so "all 3 findings start PENDING_REVIEW" is right.
- Counts: `--collect-only` gives 31 for `test_pod_tests.py`, 29 for `test_model_golden.py`, 340 for the whole suite, and 0 for Done line 12's `-k`. CI on `main` at `97c5dea` passed 333 (run 45066284820), and steps 1 to 4 added 7, which gives 340. So 36, 40, 43, 45, 32, 14 and 357 follow. `python -m pytest tests/tester/test_pod_tests.py -q` gives `31 passed` today.
- The probe holds. Today's `run_suite` against `FakeTarget` with `own=True` gives system, component and model of 8, 6, 6 (plain), 7, 6, 5 (`model_drift`), 8, 6, 6 (both) and 5, 5, 4 (neither). Adding AC-04/REQ-03 (step 8), AC-05/C7 (step 9) and AC-09/REQ-06 (step 10) gives the after-values the Epic states. I went through every existing test in `tests/tester/test_pod_tests.py` for each step: the only literals that move are the ones the steps name (`:51`, `:52`, `:70`, `:129-131`, `:220`, `:226-228`). `tests/tester/test_api.py:103-109` checks only the count of the catalog.
- L8 reproduces. `t23-fixture/model_fixture_l8.py`, with its `SOURCE` pointed at this checkout's `Source/`, builds L-pre to L7 at contract §3's SHAs and L8 at `c8058c2e8a52b5b1e86710e0821b94437fc438e1`. `drifter check` on L8, run twice, gave identical output (aligned, three empty lists), exit 0, a clean `git status` and no `l8-code-was-run.txt`. `l8-case.json` holds the case as step 10 describes it.
- Step 12's ten greps give the "Today" outputs the Epic states. Step 13's grep prints both file names today, and each of its six phrases matches only where it says. Done lines 3 and 11 hold today (nothing, and `:2`).
- Open questions 1, 2, 4 and 5 have sourced answers. Question 3 is ruled (W4-9 row). No row is needed in `docs/decisions/OPEN-DECISIONS.md`.

What must change for RATIFY:

1. L8 is already pushed, so Relies on is stale. `git ls-remote https://github.com/kaan-kanadasi/doc-tracker-model-fixtures` shows `refs/heads/main` and `refs/tags/L8` at `c8058c2e8a52b5b1e86710e0821b94437fc438e1`. Relies on (line 49) still says `main` is at L7. Out of scope ("Pushing L8 …"), the "Not a Done line" paragraph and step 13 ("once L8 is pushed") still treat the push as pending. Record that it is pushed. The localhost run in the W4-5 and W4-10 rows then has nothing left to wait for.
2. Step 12 misses a contract line that becomes untrue. `docs/contract/pod-contract.md:22` says that `model-golden-outputs.json` holds "expected answers for T-24 to T-33 (section 3)". After steps 8 to 10 it also serves T-21's model version, T-22 and T-23 (L8). Step 12 already fixes the same claim in §3's "Used by" cell. Add `:22` to step 12 with a grep and its literal output, and add that grep to Done line 15.
3. Relies on (line 50) says `model_fixture_l8.py` is `scripts/model_fixture.py` "plus three texts and one entry". It also differs at line 13: `SOURCE = Path(__file__).resolve().parent / "drifter-src" / "Source"` instead of `parents[1] / "Source"` (`diff --strip-trailing-cr`). Say so, and have step 10 say that the `SOURCE` line is not copied.

Notes, not blocking:

- Step 9's two fail tests and step 10's fail test name only `flip_aligned_case`. Without `features = ["model_drift"]`, T-22 and T-23 skip, so the tests could never pass. Write the features into each of the three.
- The replay of L8 through the service (`test_analyze_answers_each_case_as_published`) was run neither by the draft nor by this review; only `drifter check` was. Step 10's check covers it.
- Contract §3's checklist "For each group: … Bump the version (section 10)" (`:140-146`) would read as unmet for group 3, which keeps 2.5.0. Consider adding a word in step 12 that §10 lets group 3 ship in 2.5.0.
- Steps 8 to 13 each run more than one command. The W4-9 ruling sanctions the second command, the run of the whole file. Step 12's ten greps are one check block.

Revised by the author after the review at 5c7a2e4: findings 1 to 3 are addressed in Relies on, steps 10, 12 and 13, Done line 15 and Out of scope (L8 is pushed; the table of files at the top of the contract gets its own change and grep, which makes eleven; the `SOURCE` line is named). The first and third notes are taken up in steps 9, 10 and 12.

RATIFY · design-reviewer at 7cdd9c6 · 2026-11-22

Scope: steps 8 to 13 and every section the revision changed. `git diff 5c7a2e4 7cdd9c6` touches only Relies on (lines 49-51), steps 9, 10, 12 and 13, Done line 15, Out of scope and the Review section. Steps 1 to 7 and the earlier verdicts are unchanged.

- The three findings of the review at 5c7a2e4 are fixed on disk:
  - Finding 1: `git ls-remote https://github.com/kaan-kanadasi/doc-tracker-model-fixtures` gives `HEAD`, `refs/heads/main` and `refs/tags/L8` at `c8058c2e8a52b5b1e86710e0821b94437fc438e1` and `refs/tags/L7` at `d288268…`, as Relies on (line 49) now says. `grep -n -i "pushed\|pushes"` finds no remaining "once L8 is pushed" in the Epic's sections; Out of scope and step 13 record the push as done.
  - Finding 2: `docs/contract/pod-contract.md:22` reads "expected answers for T-24 to T-33 (section 3)". Step 12 changes it and adds grep 11, and Done line 15 counts eleven greps.
  - Finding 3: `diff --strip-trailing-cr scripts/model_fixture.py t23-fixture/model_fixture_l8.py` shows the `SOURCE` line (13), the three texts and the L8 entry, and nothing else. Relies on (line 50) and step 10 name the `SOURCE` line.
- The filled-copy check prints nothing (exit 1). No `DESIGN.md` is needed: no import changes (`docs/diagrams/dependency.md:79`, A4), and `git grep -n -i -E "T-2[123]|skip|pod_tests|feature|model_fixture|golden"` over the five models and `docs/invariants` finds nothing about the tester or the fixture (INV-1 only cites the golden file).
- No conflict with a level above. Steps 8 to 13 follow the human's 2026-11-22 lines in the W4-9, W4-5 and W4-10 rows (`docs/state/WORK-ITEMS.md:212`, `:217`, `:218`). Keeping 2.5.0 matches contract §10 (`docs/contract/pod-contract.md:339-343`). The per-step "own check, then the whole file" follows the W4-9 ruling. `RULED/` holds only its README.
- Relies on holds at the cited lines: `Source/Tester/pod_tests.py:188-206`, `:312-314`, `:351-355`, `:371-380`, `:483-486`; `Source/Tester/page.html:406-411`; `tests/tester/conftest.py:16`, `:29`, `:68-71`; `tests/connector/test_model_golden.py:23`; contract `:22`, `:40`, `:53-57`, `:102-103`, `:122-140`, `:152-155`, `:184-186`, `:198-200`, `:339-343`; spec `:331`, `:334`, `:351-352`, `:368-369`, `:378-388`, `:395`, `:494-496`, `:748`; `docs/base/requirements-to-tests.md:38`; the W1-8 live run (`docs/state/WORK-ITEMS.md:146`: 7 of 10, 6 of 7, 5 of 7).
- Counts: `python -m pytest tests/tester/test_pod_tests.py -q` gives `31 passed`. `--collect-only` gives 29 for `test_model_golden.py`, 340 for the whole suite, and none for Done line 12's `-k` (31 deselected). So 36, 40, 43, 45, 32, 14 and 357 follow.
- The probe holds, re-run independently by patching `TESTS` in memory (T-21 with `drift("L2")` under `model_drift` only, T-22 and T-23 with drift checks) against `FakeTarget` with `own=True`. System, component, model: today 8/6/6 plain, 7/6/5 `model_drift`, 8/6/6 both, 5/5/4 neither. After step 8, `model_drift` 8/6/6. After step 9, `model_drift` and both 9/7/6. After step 10, `model_drift` and both 10/7/7, and only T-18 to T-20 skip. Plain and neither stay 8/6/6 and 5/5/4. Every existing literal that moves in `tests/tester/test_pod_tests.py` (`:51`, `:52`, `:70`, `:129-131`, `:220`, `:226-228`) is named in its step; `:77`, `:86-87`, `:98`, `:108`, `:116` and `:122` stay true. No other file under `tests/` asserts T-21 to T-23 or the fixed skips.
- L8 replays through the service. A scratch run mirrored `t23-fixture/build` as `test_model_golden.py`'s fixture does and posted `l8-case.json`'s request to `/system/analyze` through `TestClient`: 200, `drift` equal to the expected answer, `drift_error` null, no `l8-code-was-run.txt` anywhere. `l8-case.json` matches the golden file's indentation, so step 10's byte-for-byte copy fits.
- Step 12's eleven greps give the "Today" outputs the Epic states, and each of grep 9's six phrases gives `1` alone. The old phrases occur only at the lines step 12 changes (`grep -n` over the contract). Step 13's grep prints both file names today. Done lines 3 and 11 hold today (nothing, and `docs/contract/pod-contract.md:2`).
- Every step from 8 to 13 names its files, its check with the output that means done, and its trailer. Every Done line but line 4 is a command with its output.
- Open questions 1, 2, 4 and 5 have sourced answers; 3 is ruled (W4-9 row). No row is needed in `docs/decisions/OPEN-DECISIONS.md`, and `git grep -n "E04"` there prints nothing.

Notes, not blocking:

- `docs/base/specifications.md:519-520` says AC-05 is tested by the pod "only in Phase 5 (T-22)", and `:536` says AC-09 is validated "also by inspection". Both stay true after the Epic, but step 13's "any other line the change makes untrue follows (R2)" should look at them.
- Step 12's check is eleven commands, not one. It is a single check block over one file, as step 5's two greps were when ratified.
- `lint-imports` was not run in this review (Done line 10).

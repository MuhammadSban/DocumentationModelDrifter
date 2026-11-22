# E04: Contract 2.5.0, system coverage from evaluated tests

Status: draft · Owner: Kaan

W-row: W4-9 in `docs/state/WORK-ITEMS.md` (build order steps C.4 and C.5) · Branch: `E04-contract-2-5-0`

## Goal

Our tester's `coverage.system` counts a criterion only when a test that lists it ended `pass` or `fail`; `coverage.component` keeps today's rule (`pass`, `fail`, or `error` with source `system`, from a test the target answered). The pod contract becomes version 2.5.0 and states both rules, what "in scope" means for system coverage (AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10), and how a tester knows a target is its own system. The decision is the human's, in the W4-9 row of `docs/state/WORK-ITEMS.md` ("Decided by the human, 2026-11-22": "evaluated" means a test that ended pass or fail; the course PDF leaves the rule to the pod, and the stricter reading makes the report explicit about what was really checked). Team 16's tester and system see this change, so it is a ⚠ CONTRACT CHANGE: it applies once Team 16 agrees (contract §10).

This Epic does not close when its steps are done. Steps 5.6 and 5.7 (W4-5 and W4-10) add their rules for T-21, T-22 and T-23 to this same branch and the same contract version; the one pull request opens and merges only after Team 16 agrees to the 2.5.0 text and that code is on the branch (Done criteria).

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: none in `docs/diagrams/` describes the suite report or the contract's coverage rules, so none is read or changed. `docs/diagrams/dependency.md` reads: rule A4 holds, since no import changes. The seam is `run_suite`'s returned report and nothing below it, so no `DESIGN.md` (see open question 1).
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W4-9 row's "Decided by the human, 2026-11-22" line is the decision. The W4-8 row's five decisions say what "our own system" is, which section 5's new paragraph restates.
- Invariants: none read or changed.
- Other sources:
  - The course PDF, "Coverage fields" (p. 5): system coverage counts "how many acceptance criteria from the shared pod specification the suite evaluated out of all criteria in scope", using "the pod's criterion IDs and stated evaluation rules".
  - `docs/contract/pod-contract.md`: §1 (Team 16's tester's changes, the line "It counts coverage only from tests the target answered (section 5)"), §3 (the open box "Bump the version (section 10)"), §4 (each test's criteria; T-30 lists AC-02 for AC-11), §5 ("What counts"), §8 (the registry URLs at tag `contract-2.4.0`), §10 (agreement and version).
  - `docs/contract/pod-tester.openapi.yml`: `SuiteReport.coverage` (`system` description "Criteria AC-01 to AC-10 exercised by a test the target answered"; no `model` entry; no `additionalProperties: false`), `SetupRequest.target_url` (a plain string), `info.version`.
  - `docs/contract/pod-contract.openapi.yml`: `info.version`.
  - `Source/Tester/pod_tests.py`: `run_suite` (one `answered and (pass or fail or source system)` rule feeds both `components` and `criteria`; the basis strings say "exercised by a test the target answered"); `Result.answered`; `_run_one`.
  - `Source/Tester/own_system.py`: `REGISTRY_SYSTEM_URL`, `normalise`, `is_own`.
  - `Source/Tester/api.py`: `TARGET_URL`, the pattern a `target_url` must match.
  - `Source/Tester/page.html:223`: the label "Contract 2.4.0".
  - `tests/tester/test_pod_tests.py`: the `fake` and `closed_url` fixtures, `test_5xx_is_a_system_error_that_still_counts_as_answered`, `test_target_meeting_the_contract_passes_everything_it_runs` (system 8 today), `test_run_limit_ends_the_test_in_progress_and_skips_the_rest`.
  - `docs/base/specifications.md`: lines 73, 409, 709 and 716 name version 2.4.0 and say it is agreed.
  - `docs/closed/E03-model-coverage/EPIC.md`: the form of a ratified Epic here.

## Steps

One commit per step, made after the step's check passes. Each named test checks one behaviour, and each step's check selects its tests by name. A guard is a test expected to pass once written, because today's code already behaves as it asks; every other new or changed assertion is written first and fails before the code changes. Expected values are literals, read from contract §4.

### Step 1/6: system stops counting an error with source system

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`
- What: `run_suite` keeps two sets apart. `components` takes a test's components under today's rule; `criteria` takes a test's criteria only when it ended `pass` or `fail`. Test, changed first: `test_5xx_is_a_system_error_that_still_counts_as_answered` keeps `component` `covered == 6` and gains `system` `covered == 2`: with every `/analyze` answering 500, only T-15 passes, and it lists AC-06 and AC-08 (contract §4). Today that count is 8.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_5xx_is_a_system_error_that_still_counts_as_answered"` → `1 passed`
- Trailer: `Step: 1/6`

### Step 2/6: skip and every other error add nothing to system

- Files: `tests/tester/test_pod_tests.py`
- What: four guards, one per outcome, each asserting `coverage.system.covered` as a literal. Today's rule already leaves these out; the guards pin it under the new one.
  - `test_system_does_not_count_a_skipped_test`: the `fake` target as it is; T-22 and T-23 skip and T-24 to T-33 skip (no `model_drift`), so AC-05 and AC-09 are not covered: `covered == 8`, `total == 10`.
  - `test_system_does_not_count_an_error_from_communication`: `closed_url`; every test is `error` with source `communication`: `covered == 0`.
  - `test_system_does_not_count_an_error_from_the_tester`: a run limit shorter than one `/analyze` call (`fake.analyze_delay`), as `test_run_limit_ends_the_test_in_progress_and_skips_the_rest` does, so T-01 is `error` with source `tester` and the rest skip: `covered == 0`.
  - `test_system_does_not_count_an_error_when_health_fails`: `fake.health_status = 500`; T-18 to T-21 and T-24 to T-33 are `error` with source `system` because `/health` failed, and T-01 to T-17 pass: `covered == 5` (AC-01, AC-06, AC-07, AC-08, AC-10).
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_does_not_count_"` → `4 passed`
- Trailer: `Step: 2/6`

### Step 3/6: a criterion counts once

- Files: `tests/tester/test_pod_tests.py`
- What: one guard. `test_system_counts_a_criterion_listed_by_two_evaluated_tests_once`: the `fake` target as it is; T-01 to T-07 all pass and all list AC-01, and T-15 lists AC-06 and AC-08 beside T-14 and T-16, yet `covered == 8` and `total == 10`.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_counts_a_criterion_listed_by_two_evaluated_tests_once"` → `1 passed`
- Trailer: `Step: 3/6`

### Step 4/6: the two basis strings

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`
- What: `system`'s basis says: criteria AC-01 to AC-10, each counted once, from tests that ended pass or fail, with AC-11 counted as AC-02 (pod-contract.md section 5). `component`'s basis keeps its wording, "components C1 to C7 exercised by a test the target answered (pod-contract.md section 5)". Tests:
  - `test_system_basis_names_pass_or_fail_and_ac_11`, written first: the basis contains "AC-01 to AC-10", "pass or fail", "AC-11" and "section 5".
  - `test_component_basis_keeps_the_answered_wording`, a guard: the basis equals today's string, as a literal.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_basis_ or test_component_basis_"` → `2 passed`
- Trailer: `Step: 4/6`

### Step 5/6: the contract text

- Files: `docs/contract/pod-contract.md`, `docs/contract/pod-tester.openapi.yml`
- What:
  - §5 "What counts" gives two rules. A component is covered when a test the target answered lists it and ended `pass`, `fail`, or `error` with source `system` (today's rule). A criterion is covered only when a test that lists it ended `pass` or `fail`. One sentence says why they differ: a component that answered with a 5xx was still exercised, but a criterion is checked only when its test's answer could be judged.
  - §5 says what "in scope" means for system coverage: AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10 on every system, and AC-11 counts as AC-02.
  - §5 defines a tester's own system as `own_system.py` decides it: after normalising `target_url` (scheme and host in lowercase, a default port dropped, a trailing slash stripped, the path compared exactly), it is the team's Railway public URL with `/system`, the system URL in the team's registry row, or `localhost`, `127.0.0.1` or `::1` on any port with the path `/system`, only when the tester is not running on Railway. Only then does the report carry `coverage.model`.
  - §5 gains one line that our `target_url` pattern (an `http` or `https` URL with no query, fragment or credentials, `Source/Tester/api.py` `TARGET_URL`) accepts only values that are also valid under the course's `format: uri`.
  - §1's line "It counts coverage only from tests the target answered (section 5)" says both rules.
  - `pod-tester.openapi.yml`: `coverage.system`'s description says criteria AC-01 to AC-10 from tests that ended pass or fail; `coverage` gains an optional `model` entry (`CoverageMeasure`), described as present only in a report whose tester and target belong to the same team.
- Check: `git grep -c -E "ended .?pass.? or .?fail|in scope|own system|format: uri" -- docs/contract/pod-contract.md` → `docs/contract/pod-contract.md:4` or more, and `python -m pytest tests/tester -q -k "validates_against_the_pod_tester_openapi"` → `1 passed`
- Trailer: `Step: 5/6`

### Step 6/6: the version

- Files: `docs/contract/pod-contract.md`, `docs/contract/pod-contract.openapi.yml`, `docs/contract/pod-tester.openapi.yml`, `Source/Tester/page.html`, `docs/base/specifications.md`
- What: every 2.4.0 becomes 2.5.0. In `pod-contract.md`: the top line, the two registry URLs in §8 (tag `contract-2.5.0`), and §10, where "it is the first agreed version" goes and the text says 2.5.0 is proposed and applies once Team 16 agrees. Both openapi files' `info.version`. The label in `page.html`. The four mentions in `docs/base/specifications.md` (lines 73, 409, 709, 716); while Team 16 has not agreed, those that say "agreed" say "proposed, pending Team 16's agreement" instead. Tick §3's open box "Bump the version (section 10)". Any spec line that describes how system coverage counts follows step 5; at drafting `git grep -n -i "answered" -- docs/base/specifications.md` prints nothing, so none is known.
- Check: `git grep -n "2\.4\.0" -- docs/contract docs/base/specifications.md Source` → prints nothing
- Trailer: `Step: 6/6`

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
7. The named tests pass: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_5xx_is_a_system_error_that_still_counts_as_answered or test_system_does_not_count_ or test_system_counts_a_criterion_listed_by_two_evaluated_tests_once or test_system_basis_ or test_component_basis_"` → `8 passed`
8. No old version left: `git grep -n "2\.4\.0" -- docs/contract docs/base/specifications.md Source` → prints nothing
9. No open box in §3: `git grep -n -F -- "- [ ]" docs/contract/pod-contract.md` → prints nothing
10. Imports still follow the map: `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`
11. The human's line: Team 16 agrees to the 2.5.0 text, and the agreement is recorded in `pod-contract.md` §10 with its date.
12. The human's line: the code of steps 5.6 and 5.7 (W4-5 and W4-10), with their rules for T-21, T-22 and T-23 in the same contract version, is on this branch, and both rows are marked done.
13. The human's line: this Epic does not close when its six steps are done. Its one pull request is opened only after lines 11 and 12 hold, before the audit, and the Epic merges through it.
14. The human's line, after the merge: the tag `contract-2.5.0` on the merge commit, and both teams' registry rows pointing to it.

## Out of scope

The rules for T-21, T-22 and T-23: build order steps 5.6 and 5.7, rows W4-5 and W4-10. They are added to this branch later, in the same contract version 2.5.0, and are not steps of this Epic. Also out: the `/tester` page showing `coverage.model` and an end-to-end `test_run` test (left over from E03, `docs/state/WORK-ITEMS.md` Next action).

## Open questions

1. Does a change to the pod contract count as a boundary change that needs a `DESIGN.md` beside this Epic (`docs/epics/README.md`, Naming)? The draft reads "boundary" as a module boundary or a model in `docs/diagrams/`, neither of which changes, and treats the contract as the boundary's own document, edited directly.
2. Who writes Team 16's agreement into §10, and does recording it need its own commit on this branch before the pull request opens (Done line 11)?

## Review

Not reviewed yet. The design reviewer writes RATIFY or REVISE here.

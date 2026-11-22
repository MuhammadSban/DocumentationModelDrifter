# E04: Contract 2.5.0, system coverage from evaluated tests

Status: draft · Owner: Kaan

W-row: W4-9 in `docs/state/WORK-ITEMS.md` (build order steps C.4 and C.5) · Branch: `E04-contract-2-5-0`

## Goal

Our tester's `coverage.system` counts a criterion only when a test that lists it ended `pass` or `fail`; `coverage.component` keeps today's rule (`pass`, `fail`, or `error` with source `system`, from a test the target answered). The pod contract becomes version 2.5.0 and states both rules, what "in scope" means for system coverage (AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10), and how a tester knows a target is its own system. The decision is the human's, in the W4-9 row of `docs/state/WORK-ITEMS.md` ("Decided by the human, 2026-11-22": "evaluated" means a test that ended pass or fail; the course PDF leaves the rule to the pod, and the stricter reading makes the report explicit about what was really checked). Team 16's tester and system see this change, so it is a ⚠ CONTRACT CHANGE: it applies once Team 16 agrees (contract §10).

This Epic does not close when its steps are done. Steps 5.6 and 5.7 (W4-5 and W4-10) add their rules for T-21, T-22 and T-23 to this same branch and the same contract version; how their work reaches this branch is the human's call, row E04-1 in `docs/decisions/OPEN-DECISIONS.md`. The one pull request is opened only after Team 16 agrees to the 2.5.0 text (step 7) and the code of steps 5.6 and 5.7 is on the branch (Done line 12), before the audit, and the Epic merges through it.

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

## Steps

One commit per step, made after the step's check passes. Each named test checks one behaviour, and each step's check selects its tests by name. A guard is a test expected to pass once written, because today's code already behaves as it asks; every other new or changed assertion is written first and fails before the code changes. Expected values are literals, read from contract §4.

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
- What: one guard. `test_system_counts_a_criterion_listed_by_two_evaluated_tests_once`: the `fake` target with `features = ["prose_detector", "model_drift"]`, so T-01 to T-21 and T-24 to T-33 all pass; AC-01 is listed by seven passing tests and AC-02 by more than ten, yet `covered == 8` and `total == 10` (AC-05 and AC-09 come only from T-22 and T-23, which skip).
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_counts_a_criterion_listed_by_two_evaluated_tests_once"` → `1 passed`
- Trailer: `Step: 3/7`

### Step 4/7: the two basis strings

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`
- What: `system`'s basis says: criteria AC-01 to AC-10, each counted once, from tests that ended pass or fail, with AC-11 counted as AC-02 (pod-contract.md section 5). AC-11 appears only in our tester's basis, as spec §4.1 (lines 360-362) and ADR 0001 count it; the contract text does not name it (step 5). `component`'s basis keeps its wording, "components C1 to C7 exercised by a test the target answered (pod-contract.md section 5)". Tests:
  - `test_system_basis_names_pass_or_fail_and_ac_11`, written first: the basis contains "AC-01 to AC-10", "pass or fail", "AC-11" and "section 5".
  - `test_component_basis_keeps_the_answered_wording`, a guard: the basis equals today's string, as a literal.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_system_basis_ or test_component_basis_"` → `2 passed`
- Trailer: `Step: 4/7`

### Step 5/7: the contract text

- Files: `docs/contract/pod-contract.md`, `docs/contract/pod-tester.openapi.yml`
- What:
  - §5 "What counts" gives two rules. A component is covered when a test the target answered lists it and ended `pass`, `fail`, or `error` with source `system` (today's rule). A criterion is covered only when a test that lists it ended `pass` or `fail`. One sentence says why they differ: a component that answered with a 5xx was still exercised, but a criterion is checked only when its test's answer could be judged.
  - §5 says what is in scope, in the phrase "in scope for system coverage": AC-01 to AC-10, AC-05 and AC-09 included, so `total` is 10 on every system. It does not name AC-11, which is Team 15's own (ADR 0001).
  - §5 defines "a tester's own system" as `own_system.py` decides it: after normalising `target_url` (scheme and host in lowercase, a default port dropped, a trailing slash stripped, the path compared exactly), it is the team's Railway public URL with `/system`, the system URL in the team's registry row, or `localhost`, `127.0.0.1` or `::1` on any port with the path `/system`, only when the tester is not running on Railway. Only then does the report carry `coverage.model`.
  - §5 gains one line on `target_url` and the course's `format: uri`, in the direction that holds: every system base URL that is a valid `format: uri` with a lowercase `http` or `https` scheme and no `?`, `#` or `@` also matches our pattern (`Source/Tester/api.py` `TARGET_URL`). The line does not claim the reverse: the pattern also accepts some strings that are not URIs, such as `http://a%zz/system`, so a tester does not use it to validate a URI.
  - §1's line "It counts coverage only from tests the target answered (section 5)" says both rules.
  - `pod-tester.openapi.yml`: `coverage.system`'s description says criteria AC-01 to AC-10 from tests that ended pass or fail; `coverage` gains an optional `model` entry (`CoverageMeasure`), described as present only in a report whose tester and target belong to the same team.
- Check: `git grep -h -o -E "ended .pass. or .fail.|in scope for system coverage|a tester's own system|format: uri" -- docs/contract/pod-contract.md | sort -u` → exactly four lines, one per phrase: "a tester's own system", "ended `pass` or `fail`", "format: uri", "in scope for system coverage". Today it prints nothing.
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
12. Steps 5.6 and 5.7 are done on this branch: `git grep -c -E "^\| W4-(5|10) \| \*\*Done" -- docs/state/WORK-ITEMS.md` → `docs/state/WORK-ITEMS.md:2`

## Out of scope

The rules for T-21, T-22 and T-23: build order steps 5.6 and 5.7, rows W4-5 and W4-10. They are added to this branch later, in the same contract version 2.5.0, and are not steps of this Epic. Also out: the `/tester` page showing `coverage.model` and an end-to-end `test_run` test (left over from E03, `docs/state/WORK-ITEMS.md` Next action).

After the merge, and not part of Done, the human tags the merge commit `contract-2.5.0` and points both teams' registry rows to it.

## Open questions

1. Does a change to the pod contract count as a boundary change that needs a `DESIGN.md` beside this Epic (`docs/epics/README.md`, Naming)? The draft reads "boundary" as a module boundary or a model in `docs/diagrams/`, neither of which changes, and treats the contract as the boundary's own document, edited directly. Answered: no `DESIGN.md`. A boundary here is a module boundary, "what calls what, and who owns which file" (`docs/templates/DESIGN.md:7`; INV-3, `docs/invariants/INVARIANTS.md:18`), and no import or module changes (`docs/diagrams/dependency.md:79`, rule A4). No model in `docs/diagrams/` describes the suite report or its coverage rules (`git grep -n -i "coverage\|suite"` over the five models prints only `data-flow.md:97`, the `drift` answer). E03 changed the same report's `coverage` object without a `DESIGN.md` and was ratified (`docs/closed/E03-model-coverage/EPIC.md`, Review, second finding).
2. Who writes Team 16's agreement into §10, and does recording it need its own commit on this branch before the pull request opens (Done line 11)? Answered: its own commit, written once the human reports Team 16's agreement, as 2.4.0's was (commit `6371a3e`, "Record Team 16's agreement to contract 2.4.0"). On this branch every agent commit needs `Step: i/N`, `plan` or `close` (`.claude/hooks/step-trailer.py:12`; R7), and none of steps 1 to 6 records the agreement, so the Epic needs a step for it (Review, finding 5).
3. Added by the design reviewer: how do the code and commits of W4-5 and W4-10 reach this branch and its one pull request, when R7 and `docs/epics/README.md` ("Build only from a live, ratified Epic"; Naming, Branch: "All work on the Epic happens on it") give each Epic its own branch and `Step:` lines? Not answered by the code, a model or a ruling: row E04-1 in `docs/decisions/OPEN-DECISIONS.md`.

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

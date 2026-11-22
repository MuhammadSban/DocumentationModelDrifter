# E03: Model coverage in our tester's report

Status: draft · Owner: Kaan

W-row: W4-8 in `docs/state/WORK-ITEMS.md` (build order steps C.1 to C.3) · Branch: `E03-model-coverage`

## Goal

When our tester runs against our own system, its suite report carries `coverage.model`: `total` is 7, the requirements REQ-01 to REQ-07 of `docs/base/specifications.md` §3.1, and `covered` is how many of them a test that ended pass or fail evaluated. Its `basis` names the design version, the version line of a new map file, `docs/base/requirements-to-tests.md`, and links that file on `main`. The map file is the only source of the requirement-to-criterion pairs: the tester reads them from it at run time and derives the tests from its own `TESTS` list. Against any other system the key is absent. The course PDF asks for this from Phase 5 ("Model coverage (model): Include this field only when testing your own system", p. 5). The key is optional and same-team only, so it changes nothing Team 16 sees and may merge before contract 2.5.0 (W4-9).

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/dependency.md` reads: rule A4, `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`, so the tester reads the Railway environment itself (`RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_PROJECT_ID`) and cannot use `GitHub_Connector.settings`. No model in `docs/diagrams/` describes the suite report, so none changes, and there is no `DESIGN.md`: no boundary, invariant or model changes.
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W4-8 row carries five calls marked "Decided by the human, 2026-11-22": the requirement list is REQ-01 to REQ-07; what "our own system" is, with the `target_url` normalisation; covered means a mapped test ended pass or fail; our registry row's system URL; and what "localhost" means.
- Invariants: none read or changed. INV-1 (determinism) concerns the check's answer, not the tester's report.
- Other sources: the course PDF, "Coverage fields" (p. 5); `docs/contract/pod-contract.md` §4 (each test's criteria); `docs/contract/pod-tester.openapi.yml` (the `coverage` object requires `code`, `component` and `system` and does not forbid other keys; `CoverageMeasure` allows null counts); spec §4.1 (each criterion's requirements) and §6.1, §6.2 (requirement coverage per phase); `Source/Tester/pod_tests.py` (`run_suite`, `_measure`, `TESTS`, `Result`); `Source/Tester/api.py` (`test_run`, and `TEAM16_SYSTEM_URL` as the pattern for a configured URL); the `Dockerfile` (which docs the image ships); `jsonschema` and `pyyaml`, already in the requirements files.

## Steps

One commit per step, made after the step's check passes. Each named test checks one behaviour, and each step's check selects its tests by name.

### Step 1/5: write the map file

- Files: `docs/base/requirements-to-tests.md` (new), `docs/README.md`
- What: the file opens with a version line, `Version: 1`. Then a pairs table with one row per criterion AC-01 to AC-10 and its requirements, equal to spec §4.1: AC-01 REQ-01; AC-02 REQ-02; AC-03 REQ-02, REQ-07; AC-04 REQ-03; AC-05 REQ-03; AC-06 REQ-04; AC-07 REQ-05; AC-08 REQ-05; AC-09 REQ-06; AC-10 REQ-07. One line says AC-11 counts as AC-02. Then the requirement-to-test table, one row per REQ-01 to REQ-07: its criteria and the tests that list them in contract §4. A short note says which tests skip on our system today (T-21, T-22, T-23), so REQ-03 and REQ-06 stay uncovered until W4-5 and W4-10. The docs map gets a "read it when" line.
- Check: `git grep -c -E "^\| (REQ-0[1-7]|AC-(0[1-9]|10)) " -- docs/base/requirements-to-tests.md` → `docs/base/requirements-to-tests.md:17`
- Trailer: `Step: 1/5`

### Step 2/5: the tester reads the map file

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`, `Dockerfile`
- What: a reader in `pod_tests.py` returns the file's version and, for each requirement, its criteria. The tests per requirement are derived from `TESTS`: every test that lists one of its criteria. The tester reads the file at run time, so the `Dockerfile` copies `docs/base/requirements-to-tests.md` into the image beside `docs/contract/`. Tests, written first:
  - `test_map_reader_returns_the_version_and_seven_requirements_with_their_criteria`
  - `test_map_table_equals_the_tests_derived_from_the_test_list`
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_map_"` → `2 passed`
- Trailer: `Step: 2/5`

### Step 3/5: tell our own system from another

- Files: `Source/Tester/own_system.py` (new), `tests/tester/test_own_system.py` (new)
- What: `own_system.py` normalises a `target_url` (scheme and host in lowercase, a default port dropped, a trailing slash stripped, the path compared exactly) and answers whether it names our own system: the Railway public URL, `https://$RAILWAY_PUBLIC_DOMAIN/system`; the registry URL; or a localhost form, only when `RAILWAY_PROJECT_ID` is unset. The registry URL is configured in `own_system.py` as the constant `REGISTRY_SYSTEM_URL = "https://documentationmodeldrifter-production.up.railway.app/system"`, as `TEAM16_SYSTEM_URL` is in `api.py`. Tests, written first, in `test_own_system.py`:
  - `test_normalise_lowercases_the_scheme`
  - `test_normalise_lowercases_the_host`
  - `test_normalise_drops_a_default_port`
  - `test_normalise_strips_a_trailing_slash`
  - `test_normalise_compares_the_path_exactly`
  - `test_railway_public_url_is_own`
  - `test_registry_url_is_own`
  - `test_localhost_off_railway_is_own`
  - `test_127_0_0_1_off_railway_is_own`
  - `test_ipv6_loopback_off_railway_is_own`
  - `test_localhost_on_railway_is_not_own`
  - `test_team16_url_is_not_own`
- Check: `python -m pytest tests/tester/test_own_system.py -q` → `12 passed`
- Trailer: `Step: 3/5`

### Step 4/5: report `coverage.model` for our own system only

- Files: `Source/Tester/pod_tests.py`, `Source/Tester/api.py`, `tests/tester/test_pod_tests.py`
- What: `test_run` asks `own_system` about the session's target and hands the answer to `run_suite`. For our own system `coverage.model` is `{covered, total: 7, basis}`: a requirement is covered only when a test mapped to it ended pass or fail, and each requirement counts once. `basis` names the map file's version and links `https://github.com/MuhammadSban/DocumentationModelDrifter/blob/main/docs/base/requirements-to-tests.md`. When the file cannot be read, `covered` and `total` are null and `basis` says why. For another system the key is absent. Tests, written first, with the `fake` target the existing tests use:
  - `test_model_is_present_for_our_own_system_with_total_7_and_covered_at_most_total`
  - `test_model_counts_a_requirement_with_no_evaluated_test_in_total`
  - `test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error`
  - `test_model_counts_a_requirement_listed_by_two_evaluated_tests_once`
  - `test_model_key_is_absent_for_another_system`
  - `test_model_report_validates_against_the_pod_tester_openapi`
  - `test_model_unreadable_map_gives_null_counts_and_a_basis_saying_why`
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k "test_model_"` → `7 passed`
- Trailer: `Step: 4/5`

### Step 5/5: update the spec

- Files: `docs/base/specifications.md`
- What: four edits. §4.1 names `docs/base/requirements-to-tests.md` as the source of its criterion-to-requirement pairs. One sentence in §4.1 says our tester reports `coverage.model` over REQ-01 to REQ-07 for our own system only. The same place says the list's version is the map file's version line. §6.2's "Requirement coverage" line (line 534) lists all seven, REQ-01 to REQ-07.
- Check: `git grep -c -E "requirements-to-tests.md|coverage.model|REQ-01, REQ-02, REQ-03, REQ-04, REQ-05, REQ-06, REQ-07" -- docs/base/specifications.md` → `docs/base/specifications.md:3` or more
- Trailer: `Step: 5/5`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → every spec line this Epic made wrong is in the diff; empty when the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E03" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The tester's tests pass: `python -m pytest tests/tester -q` → ends with `passed`, no `failed`
6. The map file has its version line and 17 rows: `git grep -c -E "^(Version: |\| (REQ-0[1-7]|AC-(0[1-9]|10)) )" -- docs/base/requirements-to-tests.md` → `docs/base/requirements-to-tests.md:18`
7. The named tests pass: `python -m pytest tests/tester -q -k "test_map_ or test_model_"` → `9 passed`, and `python -m pytest tests/tester/test_own_system.py -q` → `12 passed`
8. The image ships the map file: `git grep -n "requirements-to-tests.md" -- Dockerfile` → one `COPY` line
9. No commit SHA in the basis: `git grep -n "RAILWAY_GIT_COMMIT_SHA" -- Source/Tester` → prints nothing
10. Imports still follow the map: `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`

## Open questions

1. Which outcomes count as "evaluated" for `coverage.model` while contract 2.4.0 holds? Answered: only pass and fail, now, without waiting for 2.5.0 (W4-8 row, "Decided by the human, 2026-11-22").
2. What exactly is the URL in our registry row? Answered: `https://documentationmodeldrifter-production.up.railway.app/system` (W4-8 row, "Decided by the human, 2026-11-22").
3. Does "localhost" also mean `127.0.0.1` and `::1`, and any port? Answered: the hosts `localhost`, `127.0.0.1` and `::1`, on any port, only when not running on Railway (W4-8 row, "Decided by the human, 2026-11-22").

## Review

Not reviewed yet. The design reviewer writes RATIFY or REVISE here.

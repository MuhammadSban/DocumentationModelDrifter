# E03: Model coverage in our tester's report

Status: draft · Owner: Kaan

W-row: W4-8 in `docs/state/WORK-ITEMS.md` (build order steps C.1 to C.3) · Branch: `E03-model-coverage`

## Goal

When our tester runs against our own system, its suite report carries `coverage.model`: `total` is 7, the requirements REQ-01 to REQ-07 of `docs/base/specifications.md` §3.1, and `covered` is how many of them the suite evaluated. Its `basis` names the design version and links to a new mapping, `docs/base/requirements-to-tests.md`, from each requirement to its criteria and tests. Against any other system the key is absent. The course PDF asks for this from Phase 5 ("Model coverage (model): Include this field only when testing your own system", p. 5). The key is optional and same-team only, so it changes nothing Team 16 sees and may merge before contract 2.5.0 (W4-9).

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/dependency.md` reads: rule A4, `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`, so the tester reads the commit SHA and the Railway domain from the environment itself and cannot use `GitHub_Connector.settings`. No model in `docs/diagrams/` describes the suite report, so none changes, and there is no `DESIGN.md`: no boundary, invariant or model changes.
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W4-8 row carries two calls marked "Decided by the human, 2026-11-22": the requirement list is REQ-01 to REQ-07, and what "our own system" is, with the `target_url` normalisation.
- Invariants: none read or changed. INV-1 (determinism) concerns the check's answer, not the tester's report.
- Other sources: the course PDF, "Coverage fields" (p. 5); `docs/contract/pod-contract.md` §4 (each test's criteria) and §5 (what counts); `docs/contract/pod-tester.openapi.yml` (the `coverage` object lists `required: [code, component, system]` and does not forbid other keys); spec §4.1 (each criterion's requirement); `Source/Tester/pod_tests.py` (`run_suite`, `_measure`, `TESTS`); `Source/Tester/api.py` (`test_setup`, `test_run`); the `Dockerfile` (which docs the image ships).

## Steps

One commit per step, made after the step's check passes.

### Step 1/5: write the mapping from requirements to tests

- Files: `docs/base/requirements-to-tests.md` (new), `docs/README.md`
- What: one table row per requirement, REQ-01 to REQ-07: the criteria spec §4.1 ties to it, and the tests that list those criteria in contract §4. From §4.1: REQ-01 AC-01; REQ-02 AC-02, AC-03 (AC-11 counts as AC-02); REQ-03 AC-04, AC-05; REQ-04 AC-06; REQ-05 AC-07, AC-08; REQ-06 AC-09; REQ-07 AC-03, AC-10. A short note says which tests skip on our system today (T-21, T-22, T-23) and so leave REQ-03 and REQ-06 uncovered until W4-5 and W4-10. The docs map gets a "read it when" line.
- Check: `git grep -c "^| REQ-0[1-7] " -- docs/base/requirements-to-tests.md` → `docs/base/requirements-to-tests.md:7`
- Trailer: `Step: 1/5`

### Step 2/5: give the tester the requirement list, and keep it equal to the mapping

- Files: `Source/Tester/pod_tests.py`, `tests/tester/test_pod_tests.py`, `Dockerfile`
- What: a `REQUIREMENTS` table in `pod_tests.py`, each requirement with its criteria, as in step 1. A test reads `docs/base/requirements-to-tests.md` and fails if its rows and `REQUIREMENTS` disagree. The image runs `tests/` on the `/tester` page, so the `Dockerfile` copies `docs/base/requirements-to-tests.md` beside `docs/contract/`.
- Check: `python -m pytest tests/tester/test_pod_tests.py -q -k requirement` → passes, at least one test selected
- Trailer: `Step: 2/5`

### Step 3/5: tell our own system from another

- Files: `Source/Tester/api.py` or a new `Source/Tester/own_system.py`, `tests/tester/`
- What: a function that normalises a `target_url` (scheme and host in lowercase, a default port dropped, a trailing slash stripped, the path compared exactly) and answers whether it names our own system: the Railway public URL (`https://$RAILWAY_PUBLIC_DOMAIN/system`), the URL in our registry row, and localhost only when not running on Railway (`RAILWAY_PROJECT_ID` unset). Written test first: one test per normalisation rule, one for each of the three sources, one for localhost on Railway, one for Team 16's URL.
- Check: `python -m pytest tests/tester -q -k own_system` → passes, at least one test selected
- Trailer: `Step: 3/5`

### Step 4/5: report `coverage.model` for our own system only

- Files: `Source/Tester/pod_tests.py`, `Source/Tester/api.py`, `tests/tester/test_pod_tests.py`, `tests/tester/test_api.py`
- What: `run_suite` takes whether the target is our own system. If so, `coverage.model` is `{covered, total: 7, basis}`, where a requirement is covered when a test that counts under the rule of open question 1 lists one of its criteria. `basis` names the design version (spec §3.1 at the deployed commit) and links to `docs/base/requirements-to-tests.md` at that commit. Otherwise the key is absent. Written test first, with a stub target as the existing tests use.
- Check: `python -m pytest tests/tester -q -k model_coverage` → passes, at least one test selected
- Trailer: `Step: 4/5`

### Step 5/5: update the spec

- Files: `docs/base/specifications.md`
- What: §4.1 says that our tester reports `coverage.model` over REQ-01 to REQ-07 against our own system only, and links the mapping.
- Check: `git grep -n "requirements-to-tests.md" -- docs/base/specifications.md` → at least one line
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
6. The mapping has seven rows: `git grep -c "^| REQ-0[1-7] " -- docs/base/requirements-to-tests.md` → `docs/base/requirements-to-tests.md:7`
7. The image ships the mapping: `git grep -n "requirements-to-tests.md" -- Dockerfile` → one `COPY` line
8. Our own system gets the key, another does not: `python -m pytest tests/tester -q -k "model_coverage or own_system"` → passes, at least one test selected
9. Imports still follow the map: `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`

## Open questions

1. Which outcomes count as "evaluated" for `coverage.model` while contract 2.4.0 holds: today's §5 rule for component and system coverage (`pass`, `fail`, or `error` with source `system`), or `pass` and `fail` only, the reading ruled for system coverage in W4-9?
2. What exactly is the URL in our registry row? Contract §8 quotes the row's access notes, not its system URL. `Source/Frontend/README.md` names `https://documentationmodeldrifter-production.up.railway.app`, which would make the registry URL that host plus `/system`, the same as the Railway public URL.
3. Does "localhost" also mean `127.0.0.1` and `::1`, and any port, or only the port the app listens on (`PORT`, default 8000)?
4. What does `basis` name as the design version when `RAILWAY_GIT_COMMIT_SHA` is unset (a local run): the branch `main`, or no link at all?

## Review

Not reviewed yet. The design reviewer writes RATIFY or REVISE here.

# Invariants

What must hold, written apart from the code, so that a check compares the code with what it ought to do and not with what it did last time. Level 4 of the authority order in `CLAUDE.md`.

Adding a row, rewording one or changing a grade needs the human's approval. An Epic names the rows it reads or changes under Relies on, by ID. IDs are never reused.

## Grades

- **DEFERRED.** Nothing stops a change that breaks it from reaching `main`. The row names the step that adds the check.
- **ENFORCED-PROVEN.** A CI check fails when it breaks, and a planted violation has been seen to turn that check red.

## Entries

| ID | What must hold | Source | Grade | Check |
|---|---|---|---|---|
| INV-1 | Determinism: the same repository version, `/models` and tool version give byte-identical models and a byte-identical answer on every run. | Spec REQ-07 and AC-10 (`docs/base/specifications.md`); the published answers in `docs/contract/golden-outputs.json` and `docs/contract/model-golden-outputs.json` | DEFERRED | CI runs `pytest`, which includes `tests/connector/test_golden.py` and `tests/connector/test_model_golden.py`, on every pull request and every push to `main` (`.github/workflows/ci.yml`, since W1-6), on Linux only. `test_golden.py` skips, and so stays green, when the runner cannot reach the fixture repository on GitHub. No planted break of determinism has been seen to turn the check red. Across platforms nothing is checked: the Windows job was deleted, so no check compares two operating systems. |
| INV-2 | Ownership: a commit that changes a file its author does not own is a violation, and no author can change the ownership or scope rules to pass their own change. | Spec §3.2, the VIOLATION row (`docs/base/specifications.md`); row W0-7 of `docs/decisions/OPEN-DECISIONS.md` | DEFERRED | The second half does not hold today: a self-grant in one commit passes (`docs/state/WORK-ITEMS.md`, "W0-7 in detail"). Waits for the human's ruling (step 4.1), then for its tests in step 4.3 or step 4.4. **The ruling must cover `scope.json`'s `verbosity` with the rest of the scope rules (E02, 2026-11-22):** lowering the level and running `drifter update` in one push is a legitimate re-baseline that reports no drift, so it hides every drift in what the level drops, and nothing warns a reviewer who does not read `scope.json` in the diff. It is gap G4 in a new place, not a new kind of hole. |
| INV-3 | Module boundaries: imports under `Source/` follow the module map, rules A1 to A6, less the ignore lines listed in `.importlinter`, and every `GitHub_Connector` module is listed in it. | The module map `docs/diagrams/dependency.md`; rule R5 in `CLAUDE.md`; row W1-5 of `docs/state/WORK-ITEMS.md` | ENFORCED-PROVEN | The `lint-imports` step of `.github/workflows/ci.yml` runs the five contracts of `.importlinter` on every pull request and every push to `main`. Proven red on 2026-11-21: draft PR #47 planted `drifter.check -> GitHub_Connector.settings`, and run 44939724034 failed at `Run lint-imports` only. Not proven in CI: the `connector` contract, which was seen failing only in a local run with an unlisted module. |

# Invariants

What must hold, written apart from the code, so that a check compares the code with what it ought to do and not with what it did last time. Level 4 of the authority order in `CLAUDE.md`.

Adding a row, rewording one or changing a grade needs the human's approval. An Epic names the rows it reads or changes under Relies on, by ID. IDs are never reused.

## Grades

- **DEFERRED.** Nothing stops a change that breaks it from reaching `main`. The row names the step that adds the check.
- **ENFORCED-PROVEN.** A CI check fails when it breaks, and a planted violation has been seen to turn that check red.

## Entries

| ID | What must hold | Source | Grade | Check |
|---|---|---|---|---|
| INV-1 | Determinism: the same repository version, `/models` and tool version give byte-identical models and a byte-identical answer on every run. | Spec REQ-07 and AC-10 (`docs/base/specifications.md`); the published answers in `docs/contract/golden-outputs.json` and `docs/contract/model-golden-outputs.json` | DEFERRED | `pytest tests/connector/test_golden.py tests/connector/test_model_golden.py` passes locally, and nothing runs it on a push until CI exists (step 0.5). Across platforms it stays DEFERRED after that: the Windows job was deleted, so no check compares two operating systems. |
| INV-2 | Ownership: a commit that changes a file its author does not own is a violation, and no author can change the ownership or scope rules to pass their own change. | Spec §3.2, the VIOLATION row (`docs/base/specifications.md`); row W0-7 of `docs/decisions/OPEN-DECISIONS.md` | DEFERRED | The second half does not hold today: a self-grant in one commit passes (`docs/state/WORK-ITEMS.md`, "W0-7 in detail"). Waits for the human's ruling (step 4.1), then for its tests in step 4.3 or step 4.4. |

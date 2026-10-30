# Docs map

- `base/student-facing-spec.docx.pdf` — blueprint for the project's testing part. Read it when writing or changing tests.
- `models/high-overview.png` — high-level flow: init proposes 3 models, the user commits them to `/models`, and each push is checked as Aligned, Drifted or Failed. Read it first to understand the system.
- `models/behavioral-model.png` — state machine for the same lifecycle (No models → Proposed → Baselined → Checking → Aligned/Drifted/Failed). Read it when working on state transitions or the push check.
- `base/specifications.txt` — the top-level specification: requirements, acceptance criteria and the pod contract. Read it before changing behavior, the API or the models.
- `history/phase2-changes.txt` — history, not instructions: what changed from Phase 2 and v1. Read it only for course reports; never build from it.

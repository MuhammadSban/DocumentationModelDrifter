# Docs map

Purpose: keep a repository's architecture documentation (the three models in `/models`) in step with its code. See `base/specifications.txt` §1.1–1.2.

When a diagram and the spec disagree, the spec wins.

## base/

- `base/specifications.txt` — the top-level specification: purpose, requirements, acceptance criteria, the four-field answer and the pod contract. Read it before changing behavior, the API or the models. Q11 lists the decisions still open.
- `base/student-facing-spec.docx.pdf` — the course's cross-team testing rules. Read it when writing or changing tests or the tester.

## models/

Diagrams of the planned system, exported from the Phase 4 overview page.

- `models/who-talks-to-what.png` — the developer, GitHub and a tester reach one drifter core through the CLI, the GitHub Action (Phase 5) and the hosted service; the repository is only read. Read it first to understand the system.
- `models/behavioral-model.png` — lifecycle of a repository under the tool: init proposes the models, a person commits them, and each push ends Aligned, Drifted or Failed. The Mermaid source in spec §3.2 is the text version. Known issue: it says "three fresh models", but ownership is checked against its rules, not regenerated (spec §3.2).
- `models/one-check.png` — one check step by step, from request to four-field answer, with the error code each step can return. Read it when working on the orchestrator or errors.
- `models/models-folder.png` — the four files in `/models` and what each holds. Element kinds and ids shown are illustrative; the real format is a pod decision.
- `models/comparison.png` — how differences are decided: set difference by id for structural and behavioral (ADDED, REMOVED, MODIFIED), a rule check per commit for ownership (VIOLATION).
- `models/four-field-answer.png` — the compare answer (`aligned`, `structural[]`, `behavioral[]`, `ownership[]`) and how a tester checks each field against the expected answer.
- `models/cross-team-test.png` — one cross-team test session: tester and system routes, the T-01 to T-17 loop, and the report.
- `models/research-evidence.png` — Team 15's tool research: what runs at runtime, what only serves tests, what is rejected. Team 15's choices, not the pod contract.

## history/

- `history/phase2-changes.txt` — history, not instructions: what changed from Phase 2 and v1. Read it only for course reports; never build from it.

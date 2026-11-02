# Docs map

Purpose: keep a repository's architecture documentation (the three models in `/models`) in step with its code. See `base/specifications.md` §1.1–1.2.

`GLOSSARY.md` at the repository root is the glossary: the terms the spec and code use, such as drift, accepting drift and acceptance criterion.

`adr/` holds architecture decision records: why a hard-to-reverse choice was made. Read them before reversing one.

When a diagram and the spec disagree, the spec wins. For anything another team's tester or system sees (routes, JSON, tests), `contract/` wins over the spec. The course's `base/student-facing-spec.docx.pdf` wins over all of them.

## base/

- `base/specifications.md` — the top-level specification: purpose, requirements, acceptance criteria and the four-field answer. Read it before changing behavior, the API or the models. Q11 lists the decisions still open. Its §5 explains how this design meets the pod contract in `contract/`.
- `base/phase4.md` — the Phase 4 build plan: the alignment check against Team 16's package, the roadmap v1, v1.1 and v1.2 with owners and decisions D1 to D12, the contract test map, and the design questions Q1 to Q8 (decided, kept for their reasoning). A plan, not a source of truth: where it disagrees with the spec or the contract, they win.
- `base/structure.md` — the structural model's format: the generator's input, node and edge kinds, the id scheme and an example. Read it before changing the structural generator. The spec wins where they disagree.
- `base/behavioral.md` — the behavioral model's format, frozen as `generate_behavioral` writes it: state and transition kinds, the id scheme, the mining rules, what the miner leaves out, and an example. Read it before changing the behavioral generator. The spec wins where they disagree.
- `base/student-facing-spec.docx.pdf` — the course's cross-team testing rules. Read it when writing or changing tests or the tester.

## contract/

The pod contract with Team 16. Both teams' registry rows link it. It follows Team 16's v1.1 package with two deviations in behavior: no prose detector is required (Team 15's `issues` is always `[]`), and Team 15 adds the optional `drift`, `drift_error` and `POST /generate`. Each system lists its features in `/health`, and a tester skips, never fails, a test whose feature the target lacks. `contract/pod-contract.md` §9 lists every difference, and §10 says how it changes.

- `contract/spec-v1.1.md` — Team 16's v1.1 specification (their `SPEC.md`), copied unchanged: the prose detector, comparison rules and acceptance criteria the contract cites as "v1.1 SPEC". Its `openapi-system-v1.1.yaml` means `contract/pod-contract.openapi.yml`; the contract wins where they differ.
- `contract/pod-contract.openapi.yml` — the system API both testers call: shared routes and JSON, plus Team 15's optional additions. Read it before changing a route, a field or an error code.
- `contract/pod-contract.md` — the testing rules: sessions, fixtures, the test list T-01 to T-33 with the components and criteria each covers, the acceptance criteria, which tests skip and why, limits, retries, errors and how the contract changes. Read it when writing or changing tests or the tester.
- `contract/pod-tester.openapi.yml` — the tester API and suite report, as the course fixes them. Read it before changing the tester's routes or report.
- `contract/mapping-v1.1.yaml` — Team 16's shared classification rules, skip allowlist and code-to-doc mappings, copied unchanged. The system loads it at runtime.
- `contract/golden-outputs.json` — Team 16's expected answers for the 10 cases on their fixture repository, copied unchanged. Testers compare against it for T-01 to T-21.
- `contract/model-golden-outputs.json` — not yet written: the expected answers for the drift tests T-24 to T-33. `contract/pod-contract.md` §3 has the checklist for adding it.

## models/

Diagrams of the planned system. Each is a Markdown file whose Mermaid block is the source; GitHub draws it, and `python models/render.py` renders a PNG on demand (not committed). `agents/modeling.md` has the rules for modeling and drawing.

- `models/who-talks-to-what.md` — the developer, GitHub and a tester reach one drifter core (orchestrator, GitHub integration, three generators, comparison) through the CLI, the GitHub Action (Phase 5) and the hosted service, which serves the pod contract's routes and adds change detection and a result store; the repository is only read. Read it first to understand the system.
- `models/behavioral-model.md` — lifecycle of a repository under the tool: init proposes the models, a person commits them, and each push ends Aligned, Drifted or Failed. Only structural and behavioral are regenerated; ownership is checked against its rules (spec §3.2).
- `models/one-check.md` — one check step by step, from request to four-field answer, with the HTTP error or no-verdict code each step can return, the 80 s deadline per check, and what the hosted service adds. Read it when working on the orchestrator or errors.
- `models/models-folder.md` — the four files in `/models` and what each holds. Structural follows `base/structure.md` (imports and inherits edges, no calls); behavioral follows `base/behavioral.md` (states and transitions); init proposes one exact-path ownership rule per file.
- `models/model-seam.md` — the seam between the core and the three model owners: who writes which file, the element rule every structural and behavioral model follows, what the core does with each model in one check, how ownership is proposed and checked, and when an owner's model is ready to plug in. Read it before writing or changing a generator.
- `models/file-fetch.md` — how one check gets the repository's files: a fresh clone without file contents, batched downloads instead of one per file (two today: `/models`, then the in-scope files), reading with lazy fetching off so a failed download stops the check at once; with the measured times that decided it and what it leaves out. Read it before changing how the GitHub integration reads files.
- `models/comparison.md` — how differences are decided: set difference by id for structural and behavioral (ADDED, REMOVED, MODIFIED), a rule check per commit for ownership (VIOLATION).
- `models/four-field-answer.md` — test T-26: the four-field answer as the `drift` key of `POST /system/analyze`, how a tester compares it with `contract/model-golden-outputs.json`, and when the test passes, fails or is skipped. A test is skipped when the target's `/health` does not list `model_drift`, and is `error` when `/health` gives no 200 within 90 s.
- `models/cross-team-test.md` — one cross-team test session as `contract/pod-contract.md` defines it: tester and system routes, the T-01 to T-33 loop over both fixtures, and the report. The tester reads `/health` once first and skips each test whose feature the target does not list. It also shows the one-session 409 and the stop at 570 s of the 600 s run.
- `models/research-evidence.md` — Team 15's tool research, as a table: what runs at runtime, what only serves tests, what is rejected. Team 15's choices, not the pod contract.

## tickets/

- `tickets/tracker-gaps.md` — open work: what the wired drift check still owes, and what one check still needs to become a tracker that watches a repository on its own. Each row has a fix and a check that closes it. `base/phase4.md` owns the schedule; this file owns the detail.
- `tickets/contract-contradictions.md` — open work: each place where the contract, the spec, the diagrams, the course PDF or Team 16's v1.1 package disagree, with a fix, a check that closes it, and an owner. A ticket whose check passes moves to the file's closed table.

## history/

- `history/phase2-changes.md` — history, not instructions: what changed from Phase 2 and v1. Read it only for course reports; never build from it.
- `history/contract-2.4.0-changes.md` — what changed from contract 2.3.0 to 2.4.0, what it means for each team's system and tester, and the matching spec changes. Send it to Team 16 with the contract; the contract wins where they differ.

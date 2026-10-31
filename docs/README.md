# Docs map

Purpose: keep a repository's architecture documentation (the three models in `/models`) in step with its code. See `base/specifications.md` §1.1–1.2.

`CONTEXT.md` at the repository root is the glossary: the terms the spec and code use, such as drift, accepting drift and acceptance criterion.

`adr/` holds architecture decision records: why a hard-to-reverse choice was made. Read them before reversing one.

When a diagram and the spec disagree, the spec wins. For anything another team's tester or system sees (routes, JSON, tests), `contract/` wins over the spec. The course's `base/student-facing-spec.docx.pdf` wins over all of them.

## base/

- `base/specifications.md` — the top-level specification: purpose, requirements, acceptance criteria and the four-field answer. Read it before changing behavior, the API or the models. Q11 lists the decisions still open. Its §5 explains how this design meets the pod contract in `contract/`.
- `base/phase4.md` — the Phase 4 build plan: the alignment check against Team 16's package, the plugin seam for the model generators, build steps A to G and the open questions. A plan, not a source of truth: where it disagrees with the spec or the contract, they win.
- `base/structure.md` — the structural model's format: the generator's input, node and edge kinds, the id scheme and an example. Read it before changing the structural generator. The spec wins where they disagree.
- `base/student-facing-spec.docx.pdf` — the course's cross-team testing rules. Read it when writing or changing tests or the tester.

## contract/

The pod contract with Team 16. Both teams' registry rows link it. It follows Team 16's v1.1 package except two deviations: no prose detector is required (Team 15's `issues` is always `[]`), and Team 15 adds the optional `drift`, `drift_error` and `POST /generate`. Each system lists its features in `/health`, and a tester skips, never fails, a test whose feature the target lacks. `contract/pod-contract.md` §9 lists every difference, and §10 says how it changes.

- `contract/pod-contract.openapi.yml` — the system API both testers call: shared routes and JSON, plus Team 15's optional additions. Read it before changing a route, a field or an error code.
- `contract/pod-contract.md` — the testing rules: sessions, fixtures, the test list T-01 to T-33 with the components and criteria each covers, the acceptance criteria, which tests skip and why, limits, retries, errors and how the contract changes. Read it when writing or changing tests or the tester.
- `contract/pod-tester.openapi.yml` — the tester API and suite report, as the course fixes them. Read it before changing the tester's routes or report.
- `contract/mapping-v1.1.yaml` — Team 16's shared classification rules, skip allowlist and code-to-doc mappings, copied unchanged. The system loads it at runtime.
- `contract/golden-outputs.json` — Team 16's expected answers for the 10 cases on their fixture repository, copied unchanged. Testers compare against it for T-01 to T-21.
- `contract/model-golden-outputs.json` — not yet written: the expected answers for the drift tests T-24 to T-33. `contract/pod-contract.md` §3 has the checklist for adding it.

## models/

Diagrams of the planned system, exported from the Phase 4 overview page.

- `models/who-talks-to-what.png` — the developer, GitHub and a tester reach one drifter core through the CLI, the GitHub Action (Phase 5) and the hosted service, which serves the pod contract's routes and adds change detection and a result store; the repository is only read. Read it first to understand the system.
- `models/behavioral-model.png` — lifecycle of a repository under the tool: init proposes the models, a person commits them, and each push ends Aligned, Drifted or Failed. The Mermaid source in spec §3.2 is the text version. Only structural and behavioral are regenerated; ownership is checked against its rules (spec §3.2).
- `models/one-check.png` — one check step by step, from request to four-field answer, with the HTTP error or no-verdict code each step can return, and what the hosted service adds. Read it when working on the orchestrator or errors.
- `models/models-folder.png` — the four files in `/models` and what each holds. Element kinds and ids shown are illustrative and predate `base/structure.md`, which wins for structural (edge kinds are `imports`, `inherits`, `calls`).
- `models/comparison.png` — how differences are decided: set difference by id for structural and behavioral (ADDED, REMOVED, MODIFIED), a rule check per commit for ownership (VIOLATION).
- `models/four-field-answer.png` — test T-26: the four-field answer as the `drift` key of `POST /system/analyze`, how a tester compares it with `contract/model-golden-outputs.json`, and when the test passes, fails or is skipped. Out of date since contract 2.4.0: a test is skipped when the target's `/health` does not list `model_drift`, not when the answer has no `drift` key.
- `models/cross-team-test.png` — one cross-team test session as `contract/pod-contract.md` defines it: tester and system routes, the T-01 to T-33 loop over both fixtures, and the report. Out of date since contract 2.4.0: the tester first reads `/health` and skips each test whose feature the target does not list; the "no drift key" note is replaced by that rule.
- `models/research-evidence.png` — Team 15's tool research: what runs at runtime, what only serves tests, what is rejected. Team 15's choices, not the pod contract.

## history/

- `history/phase2-changes.md` — history, not instructions: what changed from Phase 2 and v1. Read it only for course reports; never build from it.

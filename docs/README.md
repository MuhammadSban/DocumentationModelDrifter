# Docs map

Purpose: keep a repository's architecture documentation (the three models in `/models`) in step with its code. See `base/specifications.md` §1.1–1.2.

`GLOSSARY.md` at the repository root is the glossary: the terms the spec and code use, such as drift, accepting drift and acceptance criterion.

Every file under `docs/` is listed below, with when to read it. Paths are relative to `docs/`. Keep this map current when a file is added, moved or removed.

**Which doc wins.** The authority order is in `CLAUDE.md` at the repository root.

## base/

- `base/specifications.md` — the top-level specification: purpose, requirements, acceptance criteria and the four-field answer. Read it before changing behavior, the API or the models. Q11 lists the decisions still open. Its §5 explains how this design meets the pod contract in `contract/`.
- `base/phase4.md` — the Phase 4 build plan: the alignment check against Team 16's package, the roadmap v1, v1.1 and v1.2 with owners and decisions D1 to D12, the contract test map, and the design questions Q1 to Q8 (decided, kept for their reasoning). A plan, not a source of truth: where it disagrees with the spec or the contract, they win.
- `base/structure.md` — the structural model's format: the generator's input, node and edge kinds, the id scheme and an example. Read it before changing the structural generator. The spec wins where they disagree.
- `base/behavioral.md` — the behavioral model's format, frozen as `generate_behavioral` writes it: state and transition kinds, the id scheme, the mining rules, what the miner leaves out, and an example. Read it before changing the behavioral generator. The spec wins where they disagree.
- `base/student-facing-spec.docx.pdf` — the course's cross-team testing rules. Read it when writing or changing tests or the tester.
- `base/overview_phase4.html` — a visual tour of the architecture as Phase 4 built it. Read it for orientation; the spec wins where they disagree.

## contract/

The pod contract with Team 16. Both teams' registry rows link it. It follows Team 16's v1.1 package with two deviations in behavior: no prose detector is required (Team 15's `issues` is always `[]`), and Team 15 adds the optional `drift`, `drift_error` and `POST /generate`. Each system lists its features in `/health`, and a tester skips, never fails, a test whose feature the target lacks. `contract/pod-contract.md` §9 lists every difference, and §10 says how it changes.

- `contract/spec-v1.1.md` — Team 16's v1.1 specification (their `SPEC.md`), copied unchanged: the prose detector, comparison rules and acceptance criteria the contract cites as "v1.1 SPEC". Its `openapi-system-v1.1.yaml` means `contract/pod-contract.openapi.yml`; the contract wins where they differ.
- `contract/pod-contract.openapi.yml` — the system API both testers call: shared routes and JSON, plus Team 15's optional additions. Read it before changing a route, a field or an error code.
- `contract/pod-contract.md` — the testing rules: sessions, fixtures, the test list T-01 to T-33 with the components and criteria each covers, the acceptance criteria, which tests skip and why, limits, retries, errors and how the contract changes. Read it when writing or changing tests or the tester.
- `contract/pod-tester.openapi.yml` — the tester API and suite report, as the course fixes them. Read it before changing the tester's routes or report.
- `contract/mapping-v1.1.yaml` — Team 16's shared classification rules, skip allowlist and code-to-doc mappings, copied unchanged. The system loads it at runtime.
- `contract/golden-outputs.json` — Team 16's expected answers for the 10 cases on their fixture repository, copied unchanged. Testers compare against it for T-01 to T-21.
- `contract/model-golden-outputs.json` — the expected answers for the drift tests T-24 to T-33, one entry per case on `kaan-kanadasi/doc-tracker-model-fixtures`. `contract/pod-contract.md` §3 describes its layout and the checklist for changing it.

## diagrams/

Diagrams of the planned system. Each is a Markdown file whose Mermaid block is the source; GitHub draws it, and `python diagrams/render.py` renders a PNG on demand (not committed). `agents/modeling.md` has the rules for modeling and drawing.

- `diagrams/render.py` — renders a diagram's Mermaid block to a PNG. Run it to see a diagram outside GitHub.
- `diagrams/who-talks-to-what.md` — the developer, GitHub and a tester reach one drifter core (orchestrator, GitHub integration, three generators, comparison) through the CLI, the GitHub Action (Phase 5) and the hosted service, which serves the pod contract's routes and adds change detection and a result store; the repository is only read. Read it first to understand the system.
- `diagrams/behavioral-model.md` — lifecycle of a repository under the tool: init proposes the models, a person commits them, and each push ends Aligned, Drifted or Failed. Only structural and behavioral are regenerated; ownership is checked against its rules (spec §3.2).
- `diagrams/init.md` — `drifter init` step by step: the overwrite guard, structural and behavioral from the code with the default scope, ownership proposed from history, the four files written, then a person commits the baseline. Read it before changing `generate_models` or the init command.
- `diagrams/one-check.md` — one check step by step, from request to four-field answer, with the HTTP error or no-verdict code each step can return, the 80 s deadline per check, and what the hosted service adds. Read it when working on the orchestrator or errors.
- `diagrams/models-folder.md` — the four files in `/models` and what each holds. Structural follows `base/structure.md` (imports and inherits edges, no calls); behavioral follows `base/behavioral.md` (states and transitions); init proposes one exact-path ownership rule per file.
- `diagrams/model-seam.md` — the seam between the core and the three model owners: who writes which file, the element rule every structural and behavioral model follows, what the core does with each model in one check, how ownership is proposed and checked, and when an owner's model is ready to plug in. Read it before writing or changing a generator.
- `diagrams/file-fetch.md` — how one check gets the repository's files: a fresh clone without file contents, batched downloads instead of one per file (two today: `/models`, then the in-scope files), reading with lazy fetching off so a failed download stops the check at once; with the measured times that decided it and what it leaves out. Read it before changing how the GitHub integration reads files.
- `diagrams/comparison.md` — how differences are decided: set difference by id for structural and behavioral (ADDED, REMOVED, MODIFIED), a rule check per commit for ownership (VIOLATION).
- `diagrams/four-field-answer.md` — test T-26: the four-field answer as the `drift` key of `POST /system/analyze`, how a tester compares it with `contract/model-golden-outputs.json`, and when the test passes, fails or is skipped. A test is skipped when the target's `/health` does not list `model_drift`, and is `error` when `/health` gives no 200 within 90 s.
- `diagrams/cross-team-test.md` — one cross-team test session as `contract/pod-contract.md` defines it: tester and system routes, the T-01 to T-33 loop over both fixtures, and the report. The tester reads `/health` once first and skips each test whose feature the target does not list. It also shows the one-session 409 and the stop at 570 s of the 600 s run.
- `diagrams/research-evidence.md` — Team 15's tool research, as a table: what runs at runtime, what only serves tests, what is rejected. Team 15's choices, not the pod contract.

## adr/

Architecture decision records: why a hard-to-reverse choice was made. Read them before reversing one. The folder stays here because `contract/mapping-v1.1.yaml` classifies `docs/adr/**` as DESIGN.

- `adr/0001-one-acceptance-criteria-list.md` — why AC-01 to AC-10 always carry the pod's meaning. Read it before renumbering or redefining an acceptance criterion.

## agents/

How agents work in this repository. `CLAUDE.md` at the repository root points here.

- `agents/modeling.md` — the rules for designing a model format and drawing a diagram. Read it before either.
- `agents/domain.md` — where the glossary and the ADRs are and how to use them. Read it before exploring the codebase.
- `agents/issue-tracker.md` — how issues are created and read with the `gh` CLI. Read it before touching an issue.
- `agents/triage-labels.md` — the five triage labels and what each means. Read it before labelling an issue.

## state/

Where the work stands.

- `state/WORK-ITEMS.md` — the one queue: every Phase 5 item (W0 to W5, N1 to N6) with its tier, what it depends on, what it touches and when it is done. Read it before starting work, and trust it over memory. A plan: the spec and the contract win over it.
- `state/tracker-gaps.md` — open work: what the wired drift check still owes, and what one check still needs to become a tracker that watches a repository on its own. Each row has a fix and a check that closes it. `base/phase4.md` owns the schedule; this file owns the detail.

## decisions/

Calls that are not an agent's to make.

- `decisions/OPEN-DECISIONS.md` — the index of decisions awaiting the human. Read it before choosing between options; if the question has a row, stop and cite it instead of guessing.
- `decisions/contract-contradictions.md` — each place where the contract, the spec, the diagrams, the course PDF or Team 16's v1.1 package disagree, with a fix, a check that closes it, and an owner. A ticket whose check passes moves to the file's closed table.

## templates/

Blank forms. Copy one into place and fill only the copy.

- `templates/README.md` — which template to copy where, who fills it, and the check that a copy is filled. Read it before starting an Epic or a design doc.
- `templates/EPIC.md` — the form for an Epic: what must change. Goal, Relies on, Steps, Done criteria, Open questions, Review.
- `templates/DESIGN.md` — the form for a design doc: the intended structure, the premises and how each was verified, and what must stay true.
- `templates/RULED.md` — the form for a ruling, word for word, with the readings it forecloses. Only the human fills it.

## epics/

Live Epics, one folder each. Finished ones move to `closed/`, which does not exist until the first Epic closes; never build from one.

- `epics/README.md` — how an Epic is named, how it and its W-row name each other, its branch, its lifecycle from draft to closed, and when a change needs no Epic. Read it before drafting, reviewing, building or closing an Epic.
- `epics/E00-docs-move/EPIC.md` — the example Epic: the docs move of W2-5 (step 0.2a), written after the fact. Read it to see a filled template.

## proposals/

Phase 5 proposals. Not agreed and not built: nothing here changes the code, the contract or the spec until the team accepts it. Read one when its work item starts.

- `proposals/docker/docker.md` — a `.dockerignore`, a Dockerfile ordered for layer caching, and when to split the containers (W1-2, W1-3, W3-6).
- `proposals/init/init.md` — which `/models` files a person may edit after `drifter init`, the self-grant hole, and `drifter validate` (W0-6, W0-7, W3-8).
- `proposals/ownership/owner-approval.md` — whether an edit by a non-owner is still a violation when an owner approved it (W0-7, W4-7).
- `proposals/language-engine/README.md` — the multi-language engine in short, and the order to read the folder in (W5-1 to W5-3). Start here.
- `proposals/language-engine/01-what-changes.md` — which parts of one check change for more languages, and which stay.
- `proposals/language-engine/02-language-adapters.md` — per-language adapters. Superseded in part by 04.
- `proposals/language-engine/03-language-mapping.md` — what each language becomes in `structural.json`.
- `proposals/language-engine/04-one-template.md` — the design: one engine, and one table row plus one query file per language.
- `proposals/language-engine/05-decisions-log.md` — the decisions D1 to D11 (D6 is still open), the open questions O1 to O5 and what was only suggested.
- `proposals/language-engine/06-init.md` — how `drifter init` changes beyond Python.
- `proposals/language-engine/final_templates.md` — the end state after steps a to d, and its seams.
- `proposals/language-engine/research-multi-language.md` — the options for reading more languages, measured.
- `proposals/language-engine/research-template-engine.md` — how to build the engine, ranked by CPU time, memory and effort.
- `proposals/language-engine/guide.html` — a visual guide to the folder.

## research/

Background: outside evidence and reviews. Read it for the reasoning behind a work item; never build from it. `state/WORK-ITEMS.md` replaces the to-do lists inside these files.

- `research/mage-engineering-env.md` — lecture notes on how MAGE sets up an engineering environment for agents.
- `research/mage-research.md` — the source map behind those notes.
- `research/mage_take.md` — a review of this project against MAGE.
- `research/mage-alignment.html` — a visual explainer of MAGE's alignment checks.
- `research/industry-architecture-research.md` — how other drift tools are built, and what that means here.
- `research/architecture-review.html` — a review of the model and drifter code, findings A to F (the Wave 3 refactors).

## history/

- `history/phase2-changes.md` — history, not instructions: what changed from Phase 2 and v1. Read it only for course reports; never build from it.
- `history/deviations-review-2026-11-05.md` — the review of the former `docs/deviations/` folder, document by document: verdicts, repeats and contradictions. It was the queue's appendix; read it for why an item in `state/WORK-ITEMS.md` exists.
- `history/contract-2.4.0-changes.md` — what changed from contract 2.3.0 to 2.4.0, what it means for each team's system and tester, and the matching spec changes. Send it to Team 16 with the contract; the contract wins where they differ.

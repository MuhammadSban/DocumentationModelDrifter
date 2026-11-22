# CLAUDE.md

Model-drift tool: keeps a repository's architecture models (`/models`) in step with its code. `docs/README.md` maps every doc; read it before changing behavior, the API, the models or the tests.

## Authority order

When two docs disagree, the higher one wins, and the lower one is fixed in the same change. A level that does not exist yet is skipped.

1. The course PDF, `docs/base/student-facing-spec.docx.pdf`.
2. The pod contract, `docs/contract/`, for anything another team's tester or system sees (routes, JSON, tests).
3. The human's rulings, `docs/decisions/RULED/`.
4. The invariants, `docs/invariants/INVARIANTS.md`.
5. The spec, `docs/base/specifications.md`.
6. The models in `docs/diagrams/`: `dependency.md`, `data-flow.md`, `behavior.md`, `models-folder.md` and `model-seam.md`. Every other diagram ranks at level 8.
7. The current Epic, under `docs/epics/`.
8. Everything else.

## Principles

Each numbered rule names the principle it serves.

- **Own abstractions.** Go through the project's own abstractions.
- **Done is checked.** Done is a claim checked against the disk, not the report.
- **The human's call.** When a call is the human's, stop.

## Start of session

- Read **Next action** and **Do not yet** in `docs/state/WORK-ITEMS.md` first, once they exist; until then read the whole file.
- Open `docs/decisions/RULED/` files with the Read tool.
- `docs/closed/` is history: read it only when the task asks for it.

## Rules

A rule gets a number only if all three hold: an agent working elsewhere could break it, it cannot be read from the file being edited, and it crosses files. Each row is rule · principle · check. A rule with no check says "guidance only", plus the build-order step that adds its check when one is planned. Numbers are never reused.

| Rule | What it says | Principle | Check |
|---|---|---|---|
| R1 | A call that is the human's goes to `docs/decisions/OPEN-DECISIONS.md`: stop and cite its row. Only the human writes `docs/decisions/RULED/`; cite a ruling by its id and follow it. | the human's call | guidance only |
| R2 | A change that makes a line of `docs/base/specifications.md` or `docs/base/structure.md` untrue updates that line in the same PR. | done is checked | guidance only |
| R3 | Nothing deploys red: a commit reaches the live server only after CI is green on it. A red PR can still be merged, so fix it before the next deploy. | done is checked | Railway waits for CI and skips a red commit (step 0.5) |
| R4 | A protected change goes through the permission prompt. Never route around a deny or ask rule (`python -c`, a script). | own abstractions | guidance only; the human's PR review |
| R5 | Imports follow the module map `docs/diagrams/dependency.md`, which `.importlinter` states as contracts. They point down through its four layers: entry points, services, core, generators. `drifter` and `models` import none of `GitHub_Connector`, `Frontend` and `Tester`. `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`. `Frontend` imports none of `GitHub_Connector`, `Tester` and `drifter.check`. | own abstractions | `lint-imports` in CI (`.github/workflows/ci.yml`) |
| R6 | A change to a part, a flow or a run state updates its model in `docs/diagrams/` in the same PR. | done is checked | guidance only; the human's PR review |
| R7 | Pick the lane before the first edit. A small change, as `docs/epics/README.md` defines it, is committed to a branch and pushed, and CI runs on the push; once CI is green it goes to `main` on the human's word, with no PR. Anything else is Epic work on a branch `E<nn>-slug`, with no PR while it is built and CI on each push, and follows that file's lifecycle: code starts after RATIFY, only from a live Epic; each commit carries its `Step:` line; one PR is opened when the last step is committed, before the audit, and the Epic merges through it; the Epic closes after the auditor re-runs Done and the human accepts. Any change gets a PR when another person's approval or review is needed. | done is checked | `.claude/hooks/step-trailer.py` blocks an agent commit without the `Step:` line; the rest is guidance only |

## Commands

Both ran on a clean clone in a fresh virtualenv (Python 3.13, Windows).

- **The CLI:** `pip install -e .` installs the `drifter` command: the core and the generators, without the web service.
- **The service:** `pip install -r requirements.txt`, then the Dockerfile's line, `uvicorn --app-dir Source GitHub_Connector.api:app --host 0.0.0.0 --port 8000`. `GET /system/health` answers 200.
- **The lint CI runs:** after the service's install, `pip install -r requirements-dev.txt`, then `ruff check` and `PYTHONPATH=Source lint-imports`.

## House rules

Unnumbered.

- **Comments.** Keep them brief, in the format `verb ___, brief explanation`.
- **Simplest solution first.** Always pursue the minimal solution; there is beauty in simplicity. Then flag to the user what's missing from a "complete solution". Don't implement it: that must be a conscious decision by the user.
- **Think before coding.** State your assumptions before implementing. If a request has more than one reasonable reading, list them and ask; don't pick one silently. If something is unclear, stop and say what's confusing. Push back when a simpler approach exists.
- **Surgical changes.** Touch only what the task needs. Don't reformat, refactor, or "improve" nearby code, and match the existing style. If you notice unrelated dead code, mention it instead of deleting it. Do remove imports or functions that your own change made unused. Every changed line should trace back to the request.
- **Modeling.** Before designing a model format or drawing a diagram, read `docs/agents/modeling.md`.
- **Verifiable goals.** Turn each task into a check you can run: for a bug, write a failing test that reproduces it, then make it pass. For multi-step work, give a short plan with a verify step for each item, and don't call it done until the checks pass.

### Agent skills

- **Issue tracker.** Specs and tickets live in this repo: a spec is an Epic under `docs/epics/`, a ticket is one Step in it, and `docs/state/WORK-ITEMS.md` is the queue. GitHub Issues are optional. See `docs/agents/issue-tracker.md`.
- **Triage labels.** The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.
- **Domain docs.** Single-context: `GLOSSARY.md` is the glossary, `docs/adr/` holds the ADRs. See `docs/agents/domain.md`.

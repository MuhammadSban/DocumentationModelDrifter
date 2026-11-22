# History, not instructions

What changed from the Phase 2 specification and v1 to the model-drift specification.

Written 2026-10-30. The current specification is docs/base/specifications.md.

This file records what earlier versions did and why they changed. It is kept for course reports
(for example "comparison with the Phase 2 plan"). Nothing named here is to be built: features,
routes, tests and repositories listed below are dropped or replaced unless
docs/base/specifications.md says otherwise.

Versions referred to:

| Version | What it is |
| --- | --- |
| Phase 2 | The pod's specification of Teams 15 and 16, agreed 2026-09-23 (Version 1). |
| v1.1 | Phase 3 change detection over POST /system/analyze, deployed on Railway. |
| v1.2 | Phase 3 LLM drift check (Google Gemini) that filled issues[]. |
| Model drift | docs/base/specifications.md, written 2026-10-30. |

## 1. What changed

- **Kept:** Purpose (keep AI model technical documentation current under EU AI Act Art. 53(1)(a)
  and Annex XI), users, read-only analysis, never running repository code, people making the
  decisions, Git and GitHub Actions as reused parts, no GenAI in the running system (Phase 2,
  8.2), and the reliability targets of at least 90% of drift caught and under 10% false alerts,
  now measured with planted changes.
- **Changed:** What "documentation" means. The tool mines three models of the repository
  (structural, behavioral, ownership), stored as JSON in /models. These are the repository's
  machine-readable design documentation. On every push it checks that the code still matches
  them. Prose docs are no longer analysed (still an open decision).
- **Changed:** Output. Findings per doc file marked PENDING_REVIEW are replaced by a verdict: true
  or false, with the exact differences per model.
- **Changed:** Human review. Confirm or dismiss per finding is replaced by: a person accepts drift
  by committing updated /models, reviewed like any change. Git records who and when.
- **Changed:** Where the check runs. One codebase runs everywhere: on a developer's machine,
  inside the GitHub Action on its own checkout, and in the hosted service for course testing. v1
  planned the Action as a thin client of the hosted service.
- **Changed:** The pod contract and the tester. Both teams switch to model drift and build to one
  new contract. The course still fixes the testing routes; the project API, setup data, test list
  and coverage lists all change.
- **Changed:** The labelled test repositories. They are still needed, because they hold the
  tester's expected answers, but they are relabelled with an expected verdict per model.
- **Dropped:** The code-to-doc mapping file, section-level mapping, the confidence rating,
  per-user accounts and login, the job queue, notifications, the LLM drift check that v1.2 added
  (Google Gemini), POST /system/analyze, and the v1 shared tests T-01 to T-23.

Why: the LLM check of v1.2 gave findings that varied between runs, its accuracy was never measured,
it allowed about 20 checks a day and sent code to Google. The Phase 3 report marked REQ-02 partial,
with AC-02 and AC-03 not demonstrated. Mining models deterministically makes every criterion
checkable again.

## 2. Section by section

### Numbering

The specification keeps the Phase 2 section numbering (Q1 to Q10) and the requirement and
acceptance IDs (REQ-01 to REQ-07, AC-01 to AC-10). AC-11 (ownership violations) is new. Q11 (open
decisions) is new.

### 1.2 Selection rationale

The pod chose Documentation Tracker in Phase 1 over the Release Evidence Register, the Oversight
and Traceability Ledger and Credit Review.

### 1.3 Pod agreement

Teams 15 and 16 agreed on Version 1 of the specification on 2026-09-23.

### 2.2 Operating limits

The limits (120 s per check, 60 s per git call, 2 checks at once, the 1 MB, binary and UTF-8
skips, ignored hidden paths, symlinks and submodules) carry over from v1.

### 2.3 Cost and feasibility estimate (removed from the specification)

Phase 2 estimated about 150 hours per team. Team 15: 40 design and specification, 15
implementation, 15 integration, 20 validation and testing, 25 deployment and operations, 35
documentation and coordination. Team 16: 30, 35, 25, 25, 15 and 20 in the same order. These
predate the model-drift approach; each piece is re-estimated by its owner at Phase 4 planning.
The GitHub integration, error handling, course endpoints and hosting carry over from v1.

### REQ-07 and AC-10

Phase 2 asked for "very similar outputs" and confidence values within about 0.05 across runs.
Both are replaced by byte-identical results; there is no confidence field.

### 3.3 Model explanation

Phase 2's M3 suppressed a warning whenever code and documentation changed in the same diff, even
if they disagreed (a co-change heuristic). The model-drift check compares facts instead.

### 4.2 Test data

The v1 fixture repositories, Team 16's ParthGupta06/doc-tracker-fixtures and Team 15's
kaan-kanadasi/DocumentationDrifter-testrepo, are labelled for change detection and doc findings.
They are not used as they are; the pod relabels them or builds a new fixture.

### 5.1 and 5.2 Interface

The course endpoints /system/test/setup and /system/test/report are unchanged from v1. The
request shape (repository, commit_id, optional base_commit) is unchanged from Phase 2 and v1.
ANALYSIS_NOT_FOUND is v1's code. POST /system/generate and POST /system/compare replace
POST /system/analyze.

### 5.3 Testing contract

The v1 pod tester's tests T-01 to T-23 checked changed files, categories and doc findings; all of
them are replaced. T-18 to T-23 had waited for the Phase 4 doc mapping. Code coverage since setup
works as in v1.

### 6.1 Phase 3 (done, removed from the specification)

Delivered: change detection over the shared API (v1.1), an LLM drift check (v1.2), the course
endpoints and the cross-team tester, deployed on Railway. The LLM check is retired. The GitHub
integration, error handling, course endpoints, tester frame and hosting carry over.

### 7.2 Design decisions

Phase 2 chose "a living map between documentation and code" so that attributing changes would be
"almost deterministic", and said "we don't want our tool to be just a wrapper on an LLM". The
model-drift approach keeps that aim and makes the check fully deterministic. Phase 2 made human
review mandatory in REQ-03 but selectable in its section 7.2; now review is mandatory and only the
enforcement strength (warn-only or required check) is selectable.

### 7.3 Operation and observability

Phase 2 planned per-user accounts, login, loading repositories on demand, a job queue and crash
tracking. None of it was built and none is needed. Phase 2's "user rejects" metric became two
measures: how often drift is accepted rather than fixed, and the false-alert rate on labelled
no-drift commits.

### 7.4 Validation strategy

Phase 2's plan to prototype with an LLM wrapper is dropped.

### 8.1 Build, buy and reuse

Git and GitHub Actions are kept from Phase 2. Model mining replaces Phase 2's rule-based detector.
The GitHub integration is v1's code. Phase 2 kept GitHub Actions for running acceptance tests; the
Action is now the main trigger.

### 8.2 GenAI use

The no-GenAI-at-runtime rule restores the Phase 2 decision that v1.2 overrode.

### 9.1 Risks

The planted-change experiment and its targets (90 of 100 caught, under 10 of 100 false alerts)
come from Phase 2's Priority 1. Phase 2's Priority 2, an AI model at runtime inventing or missing
mismatches, is closed because no model runs at runtime.

## 3. Phase 2 inconsistencies and how they were resolved

The Phase 2 document ended with twelve review notes on its own contradictions. Their resolution:

1. Detection semantics (fact comparison vs. co-change heuristic). Resolved: the facts in the code
   are compared with the facts in the models; there is no co-change rule.
2. Human review mandatory vs. selectable. Resolved: review is mandatory; only enforcement
   strength is selectable.
3. Read-only scope vs. documentation editing. Resolved: the tool never writes; the developer
   commits /models.
4. HTTP errors. Resolved in v1 and kept: 400, 404 or 500 with {code, message}, and nothing saved
   on failure. The 422 codes are new and follow the same body.
5. JSON examples. Resolved: examples use owner/name and 7 to 40 hex commit ids.
6. Confidence and repeatability. Resolved: no confidence field; results are byte-identical.
7. Mapping prerequisites. Resolved: there is no mapping file; /models is required and init
   creates it.
8. Schedule for the reliability measure. Resolved: the planted-change experiment is the first
   Phase 4 task.
9. Stateless test interface vs. per-user storage. Resolved: there is no per-user storage.
10. Review decisions in GitHub replies. Resolved: the decision is the /models commit, readable
    from git and named in each verdict.
11. Viewers, notifications and mobile features. Dropped.
12. "Human review ensures compliance." Reworded: the tool supports documentation maintenance and
    certifies nothing.

The Phase 2 note "Maybe use Laya the open source in this project" was dropped; it was unclear what
Laya referred to.

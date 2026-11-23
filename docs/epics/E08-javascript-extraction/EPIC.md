# E08: Python and JavaScript extraction

Status: ratified · Owner: Codex

W-row: W5-3-JS in docs/state/WORK-ITEMS.md · Branch: E08-javascript-extraction

## Goal

Apply the user's previously requested Python behavioral improvements and standalone JavaScript support to the real clone at origin/main 0829935. The user explicitly authorized the narrow Python/JavaScript implementation and asked that it feed the existing three models. This is local implementation for review, not the broader language-engine rollout or permission to publish. Preserve the team's node budgets, volatility parameter, locked dependencies and E07 authored-model checks.

## Relies on

- Models: docs/diagrams/dependency.md, model-seam.md, models-folder.md and data-flow.md (changes parsing and new-repository scope descriptions).
- Rulings: none; RULED contains its README only. No ownership self-grant or broader engine decision is chosen.
- Invariants: INV-1, INV-2 and INV-3 (reads; no changes).

## Steps

### Step 1/3: Integrate language extraction

- Files: Source/models/javascript_model.py, common.py, structural_model.py, behavioral_model.py; tests/languages/test_javascript.py, tests/behavioral/test_behavioral_cases.py; pyproject.toml, requirements.in, requirements.txt.
- Check: python -m pytest tests/languages tests/structural tests/behavioral tests/common -q -> all pass.
- Trailer: Step: 1/3

### Step 2/3: Connect analysis and scoped generation

- Files: Source/drifter/check.py, Source/GitHub_Connector/analysis.py, Source/GitHub_Connector/api.py, Source/Frontend/model_drift.py, Source/Frontend/model_viewer.py, tests/connector/test_javascript_analysis.py.
- Check: python -m pytest tests/connector/test_javascript_analysis.py -k "direct_core or cli_round or default_scope" -q -> six focused core/CLI checks pass. Full HTTP-route coverage remains required by Done criterion 5.
- Trailer: Step: 2/3

### Step 3/3: Document and verify the integration

- Files: docs/base/specifications.md, structure.md, behavioral.md; docs/diagrams/dependency.md, model-seam.md, models-folder.md, data-flow.md; docs/README.md, docs/state/WORK-ITEMS.md; focused regression additions in tests/languages/test_javascript.py and tests/connector/test_javascript_analysis.py.
- Check: python -m pytest tests/behavioral tests/common tests/structural tests/languages tests/drifter tests/frontend/test_behavioral_view.py tests/hooks tests/docs tests/image tests/ownership -q -> all locally runnable cases pass. Full integration remains required by Done criterion 5.
- Trailer: Step: 3/3

## Done criteria

Execution note: this Windows tool session cannot initialize the asyncio loopback socketpair or run the MSYS shell used by mock Git clones. Node and computer-use fallback transports disconnected. Local step checks therefore cover the available source, CLI, core and rendering tests; full HTTP/Git-clone integration and installation of the upstream dependency lock remain pending in CI. Cached parser versions match the declared pins. These execution limits do not waive Done criterion 5 or close the Epic.

1. CI: gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion -> success. Pending until a separately authorized push; this local delivery does not close the Epic.
2. Specification: git diff --stat origin/main...HEAD -- docs/base/specifications.md -> includes supported-language and default-scope changes.
3. Decisions: git grep -n E08 -- docs/decisions/OPEN-DECISIONS.md -> no matches.
4. The human accepts; pending their review.
5. Regression: python -m pytest -q -> all local tests pass.
6. Lint: python -m ruff check -> all checks pass.
7. Imports: lint-imports --no-cache with PYTHONPATH=Source -> all five contracts kept.
8. Compilation: python -m compileall -q Source -> no errors.

## Open questions

- Shared representation? Settled: lower JavaScript into the AST subset both existing generators consume; never compile or execute it. Preserve Python parsing and IDs; JavaScript IDs retain ./ plus paths/extensions. This fits the existing unconstrained string IDs and element kinds (DESIGN.md:7; Source/models/common.py:24; Source/models/structural_model.py:131; Source/models/structural.schema.json; docs/diagrams/model-seam.md, element rule).
- Which scope? Settled: preserve explicit committed selections, including empty and Python-only; use the mixed-language default only for absent scope with non-vendored JavaScript. Reject invalid scope rather than widen it, updating the viewer's current fallback accordingly (DESIGN.md:9; Source/drifter/check.py:226 and :473; Source/Frontend/model_drift.py, _scope; docs/diagrams/model-seam.md:38, planned update in Step 3).
- Behavioral authorization? Settled by the user's narrow request: Python improvements and JavaScript feeding existing models. Reuse string-state mining, normalize this to self and keep unknown effects as barriers; N2 and broad O4 remain open without selecting a replacement model (docs/state/WORK-ITEMS.md:5; Source/models/behavioral_model.py:17 and :108; docs/decisions/OPEN-DECISIONS.md, N2 and O4).
- Team changes? Settled: integrate against 0829935 while preserving budgets, volatility, E07 checks and dependency hashes. Keep the existing preview slot and deadline implementation (Source/models/structural_model.py:40; Source/drifter/check.py:133; Source/GitHub_Connector/api.py:171; requirements.in:1; requirements-dev.in:3; DESIGN.md:9).
- Imports? Settled for this implementation: relative in-scope ES imports and literal require, with direct named/default export aliases; omit unresolved or ambiguous targets and do not infer package aliases or transitive re-export inheritance (DESIGN.md:7; docs/state/WORK-ITEMS.md:5).

## Review

RATIFY — design-reviewer at a33883f — 2026-11-23

- The filled-copy checks print nothing for both planning files; each step names its files, check and trailer, and Done criteria give commands and expected outcomes with CI and human acceptance explicitly pending (docs/templates/README.md; EPIC.md, Steps and Done criteria).
- Repository premises hold: both generators consume parse_files, hosted paths delegate to the core, existing schemas permit the proposed IDs/kinds, and the dependency lock comes from requirements.in (Source/models/structural_model.py:81; Source/models/behavioral_model.py:20; Source/GitHub_Connector/analysis.py, generate and _drift; Source/models/structural.schema.json; Source/models/behavioral.schema.json; requirements.in:1).
- The revised plan includes the parser node and premise in data-flow.md, resolving the original omission; existing module boundaries and the three-model seam remain the implementation constraints (DESIGN.md:11; docs/diagrams/data-flow.md:33 and :121; docs/diagrams/dependency.md; docs/invariants/INVARIANTS.md, INV-1 to INV-3).
- The recorded user authorization covers this limited Python/JavaScript integration. Ownership self-grant and broad language-engine choices remain outside it; no question needs a new decision row. This verdict authorizes local implementation only and does not claim implementation checks or remote CI have passed (docs/state/WORK-ITEMS.md:5; EPIC.md, Goal and Done criteria; docs/decisions/OPEN-DECISIONS.md, W0-7, N2 and O4).

# E08: Python and JavaScript extraction

Status: draft · Owner: Codex

W-row: W5-3-JS in docs/state/WORK-ITEMS.md · Branch: E08-javascript-extraction

## Goal

Apply the user's previously requested Python behavioral improvements and standalone JavaScript support to the real clone at origin/main 0829935. The user explicitly authorized the narrow Python/JavaScript implementation and asked that it feed the existing three models. This is local implementation for review, not the broader language-engine rollout or permission to publish. Preserve the team's node budgets, volatility parameter, locked dependencies and E07 authored-model checks.

## Relies on

- Models: docs/diagrams/dependency.md, model-seam.md and models-folder.md (changes parsing and new-repository scope descriptions); data-flow.md (reads only).
- Rulings: none; RULED contains its README only. No ownership self-grant or broader engine decision is chosen.
- Invariants: INV-1, INV-2 and INV-3 (reads; no changes).

## Steps

### Step 1/3: Integrate language extraction

- Files: Source/models/javascript_model.py, common.py, structural_model.py, behavioral_model.py; tests/languages/test_javascript.py, tests/behavioral/test_behavioral_cases.py; pyproject.toml, requirements.in, requirements.txt.
- Check: python -m pytest tests/languages tests/structural tests/behavioral tests/common -q -> all pass.
- Trailer: Step: 1/3

### Step 2/3: Connect analysis and scoped generation

- Files: Source/drifter/check.py, Source/GitHub_Connector/analysis.py, Source/GitHub_Connector/api.py, Source/Frontend/model_drift.py, Source/Frontend/model_viewer.py, tests/connector/test_javascript_analysis.py.
- Check: python -m pytest tests/connector/test_javascript_analysis.py tests/drifter tests/frontend -q -> all pass.
- Trailer: Step: 2/3

### Step 3/3: Document and verify the integration

- Files: docs/base/specifications.md, structure.md, behavioral.md; docs/diagrams/dependency.md, model-seam.md, models-folder.md; docs/README.md, docs/state/WORK-ITEMS.md; focused regression additions in tests/languages/test_javascript.py and tests/connector/test_javascript_analysis.py.
- Check: python -m pytest -q -> all local tests pass.
- Trailer: Step: 3/3

## Done criteria

1. CI: gh run list --commit HEAD --limit 1 --json conclusion -> success. Pending until a separately authorized push; this local delivery does not close the Epic.
2. Specification: git diff --stat origin/main...HEAD -- docs/base/specifications.md -> includes supported-language and default-scope changes.
3. Decisions: git grep -n E08 -- docs/decisions/OPEN-DECISIONS.md -> no matches.
4. The human accepts; pending their review.
5. Regression: python -m pytest -q -> all local tests pass.
6. Lint: python -m ruff check -> all checks pass.
7. Imports: lint-imports --no-cache with PYTHONPATH=Source -> all five contracts kept.
8. Compilation: python -m compileall -q Source -> no errors.

## Open questions

- Shared representation? Lower parsed JavaScript into the AST subset both existing generators already consume, never compile or execute it. Keep Python parsing and IDs unchanged; JavaScript IDs start with ./ and retain paths/extensions (common.parse_files, structural.module_id).
- Which scope? Existing committed scope remains authoritative, including empty or Python-only selections. Only an absent scope selects Python plus standalone .js/.mjs/.cjs/.jsx when non-vendored JavaScript exists. Invalid scope must fail rather than widen (check.in_scope, _scope_rule and Frontend.model_drift._scope).
- Behavioral authorization? The user requested Python improvements, then JavaScript extraction feeding all three models. Reuse the existing narrow string-state rules, normalize this to self, and retain unsupported effects as barriers. N2 and broad language-engine O4 remain open; no replacement model is introduced (user instructions; behavioral_model.generate_behavioral).
- Team changes? Apply diffs against 0829935, preserve structural BUDGETS and core volatility settings, E07 behavioral model drift checks, and dependency hashes. The preview deadline has already been fixed upstream and needs no duplicate change (structural_model.BUDGETS; check.PARAMETERS; api.models_view; requirements.in).
- Imports? Relative in-scope ES imports and literal require only; direct named/default export aliases. No package aliases, ambiguous resolution or transitive re-export inheritance (DESIGN.md).

## Review

Pending fresh review against this clone.

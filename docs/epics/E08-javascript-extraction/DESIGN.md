# JavaScript extraction on the current team code

Epic: docs/epics/E08-javascript-extraction/EPIC.md

## Intended structure

Add one runtime module, models.javascript_model, using tree-sitter 0.25.2 and tree-sitter-javascript 0.25.0. common.parse_files validates sources in path order and lowers JavaScript into the internal Python AST subset already read by structural and behavioral generators. Never compile or execute analyzed JavaScript. Preserve all Python IDs; JavaScript IDs are ./ followed by the repository path and extension, disjoint from slash-free Python module IDs. Index direct exports before resolving relative imports and literal CommonJS bindings. Unknown effects remain barriers, and unresolved import targets are omitted rather than guessed.

analysis.py continues delegating to drifter.check. The shared new-repository default includes JavaScript only where non-vendored JavaScript exists; committed scope remains authoritative. The viewer uses the same fallback and labels JavaScript paths correctly. Preserve upstream volatility and verbosity/node-budget behavior and E07's authored-model checks. Ownership continues using Git history without a language-specific parser. The two pinned parsers are added to requirements.in, its existing hash-locked requirements.txt and pyproject.toml; retain every other locked dependency.

Update data-flow.md's parser node and premise to describe Python ast.parse plus Tree-sitter JavaScript lowering. The data-flow topology remains the same shared parser feeding the existing generators.

## Premises, verified

| Premise | How verified | Holds? |
|---|---|---|
| The clone is clean and updated to origin/main 0829935. | git status --porcelain; git log -1 --oneline origin/main | yes |
| Both source generators consume common.parse_files AST modules. | Source/models/structural_model.py and behavioral_model.py | yes |
| Hosted generation and analysis use the shared core. | Source/GitHub_Connector/analysis.py generate and _drift | yes |
| Existing kinds/IDs fit the schemas without a contract change. | Source/models/structural.schema.json and behavioral.schema.json | yes |
| Dependency locking is generated from requirements.in. | requirements.in header; requirements-dev.in constraint | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| INV-1 | Python golden outputs and deterministic model ordering stay unchanged. | python -m pytest tests/connector/test_model_golden.py tests/structural tests/behavioral -q |
| INV-2 | Committed scope and ownership stay authoritative; no self-grant policy change. | python -m pytest tests/connector/test_javascript_analysis.py tests/drifter -q |
| INV-3 | Core and generators import no caller package. | PYTHONPATH=Source lint-imports --no-cache |

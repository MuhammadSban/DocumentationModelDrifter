# The module map

Epic: `docs/epics/E01-module-map/EPIC.md`

## Intended structure

The model is `docs/diagrams/who-talks-to-what.md`, renamed `docs/diagrams/dependency.md` by step 1. Its diagram and its question (who reaches the core, through which entry point) stay as they are. Step 2 adds the module map below it, as tables: `tests/docs/test_diagrams.py:20` allows one Mermaid block per file, and a grid of facts is a table (`docs/agents/modeling.md`).

The map is the target. Where today's code breaks it, `.importlinter` carries a baseline ignore line (see "Baseline" below). The core is not redesigned: no file under `Source/` changes.

### The four layers

An import points down: a module imports from its own layer or a lower one, never from a higher one. Skipping a layer is allowed.

| Layer | Modules | What it is |
|---|---|---|
| 1. Entry points | `GitHub_Connector.api` | the hosted app: the `/system` routes, the console and the pages |
| | `drifter.cli` | the `drifter` command |
| | `Tester` (the whole package) | the tester: its routes, its HTTP client and its tests |
| 2. Services | `GitHub_Connector.analysis`, `.course`, `.fetch`, `.rules`, `.runs`, `.schemas`, `.settings` | what the hosted app adds around one check: the clone, change detection, the result store, sessions, settings |
| | `Frontend` | the pages: loading, comparing and drawing models |
| 3. Core | `drifter.check` | one check, the readers, scope, the diff and the ownership checker |
| 4. Generators | `models.common` | `parse_files`, `write_model`, the glob |
| | `models.structural_model` | the structural generator and its schema |
| | `models.behavioral_model` | the behavioral generator and its schema |
| | `models.ownership_model` | the ownership proposal, `CommitRecord` and its schema |

The map names no owners, for any file, folder or layer: the import check does not use them, and a label nobody checks goes stale. The GitHub Action (Phase 5, not built) calls `drifter.cli` and adds no Python package.

`Source/Frontend/ui.py` can also be started on its own for local work (`python Source/Frontend/ui.py`, `Source/Frontend/README.md:32`). It imports none of the five packages, so it stays under `Frontend` in the services layer and is not a fourth entry point of the map.

### The allowed calls

| Rule | In words | Contract in `.importlinter` |
|---|---|---|
| A1 | Imports point down through the four layers. | `layers` |
| A2 | The three entry points do not import each other. One exception, for as long as one container serves both: `GitHub_Connector.api` imports `Tester.api` to mount the tester's routes. | `layers` (the entry points are independent siblings), with one ignore line that stays |
| A3 | Services may import each other, except that `Frontend` imports no `GitHub_Connector` module. | `layers` and `frontend` |
| A4 | `Tester` reaches the system over HTTP only: it imports none of `GitHub_Connector`, `Frontend` and `drifter`. | `tester` |
| A5 | `Frontend` imports neither `Tester` nor `drifter.check`. The hosted app asks the core and hands `Frontend` the result. | `frontend` |
| A6 | `drifter` and `models` import none of `GitHub_Connector`, `Frontend` and `Tester`. | `core` |

`tests/` is outside the map: a test may import any module.

### Public names

What a module in another package may use. `import-linter` checks modules, not names, so this table is guidance. Each name is one that another package imports today.

| Package | Public names |
|---|---|
| `models` | `common`: `parse_files`, `write_model`, `glob`, `ParseFailed`. `structural_model`: `generate_structural`. `behavioral_model`: `generate_behavioral`. `ownership_model`: `propose_ownership`, `CommitRecord`, `PathTouch`, `WINDOW`. |
| `drifter` | `check`: `answer`, `read_sources`, `local_sources`, `generate_models`, `regenerate_models`, `proposed_ownership`, `LocalReader`, `DriftError`, `MODEL_FILES`, `DEFAULT_SCOPE`, `GENERATORS`, `in_scope`, `LOG_ARGS`, `REGULAR`. `cli`: `main`. |
| `GitHub_Connector` | `api`: `app`, the object `uvicorn` serves. Nothing else: no other package imports it. |
| `Frontend` | `model_drift`: `committed`, `snapshot`, `drifted`, `SnapshotFailed`, `Verdict`. `model_loader`: `OWNERSHIP_FILE`, `SCOPE_FILE`, `models_from_dicts`. `model_viewer`: `render`. |
| `Tester` | `api`: `router`, for the one exception of A2. |

### The contracts

One file, `.importlinter`, with `root_packages` naming the five packages and five contracts. `unmatched_ignore_imports_alerting` is not set, so it keeps its default, `error`: an ignore line that matches no import fails the run.

| Contract id | Type | What it lists |
|---|---|---|
| `layers` | layers | line 1: `GitHub_Connector.api \| Tester \| drifter.cli`; line 2: the seven `GitHub_Connector` service modules and `Frontend`, joined by `:`; line 3: `drifter.check`; line 4: `models` |
| `tester` | forbidden | source `Tester`; forbidden `GitHub_Connector`, `Frontend`, `drifter` |
| `frontend` | forbidden | source `Frontend`; forbidden `GitHub_Connector`, `Tester`, `drifter.check` |
| `core` | forbidden | sources `drifter`, `models`; forbidden `GitHub_Connector`, `Frontend`, `Tester` |
| `connector` | layers, with `containers = GitHub_Connector` and `exhaustive = true` | line 1: `api`; line 2: the seven service modules, joined by `:`. No ignore line. Added by step 5, after the human asked on 2026-11-21 that CI catch a new module nobody listed. |

In a layers line, `|` means the modules must not import each other and `:` means they may. With `exhaustive = true`, every module directly inside the container must be on one of the contract's lines, or the contract breaks.

### Baseline: the imports that break the map today

Each is one ignore line, with a comment above it that names what removes it or says why it stays.

| Import | Breaks | Ignore line in | Removed by |
|---|---|---|---|
| `GitHub_Connector.api -> Tester.api` (`Source/GitHub_Connector/api.py:19`) | A2 | `layers` | Stays: the allowed exception. W3-6 removes it if the tester is split into its own service. |
| `Frontend.model_drift -> drifter.check` (`Source/Frontend/model_drift.py:17`) | A5 | `frontend` | W3-3: the page asks the core for the models at a commit. Step 7 adds the promise to W3-3's Done column, which does not hold it today (`docs/state/WORK-ITEMS.md:184`). |

### Left out, on purpose

- **A new `GitHub_Connector` module has to be listed twice, and only one of the two is checked.** The `connector` contract breaks until the module is on one of its lines, so CI catches a module nobody listed. Line 2 of the `layers` contract takes no wildcard and has no such check: someone adds the module there by hand, and the two lists can disagree. The four other packages need no such contract: `layers` names `Frontend`, `Tester` and `models` whole, and `drifter` holds only `check` and `cli`, both listed.
- **Names are not checked.** A caller can import a name the Public names table does not list.
- **An import the tool cannot see is not checked:** one built from a string at run time. None exists today.

## Premises, verified

Every fact the structure rests on, checked against the disk before it is written here. The `lint-imports` runs used `import-linter` 2.17 in a throwaway virtualenv, with the draft contracts in a scratch file and `PYTHONPATH=Source`.

| Premise | How verified | Holds? |
|---|---|---|
| The five packages can be analysed from the repository root, `Frontend` included although it has no `__init__.py`. | `lint-imports` printed `Analyzed 27 files, 47 dependencies.` | yes |
| With no ignore line, exactly two imports break the map: the two in the Baseline table. | `lint-imports` printed `Contracts: 2 kept, 2 broken.` and named `GitHub_Connector.api -> Tester.api (l.19)` and `Frontend.model_drift -> drifter.check (l.17)` | yes |
| With the two ignore lines the first four contracts pass. | `lint-imports` printed `Contracts: 4 kept, 0 broken.`, exit 0 | yes |
| With the `connector` contract added, and no ignore line in it, all five pass. | On the committed `.importlinter` plus that contract, in a scratch file: `Every connector module has a layer KEPT`, `Contracts: 5 kept, 0 broken.`, exit 0 | yes |
| A new `GitHub_Connector` module that nobody listed fails the run. | On a copy of `Source/` with an added `GitHub_Connector/eighth.py`: `Every connector module has a layer BROKEN`, `Contracts: 4 kept, 1 broken.`, exit 1, and the output names `GitHub_Connector.eighth` | yes |
| A planted forbidden import fails the run. | On a copy of `Source/` with `from GitHub_Connector import settings` added to `drifter/check.py`: `Contracts: 2 kept, 2 broken.`, exit 1 | yes |
| An ignore line that matches no import fails the run, at the default setting. | With one ignore line pointed at `drifter.cli`: `No matches for ignored import Frontend.model_drift -> drifter.cli.` | yes |
| A comment line inside `ignore_imports` is accepted. | The passing run above had one comment line above each ignore line | yes |
| `import-linter` 2.17 is the newest release, and it has six contract types: forbidden, layers, independence, protected, private_modules and acyclic_siblings. The map uses the first two. | `pip index versions import-linter`; `importlinter/application/use_cases.py:650-655` in the 2.17 install | yes |
| No module under `Source/` builds an import from a string. | `git grep -n -E "importlib\|__import__\|import_module" -- Source` finds only `from importlib import resources` (`Source/drifter/check.py:18`) | yes |
| `Tester` imports no other package of the five today. | `git grep -n -E "^(from\|import) (drifter\|models\|GitHub_Connector\|Frontend)" -- Source/Tester` prints nothing | yes |
| Editing `.importlinter` and `docs/diagrams/dependency.md` already prompts the human. | `.claude/settings.json:12-13` | yes |
| CI is one job that installs both requirements files, then runs `pytest` and `ruff check`. | `.github/workflows/ci.yml:22-24` | yes |
| Rule R5 in `CLAUDE.md` agrees with the allowed calls. | `CLAUDE.md:42` says `Tester` and `Frontend` may import `drifter`; A4 and A5, taken from the W1-5 row, say otherwise | no; answered by the human on 2026-11-21: the row stands, and step 7 rewords R5 |

The one premise that does not hold is a line in the Epic's Open questions, with the human's answer.

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| INV-3 (new) | Imports under `Source/` follow the module map in `docs/diagrams/dependency.md`: rules A1 to A6, less the ignore lines listed in `.importlinter`. | `PYTHONPATH=Source lint-imports` prints `Contracts: 5 kept, 0 broken.`; a CI step from step 4, proven red by step 6 |
| INV-1 | Determinism: the same input gives byte-identical models and answer. | Not touched: `git diff --stat main...HEAD -- Source tests` prints nothing |
| Every connector module has a layer | A module directly inside `GitHub_Connector` is on a line of the `connector` contract. | `PYTHONPATH=Source lint-imports --no-cache \| grep -c "Every connector module has a layer KEPT"` prints `1` |
| The baseline only shrinks | `.importlinter` holds two ignore lines; a third needs the human's approval of the file. | `PYTHONPATH=Source lint-imports --no-cache | grep -c "KEPT (1 ignored import)"` prints `2`, and the same run ends with `Contracts: 5 kept, 0 broken.`, so the other three contracts ignore nothing; the edit prompt on `.importlinter` (`.claude/settings.json:12`) |

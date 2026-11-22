# Model generation parameters, and verbosity as the first of them

Epic: `docs/epics/E02-model-parameters/EPIC.md`

## Intended structure

A model generation parameter is a value that changes what a generator emits. It is declared once
per repository, in `models/scope.json`, and committed. It is therefore part of `/models`, which is
what makes it safe: INV-1 already names `/models` among the three inputs that decide the bytes, and
INV-2 already covers "the scope rules" among the files an author must not change to pass their own
change. Neither invariant is reworded by this Epic. A parameter kept anywhere else, in a browser or
in a request, would put the bytes of a model outside those three inputs and end determinism.

`verbosity` is the first parameter. It is an integer, 1 to 4, and it names how much of the code the
structural model describes. The four levels are a ladder: each keeps everything the level below it
keeps, and adds one layer.

| Level | Name | Structural keeps | What it answers |
|---|---|---|---|
| 1 | Overview | `module` nodes, `imports` edges | which parts of the repository depend on which |
| 2 | Types | level 1, plus `class` nodes and `inherits` edges | plus: which types extend which |
| 3 | Members | level 2, plus `function` and `method` nodes, with no `params`, `decorators` or `is_async` | plus: what each type and module offers |
| 4 | Full | level 3, plus `params`, `decorators` and `is_async` on every function and method | plus: the signature of each one |

Level 4 is the default and is byte-identical to what the generators write today, so every golden in
`docs/contract/model-golden-outputs.json` and every structural test passes untouched. A repository
that commits no `verbosity` key is at level 4.

The seam changes in one way only. `docs/diagrams/model-seam.md` states the generator contract as
`generate_structural(files) -> dict`; it becomes `generate_structural(files, verbosity=FULL) -> dict`,
a keyword argument with a default. Every one of the 29 call sites outside the core keeps working
unchanged, and the core's `GENERATORS` map in `Source/drifter/check.py` passes the value it read
from `scope.json`. Behavioral keeps every element at every level in this Epic: it has no ladder yet,
and inventing one is the "what is missing" note below, not this Epic's work.

The panel is the console's, not the viewer page's. `Source/Frontend/model_viewer.py` renders a page
with no scripts of its own, and that stays true: the panel lives in `Source/Frontend/index.html`,
which already runs scripts and already persists reader state in `localStorage` under one `STORE` key.
The panel sets a level, the console puts it on the iframe URL as `verbosity`, and
`GET /models/view` regenerates at that level. The reader's chosen level is remembered per browser,
beside the watchlist, and it is a preview: it never writes to any repository.

So there are two distinct things, and the page names both:

- **the committed level**, in `models/scope.json`, which is what `drifter check` and `/system/analyze`
  use, and which is per repository;
- **the previewed level**, from the panel, which is what the console's Models view draws, and which
  is per reader and per browser.

Where they differ, the viewer page carries a note in the same place and style as its existing
provenance and comparison notes: showing level 3 of 4, the repository commits level 4, and the drift
chips on this page compare level 3 against level 3. A preview read as the real check is the one way
this panel could mislead, so, like `_provenance`, it never goes unmarked.

## Premises, verified

Every fact the structure rests on, checked against the disk before it is written here.

| Premise | How verified | Holds? |
|---|---|---|
| INV-1 already counts `/models` among the inputs that fix the bytes, so a parameter inside it needs no rewording | `docs/invariants/INVARIANTS.md:16`, INV-1 | yes |
| INV-2 already covers the scope rules, so a parameter inside `scope.json` inherits the W0-7 hole and its fix rather than opening a new one | `docs/invariants/INVARIANTS.md:17`, INV-2 | yes |
| `generate_structural(files)` and `generate_behavioral(files)` take one argument today, and the core calls them through one map | `Source/models/structural_model.py:15`, `Source/models/behavioral_model.py:17`, `Source/drifter/check.py:104-105` | yes |
| 29 call sites would break on a positional parameter, which is why the new one is keyword with a default | `grep -rn "generate_structural\|generate_behavioral" Source tests` gives 29 invocations outside the two definitions | yes |
| The structural model already carries exactly the four node kinds and two edge kinds the ladder cuts on | `Source/models/structural_model.py:1-2`, `docs/diagrams/models-folder.md`, the `structural.json` box | yes |
| `scope.json` has no JSON Schema yet, so a new key is read and validated in the same place `include` and `exclude` are | `Source/drifter/check.py:153-154`; `docs/diagrams/models-folder.md` lists "open: JSON Schema"; W3-1 is the row that adds it | yes |
| `GET /models/view` is the console's own route, kept out of the OpenAPI document, so a new query parameter is not a contract change and needs no agreement from Team 16 | `Source/GitHub_Connector/api.py:169`, `include_in_schema=False` | yes |
| The viewer page runs no script of its own, so the panel cannot live inside it without ending that | `Source/Frontend/model_viewer.py:1-6` and `_script`, whose only job is Mermaid | yes |
| The console already persists reader state per browser in `localStorage`, so the panel adds a key to a store that exists rather than a mechanism that does not | `Source/Frontend/index.html:288-299` | yes |
| The viewer page already carries notes that separate what a page shows from what it proves, in the style this panel's note follows | `Source/Frontend/model_viewer.py`, `_provenance` and `_compared` | yes |
| `docs/base/structure.md:4` and `docs/base/specifications.md:261` both become untrue and are fixed in the same PR under R2 | `grep -n` on both files | yes |
| `docs/base/specifications.md:213`, "four files", stays true, because verbosity is a key and not a fifth file | `docs/base/specifications.md:213` | yes |
| Lowering the level hides drift in everything it drops, which is gap G4 of W0-7 in a new place and not a new kind of hole | `docs/state/WORK-ITEMS.md`, W0-7 detail, gap G4 | yes |
| No import contract changes: the panel is console-side and the parameter is read where scope is read | `.importlinter`, and rule R5 in `CLAUDE.md` | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| INV-1 | The same repository version, `/models` and tool version give byte-identical models. The level is read from committed `/models`, never from a request or a browser, and the default is today's output. | `pytest tests/structural tests/common/test_seam.py tests/drift -q`, plus the new `tests/structural/test_verbosity.py` case that asserts `generate_structural(CODE)` equals `generate_structural(CODE, verbosity=4)` byte for byte through `write_model` |
| INV-2 | No author can change the rules to pass their own change. Verbosity sits in `scope.json`, so the W0-7 ruling must name it: whichever option closes `scope.json` closes verbosity with it. | DEFERRED. The check arrives with the W0-7 ruling, build order step 4.3 or 4.4 (row W3-5). This Epic adds the test that a lowered level hides a real drift, marked expected-fail until that ruling lands. |
| INV-3 | Imports under `Source/` follow the module map. The panel is in `index.html`, the route stays in `GitHub_Connector`, the levels are applied in `models`. | `PYTHONPATH=Source lint-imports` ends `Contracts: 5 kept, 0 broken.` |

## What is missing from a complete solution

Named here, not built, so that leaving them out is the human's decision and not an oversight.

- **Behavioral has no ladder.** Every level emits every state and transition. A behavioral ladder
  needs a grain for machines, and row N2 has not been ruled on.
- **Ownership has none either**, and should not: it is checked, never regenerated.
- **One parameter, not a set.** `scope.json` gains one key. A general parameter block, a
  per-generator namespace or a parameter registry would be the shape for the second and third
  parameter, and designing it now would be designing for one example.
- **Lowering the level floods the next check.** Every element the new level drops is reported
  REMOVED once. There is no "accept the level change without reporting its drift" path, and
  `drifter update` is the only way through it.
- **The preview is per reader, not per repository.** Two readers of the same repository can be
  looking at different levels, and nothing on a screenshot of one says so except its note.
- **No verbosity in the reporter.** W4-3 renders the answer to annotations and a job summary; it
  will not say which level produced it.

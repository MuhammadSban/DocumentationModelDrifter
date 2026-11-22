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

### The level is chosen before the first model exists, and a change to it redefines the baseline

This is the whole of how verbosity behaves over time, and it needs no new machinery.

`drifter init` gains `--verbosity`, writes it into the `scope.json` it writes, and generates the
first `structural.json` at that level. So the level is set before the initial model is generated,
and the first baseline is already at the chosen level.

Afterwards the level is changed the way the scope is changed: a person edits `models/scope.json` by
hand in a reviewed PR and runs `drifter update`, which reads the scope committed at that commit and
rewrites `structural.json` and `behavioral.json` from it (`Source/drifter/cli.py:4-5`). The models
it writes **are** the new baseline. Nothing reports the elements the old level held and the new one
does not: there is no comparison between two levels anywhere, because the check never compares two
commits' models. It regenerates at one commit and sets the result against the model committed at
that same commit (`Source/drifter/check.py:110-119`, and "One check" in `docs/diagrams/model-seam.md`).

Both sides of that comparison therefore read their level from the same committed `scope.json`, and
can never disagree about it. The one case left is a person who edits the level and does not
regenerate, and that case already has a spec sentence and needs no new one: "Editing the scope
without regenerating the models shows up as drift by itself" (`docs/base/specifications.md:264`).
Verbosity is part of the scope, so the sentence covers it as written.

`_regenerate(files)` in `Source/drifter/check.py:290` is the one place every generation passes
through, from all three entry points: `generate_models` for init, `regenerate_models` for update,
and `model_differences` for the check. It takes the level and hands it to the structural generator.
The check reads the level from `sources.models["scope.json"]`, which `read_sources` has already
parsed and validated, so `Sources` gains no field.

### The panel is on the viewer page, and the function of it needs no script

`Source/Frontend/model_viewer.py` renders the panel into the page itself, above the three model
panels. It is a plain HTML form, `method="get"`, pointing at the route the page was served from:
four radio stops named Overview, Types, Members and Full, `repository` and `commit_id` as hidden
inputs, and a submit button. Choosing a level and submitting is a new GET of
`/models/view`, which regenerates at that level. No JavaScript is involved in the function of the
panel, so a blocked CDN or a disabled script leaves the panel working.

Only remembering the choice needs a script, and it is the page's first: a few lines that read and
write one key in `localStorage` and preselect the stop, wrapped in try and catch so that a private
window or blocked storage leaves the panel working in memory. That ends the property that the page
runs no script but Mermaid. The human asked for the panel on the viewer page on 2026-11-22, so the
property is spent knowingly, and the panel is written so that losing the script costs the memory
and nothing else.

The page is also rendered standalone, by `python -m Frontend.model_viewer`, into a file with no
server behind it. There the form has nowhere to submit, so `render` takes the route it was served
from and renders the panel read-only without one: the committed level, and the sentence that
changing it means editing `models/scope.json` and running `drifter update`. A page that offered a
control that silently did nothing would be worse than a page that offers none.

`Source/Frontend/index.html` does not change. The console frames the page, and the page now carries
its own control, so the console neither builds the panel nor holds the reader's choice.

### Two distinct things, and the page names both

- **The committed level**, in `models/scope.json`: what `drifter check`, `drifter update` and
  `/system/analyze` use, and what the baseline is at. Per repository.
- **The previewed level**, from the panel: what the console's Models view is drawing right now.
  Per reader and per browser, and it never writes to any repository.

Where they differ, the page carries a note in the same place and style as its existing provenance
and comparison notes: showing level 3 of 4, the repository commits level 4, and the drift chips on
this page compare level 3 against level 3. A preview read as the real check is the one way this
panel could mislead, so, like `_provenance`, it never goes unmarked.

## Premises, verified

Every fact the structure rests on, checked against the disk before it is written here.

| Premise | How verified | Holds? |
|---|---|---|
| INV-1 already counts `/models` among the inputs that fix the bytes, so a parameter inside it needs no rewording | `docs/invariants/INVARIANTS.md:16`, INV-1 | yes |
| INV-2 already covers the scope rules, so a parameter inside `scope.json` inherits the W0-7 hole and its fix rather than opening a new one | `docs/invariants/INVARIANTS.md:17`, INV-2 | yes |
| The check never compares two commits' models: it regenerates at one commit and sets that against the model committed at the same commit, so two levels are never diffed against each other | `Source/drifter/check.py:110-119`, `model_differences` and `differences`; "One check" in `docs/diagrams/model-seam.md` | yes |
| `drifter update` reads the scope committed at the commit and rewrites only the two generated models, which is exactly the re-baseline a level change needs | `Source/drifter/cli.py:4-5`, `Source/drifter/check.py:279-287` | yes |
| The spec already states the semantic for editing the scope without regenerating, and verbosity is part of the scope | `docs/base/specifications.md:264` | yes |
| One choke point exists for every generation, from all three entry points | `Source/drifter/check.py:290`, `_regenerate`, called by `generate_models`, `regenerate_models` and (through `GENERATORS`) `model_differences` | yes |
| The check already has the committed scope parsed and validated where the generators run, so `Sources` needs no new field | `Source/drifter/check.py:79-83` and `:230`, `_scope_rule(models["scope.json"])` | yes |
| `drifter init` writes `scope.json` itself, so a flag can set the level before the first generation | `Source/drifter/check.py:263-270`, `generate_models`, and `Source/drifter/cli.py:57-65` | yes |
| `generate_structural(files)` and `generate_behavioral(files)` take one argument today | `Source/models/structural_model.py:15`, `Source/models/behavioral_model.py:17` | yes |
| 29 invocations would break on a positional parameter, which is why the new one is keyword with a default | `grep -rn "generate_structural(\|generate_behavioral(" Source tests` gives 29 outside the two definitions | yes |
| The structural model already carries exactly the four node kinds and two edge kinds the ladder cuts on | `Source/models/structural_model.py:1-2`; the `structural.json` box of `docs/diagrams/models-folder.md` | yes |
| `scope.json` has no JSON Schema yet, so a new key is validated where `_scope_rule` validates the rest | `Source/drifter/check.py:230`, `:285`; `docs/diagrams/models-folder.md` lists "open: JSON Schema"; W3-1 is the row that adds it, and W3-1 deletes `_scope_rule` in favour of the schema | yes |
| `GET /models/view` is the console's own route, kept out of the OpenAPI document, so a new query parameter is not a contract change and needs no agreement from Team 16 | `Source/GitHub_Connector/api.py:169`, `include_in_schema=False` | yes |
| The viewer page runs no script but Mermaid today, so the panel's memory ends that property; its function does not need to | `Source/Frontend/model_viewer.py:1-6` and `_script` | yes |
| The page is rendered standalone with no server, where a form has nowhere to submit | `Source/Frontend/model_viewer.py`, `main`, and the module comment's own CLI line | yes |
| The viewer page already carries notes that separate what a page shows from what it proves, in the style this panel's note follows | `Source/Frontend/model_viewer.py`, `_provenance` and `_compared` | yes |
| `docs/base/structure.md:4` and `docs/base/specifications.md:261` both become untrue and are fixed in the same PR under R2 | `grep -n` on both files | yes |
| `docs/base/specifications.md:213`, "four files", stays true, because verbosity is a key and not a fifth file | `docs/base/specifications.md:213` | yes |
| Lowering the level hides drift in everything it drops, which is gap G4 of W0-7 in a new place and not a new kind of hole | `docs/state/WORK-ITEMS.md`, W0-7 detail, gap G4 | yes |
| No import contract changes: the panel is inside the Frontend, the route stays in `GitHub_Connector`, the levels are applied in `models` | `.importlinter`, and rule R5 in `CLAUDE.md` | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| INV-1 | The same repository version, `/models` and tool version give byte-identical models. The level is read from committed `/models`, never from a request or a browser, and the default is today's output. The panel's level reaches one route and no generator that writes a file. | `pytest tests/structural tests/common/test_seam.py tests/drift -q`, plus the new `tests/structural/test_verbosity.py` case asserting that `write_model(generate_structural(CODE))` equals `write_model(generate_structural(CODE, verbosity=4))` byte for byte |
| INV-2 | No author can change the rules to pass their own change. Verbosity sits in `scope.json`, so the W0-7 ruling must name it: whichever option closes `scope.json` closes verbosity with it. | DEFERRED. The check arrives with the W0-7 ruling, build order step 4.3 or 4.4 (row W3-5). This Epic adds the test that a lowered level plus `drifter update` in one commit hides a real drift, marked expected-fail until that ruling lands. |
| INV-3 | Imports under `Source/` follow the module map. The panel is in `Frontend`, the route stays in `GitHub_Connector`, the levels are applied in `models`. | `PYTHONPATH=Source lint-imports` ends `Contracts: 5 kept, 0 broken.` |

## What is missing from a complete solution

Named here, not built, so that leaving them out is the human's decision and not an oversight.

- **Behavioral has no ladder.** Every level emits every state and transition. A behavioral ladder
  needs a grain for machines, and row N2 has not been ruled on.
- **Ownership has none either**, and should not: it is checked, never regenerated.
- **One parameter, not a set.** `scope.json` gains one key. A general parameter block, a
  per-generator namespace or a parameter registry would be the shape for the second and third
  parameter, and designing it now would be designing for one example.
- **A level change is a large diff, even though it is not drift.** `drifter update` rewrites
  `structural.json` whole, so the PR that lowers the level carries every dropped element as a
  deleted line. That is a reviewer's problem and not the check's, and nothing here shrinks it.
- **Nothing warns that a level was lowered.** The check reports no drift for a re-baselined level,
  by design; a reviewer who does not read `scope.json` in the diff will not learn that the models
  now describe less. The W0-7 ruling is where that belongs, because it is the same gap.
- **The preview is per reader, not per repository.** Two readers of the same repository can be
  looking at different levels, and nothing on a screenshot of one says so except its note.
- **The panel's memory is per origin.** The page is framed from the API's origin, so a reader who
  points the console at a different API starts again from the committed level.
- **No verbosity in the reporter.** W4-3 renders the answer to annotations and a job summary; it
  will not say which level produced it.

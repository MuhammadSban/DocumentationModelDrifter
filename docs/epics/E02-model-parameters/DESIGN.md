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

Afterwards the level is changed with `drifter update --verbosity`, which writes the new level into
`scope.json` and regenerates at it together, so the one commit carrying both is aligned. **Corrected
in step 8, after driving the installed command:** this was first designed as a hand edit of
`scope.json` followed by a plain `drifter update`, and that does not work. `update` reads the scope
**committed at the commit**, not the working tree (`Source/drifter/cli.py`), so a level edited only
in the working tree makes it regenerate at the old level and leaves the repository in drift. Two
commits did work, the first of them deliberately red; the flag replaced them with one.

Either way the models `update` writes **are** the new baseline. Nothing reports the elements the old
level held and the new one does not: there is no comparison between two levels anywhere, because
the check never compares two commits' models. It regenerates at one commit and sets the result
against the model committed at that same commit (`model_differences` and `differences` in
`Source/drifter/check.py`, and "One check" in `docs/diagrams/model-seam.md`).

Both sides of that comparison therefore read their level from the same committed `scope.json`, and
can never disagree about it. The one case left is a person who edits the level and does not
regenerate, and that case already has a spec sentence and needs no new one: "Editing the scope
without regenerating the models shows up as drift by itself" (`docs/base/specifications.md:263-264`).
Verbosity is part of the scope, so the sentence covers it as written.

### Three generation sites take the level, and one function decides which generator has a ladder

Corrected twice: the first review found the second site, the second review found the third. There
is no choke point. A model is generated in three places, and the level reaches all three.

1. **`_regenerate(files, verbosity)`** in `Source/drifter/check.py`, for `generate_models`
   (`drifter init` and `POST /system/generate`) and `regenerate_models` (`drifter update`).
2. **`model_differences`** in `Source/drifter/check.py`, for the check itself. It calls
   `generate_one` directly, without going through `_regenerate`, and reads the level from
   `sources.models["scope.json"]`, which `read_sources` has already parsed and validated with
   `_scope_rule`, so `Sources` gains no field. This is the site that matters most: miss it and the
   check regenerates at level 4 against a level-1 committed model and reports every element the
   level drops as `REMOVED`.
3. **`snapshot(reader, commit, verbosity)`** in `Source/Frontend/model_drift.py`, which the
   console's models page uses for its naive chip. It loops over `GENERATORS` itself and never calls
   `_regenerate` either. That duplication is known and is not this Epic's to repair:
   `.importlinter:47` carries the ignore line `Frontend.model_drift -> drifter.check` with the
   comment "removed by W3-3, the page asks the core for the models at a commit". E02 passes the
   level to it and leaves the duplication to W3-3.

What the three sites do share is **`generate_one(name, files, verbosity)`**, which this Epic adds to
`Source/drifter/check.py` beside `GENERATORS`. Only structural has a ladder: behavioral keeps every
element at every level while N2 is unruled, so it is still called with one argument. That fact lives
in `generate_one` and nowhere else, so the three sites each pass the level and none of them repeats
the decision. `GENERATORS` is retyped `dict[str, Callable[..., dict]]`, because its entries no
longer share one signature and `ruff` is not a type checker that would have caught the old
annotation going stale.

`snapshot` already reads the commit's own `scope.json` to choose its files (`_scope`,
`_scope` in the same file), so the committed level is there to be read when no level
is given. A level passed in is the panel's preview and overrides it.

`models_view` in `Source/GitHub_Connector/api.py` calls `snapshot` twice, at the head and at the base,
and the chip is the comparison of the two. Both calls take the same level, or the chip would set
the previewed level against level 4 and report drift that is only the preview. This is what makes
the page's claim true that the chips compare the drawn level with itself.

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
from and renders the panel read-only without one: the committed level, and the one command that
changes it, `drifter update --verbosity`. A page that offered a control that silently did nothing
would be worse than a page that offers none.

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
| The check never compares two commits' models: it regenerates at one commit and sets that against the model committed at the same commit, so two levels are never diffed against each other | `model_differences` and `differences` in `Source/drifter/check.py`; "One check" in `docs/diagrams/model-seam.md` | yes |
| **Corrected in step 8, by driving the installed command.** `drifter update` reads the scope committed at the commit, not the working tree, so on its own it is **not** the re-baseline a level change needs: it regenerates at the old level and leaves the repository in drift. `update --verbosity` writes the level and the models together, which is one commit. | `Source/drifter/cli.py`, the module comment and `update`'s `--verbosity`; `Source/drifter/check.py`, `regenerate_models`; driven by hand on 2026-11-22 and pinned by `test_update_with_a_level_changes_it_and_rebaselines_in_one_commit` | no, as first written; yes as corrected |
| The spec already states the semantic for editing the scope without regenerating, and verbosity is part of the scope | "Editing the scope without regenerating the models shows up as drift by itself", `docs/base/specifications.md` §3.2, Scope | yes |
| **Corrected twice, by the first and second reviews. There is no choke point: three sites generate a model and the level must reach all three.** `_regenerate` serves init, update and `POST /system/generate`; `model_differences` calls `generate_one` itself for the check, never `_regenerate`; the console's page has its own loop over `GENERATORS` | `_regenerate`, `model_differences` and `generate_one` in `Source/drifter/check.py`; `snapshot` in `Source/Frontend/model_drift.py` | yes, as corrected |
| Only structural has a ladder, so one function decides which generator takes a level and the three sites do not each repeat it | `generate_one` beside `GENERATORS` in `Source/drifter/check.py`, added by this Epic; behavioral keeps every element at every level while N2 is unruled | by construction |
| The `GENERATORS` annotation stops being true of one entry once structural takes a level, and nothing would catch it: CI runs `ruff`, not a type checker | the `GENERATORS` declaration in `Source/drifter/check.py`, which was `dict[str, Callable[[dict[str, str]], dict]]`; `.github/workflows/ci.yml` runs `pytest`, `ruff check` and `lint-imports` only | yes, so step 3 retypes it |
| The console's page regenerates through `snapshot` twice, at the head and at the base, so both calls must take the same level or the chip compares the preview with level 4 | the two `model_drift.snapshot` calls in `models_view`, `Source/GitHub_Connector/api.py` | yes |
| `snapshot` already reads the commit's own `scope.json`, so the committed level is there to read when the panel passes none | `snapshot` and `_scope` in `Source/Frontend/model_drift.py` | yes |
| `model_drift`'s duplicate reading is known and owned by another row, so E02 passes the level and does not unify the two sites | the ignore line `Frontend.model_drift -> drifter.check` in `.importlinter` and its comment "removed by W3-3"; W3-3's row in `docs/state/WORK-ITEMS.md` | yes |
| **Corrected after the first review.** `generate_models` has a second caller that passes one argument, so its new parameter is keyword with a default and `analysis.py` needs no edit | `check.generate_models(cmp)` inside `generate`, `Source/GitHub_Connector/analysis.py` | yes, as corrected |
| The check already has the committed scope parsed and validated where the generators run, so `Sources` needs no new field | the `Sources` dataclass and `read_sources`, which calls `_scope_rule(models["scope.json"])`, in `Source/drifter/check.py` | yes |
| `drifter init` writes `scope.json` itself, so a flag can set the level before the first generation | `generate_models` in `Source/drifter/check.py` and `_init` in `Source/drifter/cli.py` | yes |
| `generate_structural(files)` and `generate_behavioral(files)` took one argument before this Epic | the two definitions in `Source/models/structural_model.py` and `Source/models/behavioral_model.py` | yes |
| 29 invocations would break on a positional parameter, which is why the new one is keyword with a default | `grep -rn "generate_structural(\|generate_behavioral(" Source tests` gave 29 outside the two definitions | yes |
| The structural model already carries exactly the four node kinds and two edge kinds the ladder cuts on | the module comment of `Source/models/structural_model.py`; the `structural.json` box of `docs/diagrams/models-folder.md` | yes |
| `scope.json` has no JSON Schema yet, so a new key is validated where `_scope_rule` validates the rest | `_scope_rule` in `Source/drifter/check.py`; `docs/diagrams/models-folder.md` lists "open: JSON Schema"; W3-1 is the row that adds it, and W3-1 deletes `_scope_rule` in favour of the schema | yes |
| `GET /models/view` is the console's own route, kept out of the OpenAPI document, so a new query parameter is not a contract change and needs no agreement from Team 16 | the `include_in_schema=False` on `models_view`, `Source/GitHub_Connector/api.py` | yes |
| The viewer page runs no script but Mermaid today, so the panel's memory ends that property; its function does not need to | `_script` and `MERMAID` in `Source/Frontend/model_viewer.py`. Its module comment said "no server, no scripts, no network", which those two already made untrue and the panel's memory makes wronger; step 6 rewords it | yes |
| The page is rendered standalone with no server, where a form has nowhere to submit | `main` in `Source/Frontend/model_viewer.py`, and the CLI line of its module comment | yes |
| The viewer page already carries notes that separate what a page shows from what it proves, in the style this panel's note follows | `_provenance` and `_compared` in `Source/Frontend/model_viewer.py` | yes |
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
- **~~One parameter, not a set.~~ Built in step 10, by the human's ask of 2026-11-22.** `PARAMETERS`
  in `Source/drifter/check.py` declares each key with its default and allowed values, and
  `parameters_of` and `_scope_rule` both work from it. What is still verbosity's own: `generate_one`
  names `verbosity` and `"structural"` by hand, and the three sites pass the level positionally, so
  a second parameter is a row plus those edits, not a row alone. The reading and validating half,
  which is the expensive one, is genuinely general. A per-generator namespace and a parameter block
  inside `scope.json` are still not built, and nothing here names a parameter to come.
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
- **The hosted `init` can only propose level 4.** `POST /system/generate` calls `generate_models`
  with the reader alone (`generate` in `Source/GitHub_Connector/analysis.py`) and `generate_models`
  writes `DEFAULT_SCOPE`, which carries no key. Taking a level there would be a request field on a
  contract route, so it needs Team 16's agreement and is not this Epic's. `drifter init
  --verbosity` is the way to start below 4.

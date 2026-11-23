# Who writes /models

Epic: `docs/epics/E07-who-writes-models/EPIC.md`

## Intended structure

Nothing new is built. This is who writes each file of `/models` today, stated in a second model:

- `structural.json` and `behavioral.json` are written only by `drifter init` and `drifter update`. `drifter check` and `POST /system/analyze` regenerate them in memory and never write them. `POST /system/generate` returns them and does not save them.
- `ownership.json` and `scope.json` are written once by `drifter init`. After that, a person edits them by hand, in a reviewed commit. `drifter update` reads `scope.json` and leaves `ownership.json` untouched.
- A person does not edit the two generated files by hand. A hand edit that does not match the code is listed on every check. At the default volatility, 1 (Exact), it is drift. At a higher volatility it is drift only once the model carries more changes than that level tolerates.

`docs/diagrams/data-flow.md` draws the writers as dotted arrows into `/models` and holds this as the table "## Who writes /models" (`:71-79`). After this Epic, `docs/diagrams/models-folder.md`, the model of the folder itself, holds the same table under the same heading, at the end of the file. Neither drawing changes. The one change to `data-flow.md` is the qualifier on its last row, which PR #61 (volatility) made necessary.

## Premises, verified

Every fact the structure rests on, checked against the disk before it is written here.

| Premise | How verified | Holds? |
|---|---|---|
| `data-flow.md` holds the table at `:71-79`, and its rows match the code | `git grep -n "^## Who writes /models" -- docs/diagrams/data-flow.md` → `:71`; its own "Premises, verified" table checks `drifter init` at `:132` | yes |
| `models-folder.md` has no table of writers | its headings are `# The /models folder` and `## The verbosity ladder` only | yes |
| A hand edit to `structural.json` is drift at the default volatility | golden case L7, `docs/contract/model-golden-outputs.json`; `tests/connector/test_model_golden.py:23` | yes |
| A hand edit to `behavioral.json` is drift at the default volatility | no test today; step 1 adds the guard. By the code, `Source/drifter/check.py:97-107` and `:199-209` | yes, by reading; step 1 proves it |
| Above volatility 1, a hand edit can be listed and `aligned` still true | `Source/drifter/check.py:100-103` and `TOLERATED` (`:131`); `tests/drifter/test_cli.py`, `test_volatility_decides_how_many_changes_count_as_drift` | yes |
| `drifter init` writes no `volatility` key, so a new repository is at Exact | `tests/drifter/test_cli.py`, `test_init_writes_four_canonical_files` (its `scope.json` bytes hold only `exclude` and `include`) | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| E07-1 | The two models hold the same table of writers | Done line 7 of the Epic: `git grep -h -A8 "^## Who writes /models" -- docs/diagrams/data-flow.md docs/diagrams/models-folder.md \| tr -d '\r' \| grep -vx -- "--" \| sort \| uniq -u` → prints nothing |
| E07-2 | A hand edit to `behavioral.json` that removes a state the code still makes is drift at the default volatility | `python -m pytest tests/drifter/test_cli.py -q -k hand_edit_to_behavioral` → `1 passed` |
| INV-2 | No author can change the ownership or scope rules to pass their own change. This Epic restates who edits those files and changes nothing about it | not changed: row stays DEFERRED in `docs/invariants/INVARIANTS.md`; `git diff --stat main...HEAD -- docs/invariants/` → empty |

# The models in this folder

Five models of the system, each a Markdown page that answers one question. Find the question you have, then open that page.

| Model | The question it answers | How to read it |
|---|---|---|
| `dependency.md` | Who reaches the drifter core, through which entry point, and which module may import which? | A flowchart of the callers, the entry points and the parts of the core. Below it, the module map: four layers, and an import points down. A dashed box is not built yet. |
| `data-flow.md` | If I change this step, what sees it downstream? | A flowchart of one check, from its two ways in to the answer. A solid arrow is data flowing during a check, a dotted arrow is a write into `/models`, a cylinder is something stored. The table "What sees a change" has one row per step. |
| `behavior.md` | What can happen to a request, and what does the user see? | A state diagram. The outer states are the lifecycle of a repository; the box inside is one `POST /system/analyze` run. The table "Every ending" gives the status code, what tells the ending apart and whether a run file is saved. |
| `models-folder.md` | Which four files does `/models` hold, and what does each contain? | A class diagram used as a file listing: one box per file, one line per field or rule. |
| `model-seam.md` | What does each generator write, and what does the core do with it? | A flowchart of one check as the generators and the core share it, with the rule every element of a model follows. |

The first three are the system models: the same system seen as its parts, its data and its behavior. The last two describe the format of `/models`.

## How much a model counts

Every model in this folder is level 6 of the authority order in `CLAUDE.md`: below the course PDF, the pod contract, the rulings, the invariants and the spec (`docs/base/specifications.md`), and above the current Epic. Where a model and the spec disagree, the spec wins and the model is fixed in the same change. A change to a part, a flow or a run state updates its model in the same PR (rule R6).

`data-flow.md` and `behavior.md` are drawn from the code: each ends with a table, "Premises, verified", that names the source line of every state, status code and limit. When one of those lines changes, the table says which drawing to check.

## What is not here

- **The cross-team test session:** which calls a tester makes, in what order, and how a drift test is graded. `docs/contract/pod-contract.md` defines it, and it ranks above these models.
- **The formats of the model files in detail:** `docs/base/structure.md` and `docs/base/behavioral.md`.
- **Who owns what.** No model in this folder names who owns a file or a folder.

## Drawing rules

Each page holds at most one Mermaid block, which is the only copy of its diagram; GitHub draws it. `tests/docs/test_diagrams.py` checks that the block carries `accTitle` and `accDescr`. `python docs/diagrams/render.py` makes a PNG of every page, or of the pages named, for a report or a slide; the PNGs are not committed. The rules for drawing are in `docs/agents/modeling.md`.

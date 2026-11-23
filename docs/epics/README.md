# Epics

An Epic is one planned change: a goal, steps that each carry a check, and Done criteria that are commands. This folder holds the live Epics. A finished Epic moves to `docs/closed/`.

**Build only from a live, ratified Epic.** A closed Epic is history: its steps describe the repository as it was. To change something a closed Epic built, open a new Epic and name the closed one under Relies on.

**A small change needs no Epic.** A change that touches no boundary, no invariant and no model in `docs/diagrams/`, and only a handful of files, is committed to a branch with any other name and pushed; CI runs on the push, and once it is green the change goes to `main` on the human's word, with no pull request. Epic work gets one pull request, opened when its last step is committed, before the audit, and merges through it. Any change gets a pull request when another person's approval or review is needed. RATIFY, the audit and the `Step:` trailer apply only to Epic work.

## Naming

- **Folder:** `docs/epics/E<nn>-slug/`. `<nn>` is two digits, one above the highest number in `docs/epics/` and `docs/closed/` together, so a number is used once. The slug is lowercase words joined by hyphens.
- **Files:** `EPIC.md`, copied from `docs/templates/EPIC.md`. `DESIGN.md` sits beside it only when the Epic changes a boundary, an invariant or a model in `docs/diagrams/`.
- **Branch:** `E<nn>-slug`, the folder's name. All work on the Epic happens on it.
- **W-row:** the Epic and its row in `docs/state/WORK-ITEMS.md` name each other. The Epic's header carries the W-id. The row carries the path to `EPIC.md` in its Epic column.

## Lifecycle

The Status line of `EPIC.md` says where the Epic is.

1. **draft.** Copy the template and fill every section. Drafting commits carry the trailer `Step: plan`. Done when the filled-copy check in `docs/templates/README.md` prints nothing and every step has one check command.
2. **Review.** The design reviewer (`.claude/agents/design-reviewer.md`) runs as a fresh subagent, never in the session that drafted the Epic. It first settles each open question that the code, the models or a ruling can answer, and cites the source. Each question that is left gets a row in `docs/decisions/OPEN-DECISIONS.md`. Then it writes RATIFY or REVISE with its findings in the Epic's Review section. With RATIFY it sets `Status: ratified`.
3. **ratified.** Code starts here, after RATIFY. Build one step at a time: run the step's check, then commit with the step's trailer, `Step: i/N`.
4. **closed.** The auditor (`.claude/agents/auditor.md`) re-runs every Done criterion and reports. When the human accepts, one closing commit, with the trailer `Step: close`, does three things: `git mv docs/epics/E<nn>-slug docs/closed/E<nn>-slug`, sets `Status: closed`, and marks the W-row done with the new path. Everything the Epic wrote is kept, and a later edit under `docs/closed/` needs the human's approval.

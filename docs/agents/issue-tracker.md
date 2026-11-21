# Issue tracker: Epics in this repository

Specs and tickets for this repo live as files in the repo, not as GitHub issues.

- **The queue** is `docs/state/WORK-ITEMS.md`: one W-row per item. It wins over any other list.
- **A spec** is an Epic: `docs/epics/E<nn>-slug/EPIC.md`, copied from `docs/templates/EPIC.md`.
- **A ticket** is one Step in an Epic: its files, its one check command and its `Step: i/N` trailer.

`docs/epics/README.md` holds the naming and the lifecycle (draft, review, ratified, closed). This file only maps what a skill asks for onto them.

## Conventions

- **Create a spec**: copy `docs/templates/EPIC.md` to `docs/epics/E<nn>-slug/EPIC.md` and fill every section except Review, which the design reviewer writes. `<nn>` is one above the highest number in `docs/epics/` and `docs/closed/` together. Name the Epic's W-row in its header, and put the Epic's path in that row's Epic column.
- **Read a spec**: open its `EPIC.md` with the Read tool. From a W-id, follow the row's Epic column.
- **List open specs**: `git ls-files "docs/epics/*/EPIC.md"`. The Status line of each says where it is.
- **Create a ticket**: add a Step block to the Epic's Steps section and renumber `i/N`. Only while the Epic is a draft: a ratified Epic's steps change only through a new review.
- **Blocking**: inside an Epic, steps run in order, so a step is blocked by the one before it. Between items, the W-row's **Depends on** column names the blockers.
- **Comment**: a question goes under the Epic's Open questions. A review finding goes under Review, written by the design reviewer.
- **A call that is the human's**: a row in `docs/decisions/OPEN-DECISIONS.md` (rule R1). Do not answer it in the Epic.
- **Close a ticket**: run the step's check, then commit with its `Step: i/N` trailer. The commit is the record.
- **Close a spec**: the closing commit in `docs/epics/README.md`: the folder moves to `docs/closed/`, the Status becomes closed, and the W-row is marked done with the new path.

A small change needs no Epic: one that touches no boundary, no invariant and no model in `docs/diagrams/` goes straight to a PR.

## Labels

The triage labels in `docs/agents/triage-labels.md` are GitHub labels, so they do not apply to an Epic. An Epic's Status line carries its state, and the W-row's Tier says whether an agent or the human does the item.

## GitHub Issues are optional

An issue is never required. If one exists, it links to its W-row, and `docs/state/WORK-ITEMS.md` wins where the two disagree. Creating or editing an issue is a remote write: `gh api` prompts the human, and nothing is written to GitHub without the human's explicit OK.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create `docs/epics/E<nn>-slug/EPIC.md` as in **Create a spec** above, with `Status: draft`. Do not create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Read the Epic as in **Read a spec** above, and take the Step the work is on. If the item has no Epic, its W-row in `docs/state/WORK-ITEMS.md` is the ticket.

## Wayfinding operations

Not mapped. `/wayfinder` keeps a map issue with child issues on GitHub, and this repo has no equivalent in files.

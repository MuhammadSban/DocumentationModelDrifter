# E<nn>: <title>

Status: <draft | ratified | closed; a new copy is draft> · Owner: <name>

W-row: <W-id> in `docs/state/WORK-ITEMS.md` · Branch: `E<nn>-slug`

## Goal

<One paragraph: what is different on disk when this Epic closes, and who needs it. One Epic, one outcome.>

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: <each `docs/diagrams/` file, marked "reads" or "changes">
- Rulings: <each `RULED/` id it reads>
- Invariants: <each INV id, marked "reads" or "changes">

## Steps

One commit per step, made after the step's check passes.

### Step 1/<N>: <verb and object>

- Files: <every path this step touches>
- Check: `<one command>` → <the output that means the step is done>
- Trailer: `Step: 1/<N>`

<Repeat the block for each step, 2/N to N/N.>

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → every spec line this Epic made wrong is in the diff; empty when the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E<nn>" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. <what must hold>: `<command>` → <expected output>

## Open questions

<Each question the draft could not answer, one per line. After review, each line ends with its answer and the source that settles it (a `file:line`, a model or a `RULED/` id), or with the ID of its row in `docs/decisions/OPEN-DECISIONS.md`.>

## Review

<Written by the design reviewer: RATIFY or REVISE · reviewer · date, then the findings, each citing its source.>

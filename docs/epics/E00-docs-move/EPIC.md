# E00: Move the docs by purpose

Status: draft · Owner: Kaan

W-row: W2-5 (build order step 0.2a) in `docs/state/WORK-ITEMS.md` · Branch: `docs/mage-env-prep`

An example, written after the fact on 2026-11-20 to show a filled template. The three steps were already committed, on a branch that predates the `E00-docs-move` naming, and their commits carry no `Step:` trailer.

## Goal

Every file that was under `docs/deviations/` or `docs/tickets/` sits in a folder named for its purpose (`research/`, `proposals/`, `decisions/` or `state/`), with its git history intact. `docs/README.md` lists every file under `docs/` with a "read it when" line, and `docs/decisions/OPEN-DECISIONS.md` indexes the calls awaiting the human. Agents need it: the files written after this (the templates, `CLAUDE.md`, the role files) cite final paths and are never rewritten for a move. Structure only: no file's meaning changes.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: none read or changed. Step 2 fixes one old path inside `docs/diagrams/file-fetch.md`; the model it draws is untouched, so this Epic has no `DESIGN.md`.
- Rulings: none. `docs/decisions/RULED/` does not exist until step 0.2b creates it.
- Invariants: none. `docs/invariants/INVARIANTS.md` arrives with W2-1 (step 0.4b).

## Steps

One commit per step, made after the step's check passes.

### Step 1/3: Move the files, and nothing else

- Files: all 23 files of `docs/deviations/` and `docs/tickets/`, to `docs/research/`, `docs/proposals/`, `docs/decisions/` and `docs/state/`
- Check: `git diff --diff-filter=r --name-status -M 32fd0ec~1 32fd0ec` → prints nothing: every change in the commit is a rename
- Trailer: `Step: 1/3` (commit `32fd0ec`)

### Step 2/3: Fix the old paths, write the docs map and the open-decisions index

- Files: `docs/README.md`, `docs/decisions/OPEN-DECISIONS.md` (new), `docs/history/deviations-review-2026-11-05.md` (new, cut out of the queue), `docs/state/WORK-ITEMS.md`, and the six files that named an old path: `docs/diagrams/file-fetch.md`, `docs/history/contract-2.4.0-changes.md`, `docs/proposals/language-engine/research-template-engine.md`, `docs/proposals/ownership/owner-approval.md`, `docs/research/industry-architecture-research.md`, `docs/research/mage_take.md`
- Check: `python -c "import subprocess,pathlib;m=pathlib.Path('docs/README.md').read_text(encoding='utf-8');print([f for f in subprocess.check_output(['git','ls-files','docs'],text=True).split() if f[5:] not in m and f!='docs/README.md'])"` → `[]`: no file under `docs/` is missing from the map
- Trailer: `Step: 2/3` (commit `d20e82f`)

### Step 3/3: Reconcile the queue's rows with the build order

- Files: `docs/state/WORK-ITEMS.md`
- Check: `git grep -c "Step 0.2a done" -- docs/state/WORK-ITEMS.md` → `docs/state/WORK-ITEMS.md:1`: the W2-5 row records step 0.2a as done
- Trailer: `Step: 3/3` (commits `5bb3d0a` and `e14a5ac`: the row-by-row comparison took a second pass)

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: no workflow exists until W1-6 (step 0.5) lands, so the template's `gh run list` line has nothing to read. Stand-in: `python -m pytest -q` → every test passes
2. Spec lines updated: `git diff --stat 2f29021 e14a5ac -- docs/base/specifications.md` → prints nothing: the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E00" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The old folders are gone: `git ls-files docs/deviations docs/tickets` → prints nothing
6. Every file under `docs/` is in the docs map: the check of step 2 → `[]`
7. A moved file keeps its history: `git log --follow --format=%h -- docs/state/WORK-ITEMS.md` → the list reaches `8d9ff5f`, three commits before the move `32fd0ec`

## Open questions

- Does `docs/adr/` move with the rest? No. `docs/contract/mapping-v1.1.yaml:30` classifies `docs/adr/**` as DESIGN, so a move would change what Team 16's rules see.
- Does this Epic file the D9 ruling under `docs/decisions/RULED/`? No. Only the human writes there; it is step 0.2b (W2-5 row, `docs/state/WORK-ITEMS.md`).
- Can "no link points to a moved path" be a Done criterion? Not one that re-runs. The link check ran once after step 2 and found nothing, and its script was not kept (W2-8 row). If a broken path turns up again, W2-8 adds the check to CI.
- Can "no row contradicts the build order" be a command? No. The build order is a planning page kept outside this repository; step 3 compared it by hand, row by row (`5bb3d0a`, `e14a5ac`).
- The title of `docs/proposals/language-engine/README.md` still says "Deviations". Left as it is: a rename of a title is outside "structure only". The W2-5 row records it as still open; it is a small change and needs no Epic.

## Review

No verdict. The steps were committed before this file and before the design reviewer role (W2-6, step 0.4b) existed, so nobody wrote RATIFY ahead of the work. That is the one way this example differs from a live Epic, where RATIFY stands here before step 1. The Status stays `draft` until the human accepts; the closing commit then moves this folder to `docs/closed/E00-docs-move/`.

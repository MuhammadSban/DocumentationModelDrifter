# E01: The module map and its import check

Status: draft · Owner: Kaan

W-row: W1-5 (build order step 0.6a) in `docs/state/WORK-ITEMS.md` · Branch: `E01-module-map`

## Goal

`docs/diagrams/who-talks-to-what.md` is renamed `docs/diagrams/dependency.md` and carries the module map: four layers, the allowed calls, each package's public names and an owner on each box. A new `.importlinter` states the same map as four contracts, and `lint-imports` runs as a blocking step of `.github/workflows/ci.yml`, so a PR that adds an import against the map turns red. The two imports that break the map today are listed as baseline ignore lines. Agents and the team need it: rule R5 stops being guidance and becomes a check. No file under `Source/` changes. The design is `DESIGN.md`, beside this file.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/who-talks-to-what.md`, changes (renamed `dependency.md`, then extended). `docs/diagrams/model-seam.md`, reads (the owners of D9).
- Rulings: none. `docs/decisions/RULED/` holds only its README.
- Invariants: INV-3, changes (new: imports follow the module map). INV-1, reads (no source file changes, so the answers cannot).

## Steps

One commit per step, made after the step's check passes.

### Step 1/7: Rename the model and fix every reference to the old name

- Files: `docs/diagrams/who-talks-to-what.md` to `docs/diagrams/dependency.md` with `git mv`, its content untouched; `CLAUDE.md` (the level 6 line and R5, the file name only); `docs/README.md` (the path only)
- Check: `git grep -n "who-talks-to-what" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/epics/E01-module-map"` → prints nothing
- Trailer: `Step: 1/7`

The file's own content does not change in this commit, so git records a pure rename. Two rows of `docs/state/WORK-ITEMS.md` keep the old name on purpose: W1-5 describes this rename, and W2-1 records what R5 said on 2026-11-21.

### Step 2/7: Extend the model with the module map

- Files: `docs/diagrams/dependency.md` (three new sections, as in `docs/templates/DESIGN.md`: Intended structure, Premises verified, Must stay true, filled from `DESIGN.md`); `docs/README.md` (the line that describes the file)
- Check: `git grep -c -E "^## (Intended structure|Premises, verified|Must stay true)" -- docs/diagrams/dependency.md` → `docs/diagrams/dependency.md:3`
- Trailer: `Step: 2/7`

The existing diagram stays the file's one Mermaid block. The map is tables.

### Step 3/7: Write the contracts

- Files: `.importlinter` (new)
- Check: `PYTHONPATH=Source lint-imports` → ends with `Contracts: 4 kept, 0 broken.`
- Trailer: `Step: 3/7`

The file is the four contracts of `DESIGN.md`, "The contracts", with the two ignore lines of its Baseline table and one comment above each. `unmatched_ignore_imports_alerting` is not set. For this step's check, `import-linter==2.17` is installed by hand; step 4 adds it to the requirements.

### Step 4/7: Install the linter and run it in CI

- Files: `requirements-dev.txt` (`import-linter==2.17`); `.github/workflows/ci.yml` (one step after `ruff check`: `run: lint-imports` with `env: PYTHONPATH: Source`); `.gitignore` (`.import_linter_cache/`, which a local run creates)
- Check: `pip install -q -r requirements-dev.txt && PYTHONPATH=Source lint-imports` → ends with `Contracts: 4 kept, 0 broken.`
- Trailer: `Step: 4/7`

### Step 5/7: Prove it red on a throwaway PR

- Files: `docs/state/WORK-ITEMS.md` (the W1-5 row records the PR number and the run id)
- Check: `gh run view $(gh run list --branch proof/lint-imports-red --limit 1 --json databaseId --jq ".[0].databaseId") --json jobs --jq ".jobs[0].steps[] | select(.conclusion==\"failure\") | .name"` → `Run lint-imports`, and no other line
- Trailer: `Step: 5/7`

A branch `proof/lint-imports-red`, cut from this one, adds one line to `Source/drifter/check.py`: `from GitHub_Connector import settings  # noqa: F401`, among the imports at the top. The `noqa` keeps `ruff` green, so the only failing step is `lint-imports`. A PR from that branch to `main` runs CI, turns red, is closed without merging, and its branch is deleted. The push, the PR and the close are remote writes: each waits for the human's OK. Nothing from that branch reaches this one.

### Step 6/7: Grade the rule

- Files: `docs/invariants/INVARIANTS.md` (a new row, INV-3, at ENFORCED-PROVEN, citing step 5's run); `CLAUDE.md` (R5: its wording follows A1 to A6 of `DESIGN.md`, and its Check column names the `lint-imports` step instead of "guidance only")
- Check: `git grep -c "INV-3.*ENFORCED-PROVEN" -- docs/invariants/INVARIANTS.md` → `docs/invariants/INVARIANTS.md:1`
- Trailer: `Step: 6/7`

If the human holds step 5's push, this step waits with it: the row is not written at ENFORCED-PROVEN before the red run has been seen.

### Step 7/7: Drop the finished line from the strategy

- Files: `STRATEGY.md` (delete near-term line 1, W1-6, and renumber the rest)
- Check: `git grep -c "W1-6" -- STRATEGY.md` → prints nothing
- Trailer: `Step: 7/7`

The W1-5 line of `STRATEGY.md` goes with the closing commit, when this item closes.

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md docs/base/structure.md` → prints nothing: the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E01" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. Nothing cites the old name: the check of step 1 → prints nothing
6. The renamed file keeps its history: `git log --follow --format=%h -- docs/diagrams/dependency.md` → the list reaches `7f1ac0a`, the commit that first drew the diagram
7. The map has its three sections: the check of step 2 → `docs/diagrams/dependency.md:3`
8. The contracts pass with the baseline: `PYTHONPATH=Source lint-imports` → ends with `Contracts: 4 kept, 0 broken.`
9. The baseline is two lines: `git grep -c -e "->" -- .importlinter` → `.importlinter:2`
10. The linter is pinned: `git grep -n "import-linter" -- requirements-dev.txt` → `requirements-dev.txt:2:import-linter==2.17`
11. CI runs it with the path set: `git grep -c -e "lint-imports" -e "PYTHONPATH: Source" -- .github/workflows/ci.yml` → `.github/workflows/ci.yml:2`
12. A planted import turned CI red at the right step: the check of step 5 → `Run lint-imports`
13. The throwaway PR was closed, not merged: `gh pr list --state all --head proof/lint-imports-red --json state,mergedAt --jq ".[0]"` → `{"mergedAt":null,"state":"CLOSED"}`
14. The rule is graded: the check of step 6 → `docs/invariants/INVARIANTS.md:1`
15. No source or test file changed: `git diff --stat main...HEAD -- Source tests` → prints nothing
16. The strategy no longer lists W1-6: the check of step 7 → prints nothing

## Open questions

- Who owns `Frontend`? D9 names an owner for the core, the hosted service, the CLI, the tester and each model, and none for `Source/Frontend/` (`docs/base/phase4.md:58-61`). The map needs a label on that box.
- R5 or the W1-5 row? `CLAUDE.md:42` says `Tester` and `Frontend` may import `drifter`. The W1-5 row says `Tester` must not import `drifter` and `Frontend` must not import `drifter.check`. The draft follows the row (A4 and A5 of `DESIGN.md`) and rewords R5 in step 6.
- Does the `layers` contract list modules or packages? The draft lists modules, so that `drifter.cli` is an entry point above `drifter.check` and no service imports `GitHub_Connector.api`. The cost is in `DESIGN.md`, "Left out, on purpose": a new `GitHub_Connector` module must be added to the contract by hand.

## Review

Not reviewed yet. The design reviewer writes its verdict here.

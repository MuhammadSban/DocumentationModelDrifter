# E01: The module map and its import check

Status: ratified · Owner: Kaan

W-row: W1-5 (build order step 0.6a) in `docs/state/WORK-ITEMS.md` · Branch: `E01-module-map`

## Goal

`docs/diagrams/who-talks-to-what.md` is renamed `docs/diagrams/dependency.md` and carries the module map: four layers, the allowed calls, and each package's public names. A new `.importlinter` states the same map as five contracts, and `lint-imports` runs as a blocking step of `.github/workflows/ci.yml`, so a PR that adds an import against the map turns red. The two imports that break the map today are listed as baseline ignore lines. Agents and the team need it: rule R5 stops being guidance and becomes a check. No file under `Source/` changes. The design is `DESIGN.md`, beside this file.

**A departure from the W1-5 row and the build order, by the human's decision on 2026-11-21.** Both ask for an owner label on each box of the map, taken from seam decision D9. This Epic adds none: the map names no owners, for any file, folder or layer. Owner labels are hard to keep true, and the import check does not use them. The current Epic outranks the queue in the authority order of `CLAUDE.md`, so step 2 notes the departure in the W1-5 row.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/who-talks-to-what.md`, changes (renamed `dependency.md`, then extended).
- Rulings: none. `docs/decisions/RULED/` holds only its README.
- Invariants: INV-3, changes (new: imports follow the module map). INV-1, reads (no source file changes, so the answers cannot).

## Steps

One commit per step, made after the step's check passes.

**Revised on 2026-11-21, after steps 1 to 4 were committed.** The human asked that CI catch a new `GitHub_Connector` module nobody listed. That adds one step, now step 5, and one contract, so the Epic went back to draft for a fourth review. The commits of steps 1 to 4 (`90ce5bd`, `6af05eb`, `0120a9b`, `6c69c2e`) carry the trailers `Step: 1/7` to `Step: 4/7`, from when there were seven steps. Steps 5 to 8 carry the new numbers.

### Step 1/8: Rename the model and fix every reference to the old name

- Files: `docs/diagrams/who-talks-to-what.md` to `docs/diagrams/dependency.md` with `git mv`, its content untouched; `CLAUDE.md` (the level 6 line and R5, the file name only); `docs/README.md` (the path only)
- Check: `git grep -n "who-talks-to-what" -- . ":!docs/state/WORK-ITEMS.md" ":!docs/epics/E01-module-map"` → prints nothing
- Trailer: `Step: 1/7`, as committed before the revision

The file's own content does not change in this commit, so git records a pure rename. Two rows of `docs/state/WORK-ITEMS.md` keep the old name on purpose: W1-5 describes this rename, and W2-1 records what R5 said on 2026-11-21.

### Step 2/8: Extend the model with the module map

- Files: `docs/diagrams/dependency.md` (three new sections, named as in `docs/templates/DESIGN.md`: "Intended structure", "Premises, verified" and "Must stay true", filled from `DESIGN.md`); `docs/README.md` (the line that describes the file); `docs/state/WORK-ITEMS.md` (the W1-5 row notes that the map names no owners, by the human's decision on 2026-11-21)
- Check: `git grep -c -E "^## (Intended structure|Premises, verified|Must stay true)" -- docs/diagrams/dependency.md` → `docs/diagrams/dependency.md:3`
- Trailer: `Step: 2/7`, as committed before the revision

The existing diagram stays the file's one Mermaid block. The map is tables: the layers, the allowed calls, the public names, the contracts and the baseline. It names no owners. The opening sentence of `DESIGN.md`, "Intended structure", names the old file and is not copied: in the model that sentence says only that the diagram above is unchanged and the module map follows it, so Done line 5 still prints nothing.

### Step 3/8: Write the contracts

- Files: `.importlinter` (new)
- Check: `PYTHONPATH=Source lint-imports` → ends with `Contracts: 4 kept, 0 broken.` at this step's commit; 5 kept from step 5 on
- Trailer: `Step: 3/7`, as committed before the revision

The file is the first four contracts of `DESIGN.md`, "The contracts", with the two ignore lines of its Baseline table and one comment above each. `unmatched_ignore_imports_alerting` is not set. For this step's check, `import-linter==2.17` is installed by hand; step 4 adds it to the requirements.

### Step 4/8: Install the linter and run it in CI

- Files: `requirements-dev.txt` (`import-linter==2.17`); `.github/workflows/ci.yml` (one step after `ruff check`: `run: lint-imports` with `env: PYTHONPATH: Source`; its header comment on line 1, which says "runs pytest then ruff", is reworded to name the import check too); `CLAUDE.md` (the Commands line "The lint CI runs" gains `lint-imports` with `PYTHONPATH=Source`); `.gitignore` (`.import_linter_cache/`, which a local run creates)
- Check: `pip install -q -r requirements-dev.txt && PYTHONPATH=Source lint-imports` → ends with `Contracts: 4 kept, 0 broken.` at this step's commit; 5 kept from step 5 on
- Trailer: `Step: 4/7`, as committed before the revision

### Step 5/8: Make CI catch a connector module nobody listed

- Files: `.importlinter` (a fifth contract, `connector`: type layers, `containers` naming `GitHub_Connector`, line 1 `api`, line 2 the seven service modules joined by `:`, `exhaustive = true`, no ignore line, one comment above it); `docs/diagrams/dependency.md` (the contracts table gains the `connector` row and says five contracts; the sentence below it about `|` and `:` gains the sentence of `DESIGN.md` on what `exhaustive` does; the first bullet of "Left out, on purpose" says what `DESIGN.md` now says; the premise row with `4 kept` is reworded to "the first four contracts", and two new premise rows follow it; "Must stay true" says 5 kept and gains the connector row); `docs/README.md` (the line that describes `dependency.md` says five import contracts)
- Check: `PYTHONPATH=Source lint-imports` → ends with `Contracts: 5 kept, 0 broken.`
- Trailer: `Step: 5/8`

The comment above the `connector` contract does not quote the option's own text, so the second command of Done line 18 counts one line. The human accepts this step only if it adds no ignore line, the run prints 5 kept and 0 broken, and a scratch run with a new unlisted `GitHub_Connector` module fails. `DESIGN.md`, "Premises, verified", holds both runs. If any of the three fails, the step is dropped and the gap stays written down in `dependency.md`, as it is today.

### Step 6/8: Prove it red on a throwaway PR

- Files: `docs/state/WORK-ITEMS.md` (the W1-5 row records the PR number and the run id)
- Check: `gh run view $(gh run list --branch proof/lint-imports-red --limit 1 --json databaseId --jq ".[0].databaseId") --json jobs --jq ".jobs[0].steps[] | select(.conclusion==\"failure\") | .name"` → `Run lint-imports`, and no other line
- Trailer: `Step: 6/8`

A branch `proof/lint-imports-red`, cut from this one, adds one line to `Source/drifter/check.py`: `from GitHub_Connector import settings  # noqa: F401`, among the imports at the top. The `noqa` keeps `ruff` green, so the only failing step is `lint-imports`. A draft PR from that branch to `main`, titled as a throwaway that must not be merged, runs CI, turns red, is closed without merging, and its branch is deleted. The human sees the failing step's name and output before the close. The push, the PR and the close are remote writes: each waits for the human's OK. Nothing from that branch reaches this one.

### Step 7/8: Grade the rule

- Files: `docs/invariants/INVARIANTS.md` (a new row, INV-3, at ENFORCED-PROVEN, citing step 6's run); `CLAUDE.md` (R5, reworded as below); `docs/state/WORK-ITEMS.md` (the Done when column of the W3-3 row gains "drops the `Frontend.model_drift -> drifter.check` ignore line")
- Check: `git grep -c "INV-3.*ENFORCED-PROVEN" -- docs/invariants/INVARIANTS.md` → `docs/invariants/INVARIANTS.md:1`
- Trailer: `Step: 7/8`

R5's new row, which the human sees beside the old one before the edit:

- What it says: Imports follow the module map `docs/diagrams/dependency.md`, which `.importlinter` states as contracts. They point down through its four layers: entry points, services, core, generators. `drifter` and `models` import none of `GitHub_Connector`, `Frontend` and `Tester`. `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`. `Frontend` imports none of `GitHub_Connector`, `Tester` and `drifter.check`.
- Principle: own abstractions, unchanged.
- Check: `lint-imports` in CI (`.github/workflows/ci.yml`).

If the human holds step 6's push, this step waits with it: the row is not written at ENFORCED-PROVEN before the red run has been seen.

### Step 8/8: Drop the finished line from the strategy

- Files: `STRATEGY.md` (delete near-term line 1, W1-6, and renumber the rest)
- Check: `git grep -c "W1-6" -- STRATEGY.md` → prints nothing
- Trailer: `Step: 8/8`

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
8. The contracts pass with the baseline: `PYTHONPATH=Source lint-imports` → ends with `Contracts: 5 kept, 0 broken.`
9. The baseline is two ignored imports, one in each of two contracts: `PYTHONPATH=Source lint-imports --no-cache | grep -c "KEPT (1 ignored import)"` → `2`
10. The linter is pinned: `git grep -n "import-linter" -- requirements-dev.txt` → `requirements-dev.txt:2:import-linter==2.17`
11. CI runs the linter and it passes: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --json jobs --jq ".jobs[0].steps[] | select(.name==\"Run lint-imports\") | .conclusion"` → `success`
12. A planted import turned CI red at the right step: the check of step 6 → `Run lint-imports`
13. The throwaway PR was closed, not merged: `gh pr list --state all --head proof/lint-imports-red --json state,mergedAt --jq ".[0]"` → `{"mergedAt":null,"state":"CLOSED"}`
14. The rule is graded: the check of step 7 → `docs/invariants/INVARIANTS.md:1`
15. No source or test file changed: `git diff --stat main...HEAD -- Source tests` → prints nothing
16. The strategy no longer lists W1-6: the check of step 8 → prints nothing
17. W3-3 promises to drop its ignore line: `git grep -c "drops the .Frontend.model_drift -> drifter.check. ignore line" -- docs/state/WORK-ITEMS.md` → `docs/state/WORK-ITEMS.md:1`
18. Every connector module is listed, and the check for it is on: `PYTHONPATH=Source lint-imports --no-cache | grep -c "Every connector module has a layer KEPT"` → `1`, and `git grep -c "exhaustive = true" -- .importlinter` → `.importlinter:1`. That an unlisted module breaks the contract was shown on a scratch copy (`DESIGN.md`, "Premises, verified"); these two commands show at HEAD that the contract is kept and that the option is on

## Open questions

- Who owns `Frontend`? Withdrawn: the map names no owners. The human's decision on 2026-11-21 (see Goal). No row in `docs/decisions/OPEN-DECISIONS.md` and no ruling. Third review: holds on disk. The owner label is asked only by the W1-5 row (`docs/state/WORK-ITEMS.md:136`), at level 8, below this Epic. Its Done when column does not ask for owners, and nothing at levels 1 to 6 asks the module map for them. `docs/diagrams/model-seam.md:9-14` keeps its own owner table, which this Epic leaves unchanged.
- R5 or the W1-5 row? `CLAUDE.md:42` says `Tester` and `Frontend` may import `drifter`. The W1-5 row says `Tester` must not import `drifter` and `Frontend` must not import `drifter.check`. The draft follows the row (A4 and A5 of `DESIGN.md`) and rewords R5 in step 7. Answer: the row stands. The human's answer on 2026-11-21; step 7 holds R5's new wording, and the human sees the old and new wording before the edit. Second review: settled on disk. R5's own Check column defers to this step ("`lint-imports` in CI (step 0.6a)", `CLAUDE.md:42`), and W2-1 defines R5 as "imports follow `docs/diagrams/dependency.md` and `.importlinter`; W1-5" (`docs/state/WORK-ITEMS.md:165`), so the W1-5 row's contracts (`docs/state/WORK-ITEMS.md:136`) are R5's content.
- Does the `layers` contract list modules or packages? The draft lists modules, so that `drifter.cli` is an entry point above `drifter.check` and no service imports `GitHub_Connector.api`. The cost is in `DESIGN.md`, "Left out, on purpose": a new `GitHub_Connector` module must be added to the contract by hand. Answer: modules. The row's four layers (entry → service → core → generators, `docs/state/WORK-ITEMS.md:136`) split two packages across layers: `GitHub_Connector.api` is an entry point and the other `GitHub_Connector` modules are services, `drifter.cli` is an entry point and `drifter.check` the core (`Source/drifter/cli.py:15` imports `drifter.check`). A package-level line would put each pair in one layer, so the four layers can only be listed by module; the module-level draft runs `Contracts: 4 kept, 0 broken.` with the baseline (import-linter 2.17, re-run at `1714866`, and again at `685c160` by the second review). Fourth review: still modules. The cost has changed. With step 5's `connector` contract, CI now catches a new `GitHub_Connector` module that is missing from its lines; only line 2 of `layers` is still kept by hand (`DESIGN.md:82`). The exhaustive run and the planted `eighth.py` run were re-run at `812aaa0`.

## Review

RATIFY · design-reviewer at 0fef9ba · 2026-11-21

- The fourth review's blocking finding is fixed. Step 5's Files line now lists `docs/README.md`, so `docs/README.md:37` can say five import contracts. `docs/README.md:98` already says "the five import contracts" at `0fef9ba`. `git grep -n -E "(four|five) (import )?contracts"` outside this Epic finds only `docs/README.md:37` and `docs/diagrams/dependency.md:99`, and step 5 edits both. No other line in the repository says `4 kept` or that a new `GitHub_Connector` module goes unseen, except `dependency.md:121`, `:133` and `:143`, and step 5 lists all three.
- The three non-blocking findings are addressed. Step 5 adds the `exhaustive` sentence (`DESIGN.md:69`) and rewords the premise row at `dependency.md:133` to "the first four contracts" (`DESIGN.md:94`). Step 5's note keeps the option's text out of the comment, so Done 18 counts one line. Done 18 now says that the unlisted-module case is proven by the scratch run and that the two commands stand in for it at HEAD.
- The premises hold. I re-ran them at `0fef9ba` with import-linter 2.17 and `--no-cache`:
  - The committed `.importlinter` gives `Contracts: 4 kept, 0 broken.`, exit 0.
  - The scratch `exh.importlinter` is the committed file plus only the `connector` contract, with no ignore line (checked with `diff`). It gives `Contracts: 5 kept, 0 broken.`, exit 0. Done 9's grep counts `2`, and Done 18's first grep counts `1`.
  - `plant2` adds only `GitHub_Connector/eighth.py` (checked with `diff -rq`). It gives `Analyzed 28 files`, `Every connector module has a layer BROKEN`, `Contracts: 4 kept, 1 broken.`, exit 1, and the output names `GitHub_Connector.eighth`.
  - `git ls-files Source/GitHub_Connector` lists `api` and exactly the seven service modules.
- The other checks still hold at `0fef9ba`:
  - Since `812aaa0`, only `EPIC.md` and `docs/README.md:98` changed.
  - Step 1's grep prints nothing, `--follow` reaches `7f1ac0a`, and step 2's check prints `docs/diagrams/dependency.md:3`.
  - `requirements-dev.txt:2` reads `import-linter==2.17`.
  - `ci.yml:1` and `ci.yml:26-29` run `lint-imports` with `PYTHONPATH: Source`.
  - `CLAUDE.md:42` R5 still has the old wording, which step 7 changes. `CLAUDE.md:52` names `lint-imports`.
  - `git diff --stat main...HEAD -- Source tests docs/base/specifications.md docs/base/structure.md` prints nothing.
  - `OPEN-DECISIONS.md` has no `E01` row. `STRATEGY.md:21` is the only line that names W1-6.
  - The open questions' sources read as cited: `docs/state/WORK-ITEMS.md:136` and `:165`, `docs/state/WORK-ITEMS.md:184` (W3-3), `Source/drifter/cli.py:15` and `DESIGN.md:82`.
- The filled-copy check prints nothing for `EPIC.md` or `DESIGN.md`. Every step names its files, one check with its output, and its trailer. Every Done line apart from 4 is a command with an expected output. Nothing contradicts levels 1 to 6. `DESIGN.md` exists. All three open questions have sourced answers, and none needs a row.
- Not blocking: step 5's list of `dependency.md` edits names two edits only loosely. The first is the sentence above the contracts table (`dependency.md:99`, "four contracts"), which "says five contracts" covers. The second is the clause `DESIGN.md:116` adds to the "baseline only shrinks" row, "the same run ends with `Contracts: 5 kept, 0 broken.`", which "says 5 kept" covers. The builder should copy both from `DESIGN.md`.

Fourth review below, at `812aaa0`.

REVISE · design-reviewer at 812aaa0 · 2026-11-21

- Blocking, the only one: step 5 leaves `docs/README.md` saying four contracts. `docs/README.md:37`, which describes `dependency.md`, says "the four import contracts of `.importlinter`". Step 5 makes that untrue, and no step lists `docs/README.md`. `docs/README.md:98`, which describes this Epic's `DESIGN.md`, says "the four import contracts", which is already untrue at `812aaa0` (`DESIGN.md:59` says five). For RATIFY, step 5's Files line adds `docs/README.md` (lines 37 and 98: "four" becomes "five"). `git grep -n -E "four (import )?contracts" -- . ":!docs/epics/E01-module-map"` finds only these two lines and `docs/diagrams/dependency.md:99`, which step 5 already covers.
- The renumbering holds. Every step number in the Steps, the Done criteria, the Open questions and `DESIGN.md` points at the right step: the proof is step 6 (step 7, Done 12, `DESIGN.md:113`), the grading is step 7 (Done 14, the W3-3 promise at `DESIGN.md:78`, R5 at `DESIGN.md:105`, Open questions line 2), and the strategy line is step 8 (Done 16). The committed trailers read `Step: 1/7` to `Step: 4/7` on `90ce5bd`, `6af05eb`, `0120a9b` and `6c69c2e`, as steps 1 to 4 say.
- The new premises hold. I re-ran them at `812aaa0` with import-linter 2.17 and `--no-cache`:
  - On the committed `.importlinter`: `Contracts: 4 kept, 0 broken.`, exit 0.
  - On the scratch `exh.importlinter`, which is the committed file plus only the `connector` contract and no ignore line: `Every connector module has a layer KEPT`, `Contracts: 5 kept, 0 broken.`, exit 0. Done 9's grep counts `2`, and Done 18's first grep counts `1`.
  - With `plant2` (`diff -r` shows only `GitHub_Connector/eighth.py` added): `Analyzed 28 files`, `Every connector module has a layer BROKEN`, `Contracts: 4 kept, 1 broken.`, exit 1, and the output names `GitHub_Connector.eighth`.
  - With the step 6 plant and the five contracts: `Contracts: 3 kept, 2 broken.` (`layers` and `core`), exit 1, and the connector contract is unaffected.
  - In 2.17, `exhaustive` requires `containers` (`importlinter/contracts/layers.py:186-190` in the install). `git ls-files Source/GitHub_Connector` lists `api` and exactly the seven service modules.
- Steps 1 to 4 as committed match the revised Epic, and nothing in them contradicts it:
  - `.importlinter` holds four contracts with one comment above each ignore line.
  - `ci.yml:1` and `ci.yml:25-28` run `lint-imports` with `PYTHONPATH: Source`, so the step's name is `Run lint-imports` as Done 11 and 12 expect.
  - `requirements-dev.txt:2` reads `import-linter==2.17`.
  - `.gitignore` names `.import_linter_cache/`, and `CLAUDE.md:52` names `lint-imports`.
  - `CLAUDE.md:42` R5 is still the old wording, which step 7 changes.
  - Step 1's grep prints nothing, `--follow` reaches `7f1ac0a`, and step 2's check prints `docs/diagrams/dependency.md:3`.
  - `git diff --stat main...HEAD -- Source tests docs/base/specifications.md docs/base/structure.md` prints nothing.
  - `OPEN-DECISIONS.md` has no `E01` row.
  - `ci.yml:5-6` triggers on `pull_request` with no type filter, so a draft PR runs CI, as step 6 now asks.
- The filled-copy check prints nothing for `EPIC.md` or `DESIGN.md`. Every step names its files, one check with its output and its trailer. Every Done line apart from 4 is a command with an expected output. Nothing contradicts levels 1 to 6. All three open questions have sourced answers, and none needs a row.
- Not blocking: step 5's list of `dependency.md` edits leaves out two things. The first is the sentence that `DESIGN.md:69` adds about `exhaustive = true` (beside `dependency.md:108`). The second is the premise row at `dependency.md:133`, "the contracts pass" with `4 kept`. `DESIGN.md:94` words it "the first four contracts", and the model should say the same.
- Not blocking: Done 18's `git grep -c "exhaustive = true"` also counts a comment that contains the phrase. The comment above the `connector` contract should not quote it.
- Not blocking: the human's third condition, that a new unlisted module fails, is shown only by the scratch run in `DESIGN.md:96`, and the auditor cannot re-run it from the repository. Done 18's `exhaustive = true` line is the on-disk stand-in for it.

Earlier reviews follow. They use the step numbers of their time: seven steps, with the proof as step 5, the grading as step 6 and the strategy line as step 7.

RATIFY · design-reviewer at e6d800a · 2026-11-21

- Both of the human's fixes are in. Step 2 keeps the sentence at `DESIGN.md:7` out of the model (`EPIC.md`, step 2), so Done 5 can print nothing. Done 9 counts `KEPT (1 ignored import)` and no longer counts `->`.
- The departure on owners contradicts nothing above the Epic. The W1-5 row is level 8 (`CLAUDE.md:8-16`). Its Done when column asks for packages, public names and allowed callers, and no owners (`docs/state/WORK-ITEMS.md:136`). No level 1 to 6 document asks the map for owner labels (`git grep -i owner` over `docs/contract`, `docs/invariants`, `CLAUDE.md` and the model). `model-seam.md:9-14` is not touched. Step 2 records the departure in the W1-5 row. This question needs no row.
- The other two open questions are answered on disk. R5 against the row: `CLAUDE.md:42` (its Check column) and `docs/state/WORK-ITEMS.md:165` (R5 follows `dependency.md` and `.importlinter`). Layers by module: `Source/drifter/cli.py:15` imports `drifter.check`.
- Holds, re-run at e6d800a:
  - The filled-copy check prints nothing for `EPIC.md` or `DESIGN.md`.
  - import-linter 2.17 with `PYTHONPATH=Source --no-cache`. Without ignore lines: `Contracts: 2 kept, 2 broken.`, exit 1, naming `GitHub_Connector.api -> Tester.api (l.19)` and `Frontend.model_drift -> drifter.check (l.17)`. With the baseline: `Analyzed 27 files, 47 dependencies.`, `Contracts: 4 kept, 0 broken.`, exit 0. Done 9's grep counts `2`.
  - Step 1's grep finds exactly `CLAUDE.md:14`, `CLAUDE.md:42` and `docs/README.md:37`, and no test names the old file.
  - `git log --follow` on the model reaches `7f1ac0a`.
  - `requirements-dev.txt` has one line today, so Done 10's `:2:` holds.
  - `ci.yml:5-8` runs on `pull_request` and on push to `main` only, so the proof branch makes one PR run. `ci.yml:22-24` and the header at `ci.yml:1` read as cited.
  - `.claude/settings.json:12-13` prompts on `.importlinter` and `dependency.md`.
  - `STRATEGY.md:21` is the only line that names W1-6.
  - W3-3 is `docs/state/WORK-ITEMS.md:184` and does not yet hold the Done 17 text.
  - `git grep E01` over `OPEN-DECISIONS.md` prints nothing.
  - `.gitignore` does not yet name `.import_linter_cache/`, which step 4 adds.
  - `test_diagrams.py` allows one Mermaid block per file, and the model has one.
  - These cited lines read as claimed: `Source/GitHub_Connector/api.py:19`, `Source/Frontend/model_drift.py:17`, `Source/drifter/check.py:18` and `Source/Frontend/README.md:32`.
- Not blocking: the W1-5 row also asks that every ignore line's comment name its remover or say why it stays. No Done line checks that. The two comments in the scratch contracts do. The auditor can confirm it by reading `.importlinter`.

Second review below, at `685c160`.

Earlier reviews, kept as the record of what each revision answers. Where they discuss an owner for `Frontend`, the question has since been withdrawn.

REVISE · design-reviewer at 685c160 · 2026-11-21

- Blocking, the only one: the owner of `Frontend` has no sourced answer and no row. No code, model or ruling names one. D9 does not (`docs/base/phase4.md:58-61`, `docs/diagrams/model-seam.md:9-14`). "The human's answer on 2026-11-21" appears on disk only in this Epic and `DESIGN.md:28`, and a reviewer cannot treat a relayed answer as a source. `docs/epics/README.md:21` says each question left gets a row. For RATIFY, the human files the answer as a row in `docs/decisions/OPEN-DECISIONS.md` (R1) or as a `RULED/` file, and the Open questions line cites it. Before confirming, the human should see the authorship: `git log --format=%an -- Source/Frontend` gives MuhammadSban 8, Kaan Kanadasi 2, Enrique 0.
- Settled: R5 against the W1-5 row is answered on disk, so it needs no row. R5's Check column defers to step 0.6a (`CLAUDE.md:42`), and W2-1 defines R5 as following `dependency.md` and `.importlinter` from W1-5 (`docs/state/WORK-ITEMS.md:165`). The layers question was already sourced, and its run still holds.
- All six of the first review's findings are addressed: `private_modules` is in the premise (`DESIGN.md:97`), which matches `importlinter/application/use_cases.py:650-655` in the 2.17 install. Step 6 adds the W3-3 promise, and Done 17 checks it. Done 11 checks the `Run lint-imports` step's conclusion, not a line count. Step 4 rewords `ci.yml:1` and lists `CLAUDE.md:52`. Step 2 now says "Premises, verified". The `ui.py` note is at `DESIGN.md:30`, and `Source/Frontend/ui.py:3-11` imports none of the five packages.
- Holds: the filled-copy check prints nothing for both files. With import-linter 2.17 and `PYTHONPATH=Source`, the scratch contracts give `Analyzed 27 files, 47 dependencies.` Without ignore lines they give `Contracts: 2 kept, 2 broken.` (exit 1), naming `GitHub_Connector.api -> Tester.api (l.19)` and `Frontend.model_drift -> drifter.check (l.17)`. With the baseline they give `Contracts: 4 kept, 0 broken.` (exit 0). Also confirmed:
  - Step 1's grep finds exactly `CLAUDE.md:14`, `CLAUDE.md:42` and `docs/README.md:37`.
  - `git log --follow` reaches `7f1ac0a`.
  - `STRATEGY.md:21` is the only line that names W1-6.
  - `git grep E01` over `OPEN-DECISIONS.md` prints nothing.
  - W3-3 is `docs/state/WORK-ITEMS.md:184`.
  - `.claude/settings.json:12-13` makes `.importlinter` and `dependency.md` prompt.
  - `ci.yml:22-24` holds the install, `pytest` and `ruff check` steps.
  - `gh run list` has `--commit`.
  - The cache directory is `.import_linter_cache` (`importlinter/configuration.py:17`).
  - Ruff selects no isort rules (`pyproject.toml:26`), so the plant's `noqa: F401` keeps `ruff` green. `settings.py` needs only `pydantic_settings`.
  - Nothing in `docs/base/structure.md` or `specifications.md` is made untrue.
- Not blocking: `DESIGN.md:7`, the text step 2 fills the map from, names `who-talks-to-what.md`. Copied as it stands, it makes Done 5 fail. Step 2 should reword it, or its check should also run step 1's grep.
- Not blocking: Done 9 counts lines that contain `->`, so no comment in `.importlinter` may contain `->`. The scratch comments do not.

Second review above, at `685c160`.

First review, kept as the record of what the revision answers:

REVISE · design-reviewer at 1714866 · 2026-11-21

- Two open questions are the human's call and have no row in `docs/decisions/OPEN-DECISIONS.md`: the owner of `Frontend`, and R5 against the W1-5 row. For RATIFY each needs a row there, cited from its line under Open questions (R1). No code, model or ruling answers them. `docs/base/phase4.md:58` gives Kaan the "hosted service", and `docs/base/overview_phase4.html:1052` serves `/` and `/models/view` from `Source/Frontend/`, so Kaan is the likely owner, but D9 does not say so. `CLAUDE.md:42` and `docs/state/WORK-ITEMS.md:136` disagree, and neither is a ruling.
- A premise fails: import-linter 2.17 has six contract types, not five. `private_modules` is missing (`importlinter/application/use_cases.py:650-657` in the 2.17 install). Correct the premise row in `DESIGN.md:95`. Nothing else rests on it.
- The baseline table says `W3-3` removes `Frontend.model_drift -> drifter.check` (`DESIGN.md:75`), but nothing in W3-3 says it will. Its row only says `api.py` stops importing `Frontend` (`docs/state/WORK-ITEMS.md:184`). Either a step adds "drops the `Frontend.model_drift -> drifter.check` ignore line" to W3-3's Done column, or the ignore comment and the table name a step that does promise it.
- Done line 11 counts lines, so it breaks if the stale header comment `.github/workflows/ci.yml:1` ("runs pytest then ruff") is reworded to mention `lint-imports`: the count becomes 3. Step 4 must say whether that comment changes, and line 11 must match.
- Once step 4 lands, `CLAUDE.md:52` (the lint CI commands) leaves out `lint-imports`. Step 4 or step 6 should list that line under Files.
- Step 2's Files line names the section "Premises verified", but its check and the template say "Premises, verified" (`docs/templates/DESIGN.md:9`). Make the two the same.
- Not blocking: `Source/Frontend/ui.py:81-100` is a standalone entry point (`python Source/Frontend/ui.py`, `Source/Frontend/README.md:32`). The map puts it in Services under `Frontend` and still says there are three entry points (`DESIGN.md:17-21`, A2). One sentence in the map would cover it.
- Holds: the filled-copy check prints nothing for both files. `lint-imports` re-run with 2.17 gives `Analyzed 27 files, 47 dependencies.`, `2 kept, 2 broken` on the two baseline imports without ignore lines, and `4 kept, 0 broken` (exit 0) with them. The planted `drifter.check -> GitHub_Connector.settings` gives `2 kept, 2 broken` (exit 1). An unmatched ignore line fails with `No matches for ignored import`. Also confirmed: `Source/GitHub_Connector/api.py:19`, `Source/Frontend/model_drift.py:17`, `.claude/settings.json:12-13`, `.github/workflows/ci.yml:22-24`, `tests/docs/test_diagrams.py:20`, `docs/diagrams/model-seam.md:11-14`, `docs/base/phase4.md:58-61`, the `importlib` and `Tester` greps, that 2.17 is the newest release, that layers take no wildcard, that `unmatched_ignore_imports_alerting` defaults to error, that `7f1ac0a` is in `--follow` history, and that `STRATEGY.md:21` is the only line naming W1-6. Step 1's grep finds exactly `CLAUDE.md:14`, `CLAUDE.md:42` and `docs/README.md:37`. The plant keeps `pytest` green: `GitHub_Connector/__init__.py` is empty and `settings.py` needs only `pydantic_settings`, not the `fastapi` that `tests/drifter/test_cli.py:185` blocks. So `Run lint-imports` is the only red step.

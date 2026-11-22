# Review of `docs/deviations/`, 2026-11-05

History, not instructions. This was the appendix of the Phase 5 queue (`state/WORK-ITEMS.md`), split out when W2-5 moved the folder's files to `research/`, `proposals/`, `decisions/` and `state/`. The verdicts stand as written on 2026-11-05; only the paths were updated to where each file lives now. The W-item IDs refer to the queue.

Each document was judged on four questions: is it correct, is it sound, is it worth doing, and does it repeat or contradict another document.

## Per document

| Document | Verdict | Problems found |
|---|---|---|
| `proposals/docker/docker.md` | Correct and proportionate. R1 and R2 are standard and safe. The analysis of when to split containers is sound. | Context sizes (14 MB, under 2 MB) are not measured (W1-2 measures them). The Compose sketch needs `Tester.app`, which does not exist (it says so). |
| `proposals/init/init.md` | Problem 1 is **correct, reproduced**. Problem 2 is correct (no `scope.schema.json`). | Fix 1 covers G4: besides judging at the base, it flags any change to `ownership.json` or `scope.json` by a non-owner of `/models` (in effect S3). It misses G1 and G2, and assumes an owner of `/models` exists without creating one (G3) (W0-7). Line references move after W1-1. |
| `proposals/ownership/owner-approval.md` | The problem is real: authorship is not approval. Option 1 is sound. | Option 2 contradicts REQ-07 and `tracker-gaps.md` row 7 (CLI = `/analyze`). Option 1 lists owners twice (`ownership.json` and `CODEOWNERS`; W4-7). |
| `research/mage-engineering-env.md` | Careful and well sourced; separates the lecture from the notes. | §13 is a second to-do list, overlapping `mage_take.md` C1 to C9; both are now replaced by this file. §12's "pass status not checked" is now checked: 277 pass. §12's install and server commands are still unverified (W2-1). |
| `research/mage_take.md` | Sound and fair (grade B). Its facts in con 8 are confirmed. | Its to-do lists are replaced by this file. C7's base-rules fix has the same gaps G1 to G4. |
| `research/mage-research.md` | Good source map. | Mostly repeats `mage-engineering-env.md` (findings 7, 11 and 13 appear in both with the same lecture notes). W2-5 moves it to `docs/research/`; merging it into `mage-engineering-env.md` is a later, separate change. |
| `research/industry-architecture-research.md` | The strongest outside evidence. Honest labels; admits the evidence is thin. | Its pipeline adds `rules[]` to the answer, which contradicts `architecture-review.html` A and the spec's four-field answer. Putting `rules.json` in `/models` contradicts the spec's "four files". Both are now W5-4 decisions. |
| `research/architecture-review.html` | Concrete and well targeted. A and B are the most useful. | F duplicates the language engine's end state (W5-2). C needs the two code owners to agree (W3-5). |
| `research/mage-alignment.html` | A good visual explainer of MAGE chapter 3. | Restates `mage_take.md`. Raises one unverified edge: squash merges and per-commit authors (W0-7). |
| `proposals/language-engine/` (README, 01 to 06, `final_templates.md`, research, `guide.html`) | Thorough research and a sound engine design. | `05-decisions-log.md` D1 says "decided"; `mage_take.md` says hold. Resolved by Q3: Phase 5, later wave. 02's per-language adapters are replaced by 04; 02 already says so in a "Superseded in part" banner, and the README repeats it. The evidence is lost (W5-1). It is a contract change (O2) and a spec change, which the README states only indirectly. O5 and D6 were missing from the earlier version of this file (now in W5-3). |
| `STRATEGY.md` (root) | Raw lecture notes, not a queue. | "less than 50 lines" should be 50 characters; `prepush.sh` should be `pre-push`. Rewritten in W2-3. Its "name the target files in the first commit, step i/N" is now the brief convention (W2-4). |

## Repeated in more than one place

| Topic | Where | Resolution |
|---|---|---|
| The ownership self-grant fix | `proposals/init/init.md`, `proposals/ownership/owner-approval.md`, `mage_take.md` (con 5, C7), `industry-architecture-research.md` (item 2), `architecture-review.html` (C) | One decision (W0-7), one build (W3-5) |
| The CI plan | `mage_take.md` C1 to C9, `mage-engineering-env.md` §13, `mage-alignment.html` §3.5 | One suggestion (W1-6); the C9 rule is in W2-1 |
| The red-check tally | `mage_take.md` C8, `mage-engineering-env.md` §10, the old W4-4 | Owned by W1-6; W4-4 only tells adopters to keep their own |
| Explaining MAGE | `mage-engineering-env.md`, `mage-research.md`, `mage_take.md`, `mage-alignment.html`, `ExampleRepoMAGE/README.md` | Merge the two research files in a later, separate change, after W2-5 moves them; keep the HTML as the visual |
| Phase 5 to-do lists | `mage_take.md`, `mage-engineering-env.md` §13, `STRATEGY.md` | This file. `STRATEGY.md` points here after W2-3 |
| `CODEOWNERS` | `proposals/init/init.md` fix 2, `owner-approval.md` Option 1, `mage_take.md` C7 and suggestion 1 | Q4 option S4 (W0-7); the match test is W4-7 |

## Contradictions

| Between | Contradiction | Settled by |
|---|---|---|
| `proposals/language-engine/05-decisions-log.md` D1 and `mage_take.md` con 9 | Build 14 languages now, or hold until Python shows a return | Q3: Phase 5, later wave (W5-3) |
| `industry-architecture-research.md` and `architecture-review.html` A | A rule violation adds a `rules[]` list to the answer, or the answer stays as the contract fixes it | Open, W5-4 |
| `industry-architecture-research.md` item 3 and spec §3.2 | `models/rules.json` as a fifth file, or "/models holds four files" | Open, W5-4 (contract and spec change) |
| `architecture-review.html` F and `proposals/language-engine/final_templates.md` | F is speculative, or the language engine's end state is built on it | W5-2: build it once, as part of the language engine |
| `proposals/ownership/owner-approval.md` Option 2 and REQ-07 / `tracker-gaps.md` row 7 | Network-dependent verdicts, or the same answer from the CLI and `/analyze` | Rejected (W0-7) |
| The deviations' "judge at the base" and golden case L0 | Strict base rules fail the first commit with `/models` | Gap G1 (W0-7) |
| `docker.md` "keep one container in Phase 5" and Q9 | The tester split was a signal-triggered item | The user put it in Phase 5 (W3-6). Reversed 2026-11-09 after a review and a second, independent review: one container in Phase 5, W3-6 waits for its signal, W3-7 is Phase 6, W1-7 guards `/tester/unit` |
| `STRATEGY.md` "the agent names its files, step 3/k" and a strict `commit-msg` hook | Enforce step counts on every commit, or only in briefs | W2-4 owns the convention; W2-2 checks the format only when present |
| The folder name `docs/deviations` and contract §9 | "Deviation" means two different things | W2-5 |

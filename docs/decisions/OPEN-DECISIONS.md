# Open decisions

**Awaiting the human, do not guess these.** Each row is a call only the human can make. An agent that meets one stops and cites the row; it does not pick an option.

An index only: the detail stays in the file each row names. Paths are relative to `docs/`.

- **Row format:** ID · Question · Options + recommendation · Epic · Blocks · Since.
- **Adding a row.** The design reviewer settles what it can first; only what is left gets a row.
- **Ruling on a row.** The human moves it to `decisions/RULED/`. Agents never write there. After that, agents cite the ruling.

## The self-grant hole

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| W0-7 | How is the ownership and scope self-grant hole closed, including gaps G1 to G4? | S1 rules from the base, S2 rules from each commit's parent, S3 flag every rules change, S4 GitHub enforces it. Recommended, not decided: S1 + S4. Detail: `state/WORK-ITEMS.md`, "W0-7 in detail". | none yet | W3-5, W4-1, W4-7 | 2026-11-05 |

## The CLI's exit codes

Found while planning build order step 0.6b. Detail: the design doc of the system-models Epic, "Where the code and the build order disagree", last row. The row is not that Epic's to settle, so it does not carry its number.

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| CLI-1 | Is it a defect that `drifter check`, `init` and `update` end with a traceback and exit 1 on a git failure, such as an unknown commit or a folder that is no checkout? Exit 1 is also the code for drift, and spec AC-08 gives exit 2 to a check with no verdict. | 1: leave it. 2: catch the git failure, print a one-line message and exit 2. Recommended: 2, as a small change with a failing test first. | none yet | nothing yet | 2026-11-21 |

## Contract 2.5.0

Found by the design review of E04. Detail: `epics/E04-contract-2-5-0/EPIC.md`, open question 3 and Review.

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| E04-1 | How do the code and commits of W4-5 (step 5.6) and W4-10 (step 5.7) reach E04's branch and its one pull request? R7 and `epics/README.md` build code only from a live, ratified Epic, on that Epic's own branch, with that Epic's `Step:` lines. | 1: each gets its own Epic and branch, cut from `E04-contract-2-5-0`, and merges into it before E04's pull request opens. 2: E04 is revised (`Step: plan`, a new review) to add their steps. 3: E04 merges on its own once Team 16 agrees, and W4-5 and W4-10 follow under the same version 2.5.0; this drops "for the merge" from the W4-9 row. Recommended, not decided: 1. | E04 | E04's Done line 12 and its pull request | 2026-11-22 |

## Not yet in a wave

Detail for each: `state/WORK-ITEMS.md`, "Not yet discussed".

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| N1 | Do we run the Risk 1 (noise) and Risk 2 (behavioral coverage) experiments, and when? | Run them and report counts, method and limits, or leave the spec's benefits as goals. No recommendation yet. | none yet | N2, the wording in W0-5 | 2026-11-05 |
| N2 | What happens to the behavioral model, which finds 0 states on this repository and so always passes? | Keep the miner; drop it; or turn it into an authored state model checked against mined transitions or test traces. No recommendation until N1 reports. | none yet | nothing yet | 2026-11-05 |
| N3 | Which grain does the structural model have? | Module, class or function level; drop `params` and `decorators`; leave out private symbols; finer grain as an opt-in in `scope.json`. No recommendation until the W1-6 tally has data. | none yet | N4 | 2026-11-05 |
| N4 | Do ids stay stable when a file moves? | Keep path-based ids (a move shows as REMOVED plus ADDED), or design move-stable ids. Waits for N3. | none yet | nothing yet | 2026-11-05 |
| N5 | Do we record the generator version beside `schema_version`? | Yes or no. No recommendation yet. | none yet | nothing yet | 2026-11-05 |
| N6 | Do we measure the factory (cost and latency of accepted changes, reverts, post-deploy failures)? | Yes or no, and who keeps the numbers. No recommendation yet. | none yet | nothing yet | 2026-11-05 |

## Language engine

Detail for each: `proposals/language-engine/05-decisions-log.md`. All of them block W5-3.

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| O1 | How are duplicate ids from overloading, Rust trait methods and Ruby redefinition resolved? | Proposed: parameter types in the id only for overloaded names, keep-last for redefinition, the trait in the id for Rust. | none yet | W5-3 (language waves 2 and 3) | 2026-11-02 |
| O2 | Does the answer gain the "partly read" list that `skip` adds? | Add it or not. A pod contract change, so Team 16 must agree. | none yet | W5-3 | 2026-11-02 |
| O3 | Do C#, Swift and Go get import edges? | Leave them without edges, or add a `package` node kind (a schema change). No recommendation yet. | none yet | W5-3 | 2026-11-02 |
| O4 | Is there a behavioral model for the new languages? | Not prototyped. Suggested first language: TypeScript or Java. | none yet | W5-3 | 2026-11-02 |
| O5 | Do Python edges on the template match today's? | Not compared yet. The gate of step b, before step c moves Python structural. | none yet | W5-3 (step b) | 2026-11-02 |
| D6 | Are Elixir, Haskell, Julia and Zig in or out? | In or out, per language. No recommendation yet. | none yet | W5-3 | 2026-11-02 |

## Open contradictions

Detail for each: `decisions/contract-contradictions.md`, by ticket number.

| ID | Question | Options + recommendation | Epic | Blocks | Since |
|---|---|---|---|---|---|
| Ticket 3 | Does Team 16's tester accept the extra keys `drift` and `drift_error`? | Ask Team 16 which schema their tester validates against; if v1.1, they switch to ours. | none yet | nothing yet | 2026-10-31 |
| Ticket 4 | Will Team 16 fix their OpenAPI wording for `unmapped`? | Ask Team 16 to match their SPEC §6.1. | none yet | nothing yet | 2026-10-31 |
| Ticket 5 | Our `issues` is always `[]`, so our answers differ from Team 16's goldens. Is that acceptable to a grader? | 1: implement the v1.1 prose detector. 2: keep deviation 1 and add the grader line to contract §8. Recommended: 2 (W0-3, skipped for now). | none yet | W0-3 | 2026-10-31 |
| Ticket 11 | Should a test send `c5-docs-only`? | Ask Team 16 whether their tester sends it; if yes, add T-34. | none yet | nothing yet | 2026-10-31 |

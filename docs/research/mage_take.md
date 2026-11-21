# What MAGE would think of this project

A review of DocumentationModelDrifter against James C. Davis, *MAGE: Model-Based Agentic Engineering* (1st ed., 2026), the method the spec cites as [3]. Written 2026-11-02; CI section updated 2026-11-05 for the course lecture "Building with Agents" (<https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/>).

This file holds the project's to-do list (suggested changes, and the CI plan C1–C9). `mage-engineering-env.md` §13 ranks the same gaps from the engineering-environment side and points here.

**Method.** The book was read first, concentrating on the method, glossary, §2.5–2.6 (correspondence), Ch. 3 (Alignment), §4.1 and §4.3 (dynamics, brownfield), App. D.8–D.9 (brownfield drill), §6.3 (scope conditions) and App. G.3 (DocAble's own drift evidence). Three independent reviewers then judged the repo against it: an advocate, a skeptic and an objective assessor. Their disputed claims were checked against the repo before this summary was written. References to the book are by section; references to the repo are by path.

## Verdict

**Grade: B.** This is sound, MAGE-literate engineering, but it is a well-built *sensor and validator* with a governance plan that exists only on paper.

- **It reads MAGE correctly in its main choices.** It uses the *derive* pattern on purpose: the code owns the truth, so the models are re-derived. It treats ownership as an authored rule rather than a regenerated model. It keeps humans responsible for accepting drift. It runs no LLM at runtime.
- **It has real depth.** It has byte-determinism, honest no-verdict codes, measured design decisions, a negotiated cross-team contract and 277 passing tests.
- **By the book's own test, it governs nothing yet.** No gate is wired anywhere, the repo does not run the tool on itself, and the structural and behavioral checks compare the code against an older snapshot of the same code, not against any stated obligation.

All three reviewers agreed on that shape. They disagreed on how much the missing pieces matter.

It is **not** "lacking depth" or "not sound". It **does** make sense for agentic workflows: the problem it targets, silent architecture changes made faster than people can review, is exactly the one the book describes. The gap is narrower and more specific. The tool can say "the architecture changed", but not yet "the architecture is wrong", and nothing yet acts on what it says.

## What MAGE is (the short version)

MAGE asks: *how do we safely grant autonomy to commodity intelligence?* When agents make implementation cheap, the scarce resources become judgment, representation, evidence and enforcement. The method has two principles and a loop:

1. **Modeling.** Make consequential knowledge explicit in *purposeful* models, each a reduction that answers one engineering question. There are six classes: structural, behavioral, ownership, decision, measurement and provenance.
2. **Alignment.** Enforce selected obligations through mechanisms with four roles: constraint, sensor, validator and gate. Place each at the *earliest boundary where the obligation is legible and decidable*.
3. **Governance conversion.** When a failure or a recurring judgment exposes a gap, encode the lesson in durable structure. Structure that keeps paying off is *engineering capital*. Capital also depreciates, so price its upkeep.

Four passages bear directly on a drift tool:

- **§2.5, three correspondence patterns.** "Derive when implementation owns the truth … The drift check is a reconciler -- it re-derives the model from the code and fails on divergence." This is the project's pattern.
- **§3.2, "Agreement Is Not Correctness".** "A drift check can establish a declared correspondence between two artifacts. It cannot establish that the correspondence expresses the right intent … A model extracted from code can supply the current *is*; an independently authored invariant can supply the governing *ought*. … Enforcement requires something against which the work can actually be wrong."
- **§3.2, on gating.** "A validator should not receive more gating power than its evidence surface warrants."
- **§3.4, "Correct judgment without enforcement".** A warning that correctly detects danger but blocks nothing is a failure of enforcement. Temporary advisory status needs "an owner and resolution condition."

## Scorecard (objective reviewer, adjusted after cross-checking)

| # | MAGE criterion | Rating | Why |
|---|---|---|---|
| 1 | Modeling: question first, purposeful reduction, right grain | Adequate | Every model opens with its question (spec §3.2, `docs/agents/modeling.md`). The structural grain is close to a symbol table: every function, plus its params. |
| 2 | Correspondence pattern and direction of truth | **Strong** | Derive, stated deliberately. Ownership is deliberately *not* derived, and the reason is given. |
| 3 | Correspondence vs conformance (is vs ought) | Adequate | The distinction is stated. Ownership is the only independent "ought", and it can currently be bypassed. |
| 4 | Alignment wiring and boundary placement | **Weak** | The PR boundary is the right choice (REQ-03), but there is no Action and no `.github/`, so nothing is enforced. |
| 5 | Brownfield path and exit criteria | Adequate, but not yet used | Recover, reconcile, govern and advisory-first are all named. Promotion to a required check has no number, owner or measurement. |
| 6 | Governance conversion and capital | Adequate | Real failures became durable structure. None of it runs in CI. |
| 7 | Scope conditions (return, governability, authority) | Adequate | The checks are highly decidable. The return at this grain has not been priced. The course contract limits the team's authority. |
| 8 | Evidence honesty | Adequate | Measured timings and candid tickets. The noise experiment that the headline claims rest on has not been run. |
| 9 | Fit for agentic workflows | Adequate | Excellent agent-facing docs. The tool is not part of its own agents' loop. |
| 10 | Engineering depth | **Strong** | Determinism, rename semantics, fail-fast fetch, schema-before-rule ordering, contract tests. |

## Pros: what MAGE would praise

- **It picks the right correspondence pattern and says why.** "The code owns the facts, so models are derived and re-derived" (spec §1.2) is §2.5 applied deliberately. Generators are pure functions (no git, clock, network or randomness), and REQ-07 requires byte-identical output.
- **Ownership is an authored rule, not a derived model.** "Regenerating and comparing it would fail whenever someone new touched a folder" (spec §3.2). This is the project's one real *ought*, and it is the book's is/ought distinction built into the data model. All three reviewers called it the strongest decision.
- **Each model opens with its question.** `docs/agents/modeling.md` makes "question first", "purposeful reduction" and "four answers per model" house rules. Line numbers are excluded so that moving code within a file is not drift.
- **Responsibility is not delegated.** REQ-03 and REQ-06: the tool never writes to the repo, never approves, and never resolves a false verdict. A person accepts drift by committing `/models`, and the git history of `/models` is the provenance record. This matches the book's closing argument (§7.5) that responsibility is the one thing that cannot be delegated.
- **The PR is the right boundary.** "Intermediate commits may legitimately disagree with the models, so the result that counts is the one on the pull request" restates the book's semantic-gap example almost word for word: a pre-commit check acts too early, and the right point is the task boundary.
- **It never certifies a check it could not finish.** REQ-05 and `PARSE_FAILED` refuse a true/false verdict on any incomplete check, because a skipped file would otherwise show up as false REMOVED drift. This applies "don't give a validator more gating power than its evidence surface warrants".
- **Failures became durable structure, not one-off fixes.**
  - Quoted paths escaped the ownership rules. The fix was a shared `LOG_ARGS -z` used by both history readers.
  - A malformed `ownership.json` used to read as drift. It now returns `INVALID_MODELS`.
  - Bot authors used to be mined as owners. There is now a `BOTS` constant with a test.
  - Diagram rules are now checked by `tests/docs/test_diagrams.py`.
  - Every row in `state/tracker-gaps.md` names "a check that closes it".
- **Decisions are recorded with evidence.** D1–D12 in `docs/base/phase4.md`. For example, D11 chose a blobless clone after measuring 9–13 s against 163–221 s for reading blob by blob. There is also an ADR with its rejected option.
- **It suits agentic workflows.** The check is deterministic and runs no LLM, so agents may produce the code but are not trusted to grade it. The four-field JSON answer turns an agent's silent import-graph change into a short list of differences a reviewer can act on. The agent-facing docs (`AGENTS.md`, `docs/agents/`, a "which doc wins" order in `docs/README.md`) are what the book means by skills and project instructions.

## Cons: what MAGE would criticise

1. **Structure and behavior compare "is" with "previous is".**
   - Nothing written anywhere says "module X must not import Y" or "this transition is required". The only way to clear a structural or behavioral difference is to fix the code or run `drifter update`.
   - So "drift" here means "an architecture change nobody has acknowledged yet". It does not mean "the architecture is wrong".
   - The spec's own Risk 1 shows the cost: if most red checks are noise, "developers accept every change with update". What separates a design change from noise is exactly the *ought* that was never written down.

2. **The spec bends "Agreement is not correctness".**
   - Spec §1.2: "Agreement is not correctness, so a model becomes the standard only after a person reviews and commits it."
   - The book draws a different conclusion: "The distinction is not whether the model was derived or authored … The independence that matters … runs between the source of the obligation and the realization being evaluated against it."
   - A reviewed, regenerated JSON is an **acceptance ledger** (a baseline). That is a legitimate design, but it is not an independent obligation.
   - The skeptic called this a misreading. The objective reviewer called it a defensible design that is worded too strongly. Either way, the sentence should be reworded.

3. **The structural grain is close to the code itself.**
   - The book: "If the models and controls merely reproduce the entire implementation, the indirection has accomplished little."
   - Every function and method is a node carrying `params`, `decorators` and `async`.
   - The skeptic ran the generators read-only on this repo's 28 source files. The result was 358 nodes but only 48 edges. So the model is mostly an inventory of symbols, and renaming a parameter counts as drift.
   - Module ids are file paths, so moving a file shows up as a mass of REMOVED plus ADDED.

4. **The behavioral model's value is unproven.**
   - The miner only recognises `if x == "literal":` followed by an assignment to the same variable.
   - On this repo it found 0 states and 0 transitions (skeptic's run).
   - An empty model is always "aligned", which is a green result over an empty observation surface.
   - Spec Risk 2 planned to measure this on real repos. No result is recorded.

5. **The one real obligation can be bypassed.**
   - Ownership rules are read at the commit being checked. So a non-owner can add themselves as an owner and change the file in the same push, and the check passes.
   - The team found this itself (`docs/proposals/init/init.md`, "Problem 1"). It is designed but not fixed.
   - The evidence is the git author email, which anyone can set.
   - The book: a checker that reads an obligation the work can rewrite "may only confirm that the system agrees with itself".

6. **Nothing is enforced.**
   - There is no `.github/workflows`, and the Action is Phase 5. `tracker-gaps.md` row 19: "A verdict reaches nobody."
   - The repo has no `/models`, so it does not run its own check on itself.
   - The advisory-to-required promotion ("once its false-alert rate is acceptable") has no threshold tied to it, no owner and no measurement.
   - This is the book's "correct judgment without enforcement".

7. **The claims run ahead of the evidence.**
   - Spec §1.2 states its benefits in the present tense: models that "constrain every later change, including an agent's", and a check "measured … by accuracy, false-alert rate". None of these measurements exist yet.
   - The book's own DocAble evidence (App. G.3) reports six catches and then lists what they do *not* establish. That is the standard to match.

8. **The project's own docs are drifting.** These are small, but ironic for a drift tool.
   - `docs/README.md` says `contract/model-golden-outputs.json` is "not yet written", but the file exists.
   - `tracker-gaps.md` row 2 and spec Q11 still say owner schemas are unchecked, but `_schema_rule` is wired in at `Source/drifter/check.py` (commits `babd287`, `2372cc0`, `123fd46`).
   - The fixture repository is named differently in spec §4.2 and in the goldens.

9. **Some framing over-reaches.**
   - **Audit → Drain → Promote does not fit a derived baseline.** `drifter init` makes the model equal the code by construction, so there is no backlog of violations to drain. The pattern fits authored rules, which this project does not have yet for structure.
   - **The EU AI Act claim.** The skeptic reports that Annex XI items 1(d) and 2(b) concern a general-purpose AI model's architecture and its design rationale, and that a Python import graph provides neither. The spec already marks this framing as open (Q11).
   - **Planned spend may be in the wrong place.** About 1,200 lines in `docs/proposals/language-engine/` plan support for 14 languages before the Python check has shown a return. The book's advice is "invest where it pays".

## Where the reviewers disagreed

| Question | Advocate | Skeptic | Resolution |
|---|---|---|---|
| Does committing a derived model make it a standard? | Yes: a human-accepted baseline | No: that misreads §3.2 | It is a **baseline**, not an obligation. Useful, but reword spec §1.2. |
| Is the missing gate a design flaw? | No: an adoption gap, Phase 5 | Yes: nothing is governed | The design is right, but MAGE judges what the environment enforces, so today it counts as Weak. |
| Is the model grain right? | Deliberate reduction | Mostly a symbol table | The objective reviewer sided with the skeptic. Re-decide the grain from the user's question. |
| Is the depth real? | Yes | Mostly course-contract work | Real engineering depth. The *hard* problem (noise, extraction quality) has no data yet. |

## What MAGE would likely say (paraphrased, not a quotation)

> You chose the right correspondence pattern and you can say why, which puts you ahead of most drift tooling. But a drift check has a narrow job: it keeps a declared correspondence true. Your structural and behavioral checks can tell a reviewer that something changed. They cannot tell anyone that something is wrong, because nothing independent of the code says what should hold. Your ownership rules are the one place where the work can actually be wrong, so protect them first: a rule the governed party can rewrite in the same change is not yet an obligation. You built a good sensor and validator and then stopped before the gate. A correct judgment that nothing acts on is a failure of enforcement, not a success of detection. Ask whether function-level grain answers the question your users actually ask, and price what each helper rename costs. Then run the tool on yourselves.

## Suggested changes, in priority order

Each change is tied to the MAGE move it serves. Following `AGENTS.md`, these are proposals, and choosing among them is a conscious decision for the team.

1. **Close the ownership self-grant hole.** *(§3.2 independence of the obligation; §3.4 conversion into enforcement)*
   - Judge each commit against `ownership.json` at its **base**, not its head.
   - Require that changes to `models/ownership.json` be made or approved by owners under the old rules.
   - Generate or verify `CODEOWNERS` from `ownership.json`, so GitHub's authenticated review does the enforcing.
   - Label author-email evidence as advisory.
2. **Wire the gate and run it on this repo.** *(Earliest decidable boundary; Audit → Promote; "an owner and resolution condition")*
   - Commit `/models` for `Source/`.
   - Add a PR workflow that runs `pytest` and `drifter check`, advisory first.
   - Add a "run `drifter check` before declaring done" step to `AGENTS.md`.
   - Name an owner for the advisory period and a numeric exit condition (for example, the spec's <10/100 false-alert rate).
3. **Write down one independent architecture rule.** *(§3.2: the derived model supplies the "is", an authored rule supplies the "ought")*
   - For example, an allowed or forbidden import table between packages ("`models` must not import `GitHub_Connector`"), checked against the derived structural edges.
   - This turns the tool from a change detector into an architecture guard, and gives Audit → Drain → Promote something real to drain.
4. **Re-decide the structural grain from the user's question.** *(Purposeful reduction; "build the smallest asset that retires the recurring cost")*
   - Measure noise at module and package level against function level.
   - Consider dropping `params` and `decorators` and leaving out private symbols. Make finer grain opt-in through `scope.json`.
   - Make ids stable across file moves where possible.
5. **Run the Risk 1 and Risk 2 experiments and report them in the style of App. G.3.** *(Evidence honesty)*
   - Report counts, method, limits and what the results do *not* establish.
   - If the behavioral miner stays near zero on real repos, drop it, or turn it into an authored state model checked against mined transitions (trace + check).
   - Reword spec §1.2's present-tense benefits as goals until the measurements exist.
6. **Fix the docs' own drift and trim the framing.** *("Add metadata only when a defined consumer uses it")*
   - Correct `docs/README.md`, `tracker-gaps.md` row 2, spec Q11 and the fixture repository name.
   - Reword spec §1.2's "becomes the standard" sentence to "becomes the accepted baseline".
   - Narrow the Annex XI claim to "helps keep the code-architecture part of technical documentation current".
   - Hold the multi-language plan until the Python check shows a return.

## What must be implemented: a simple CI pipeline that enforces the tests

**What the repo has today:**
- 25 pytest files (`tests/**/test_*.py`) with 277 tests. *(Collected on 2026-11-05; whether all pass was not re-run then.)*
- `coverage` listed in `requirements.txt`.
- A Railway deploy with a health check.

**What it lacks:**
- **No gate before production.** README: Railway deploys "automatically on every push to `main`". With no CI and no branch protection, an untested push reaches production. This is the most urgent gap; C6 closes it.
- No `.github/` folder and no CI, so tests run only when someone remembers to run them.
- No linting and no dependency scanning.
- No `/models` folder for the tool's own code.

**The MAGE requirement.** MAGE names no tools. It asks for four things:
- Each obligation has a check.
- The check runs at the earliest point where it can decide (§3). For this repo that point is the pull request.
- A check blocks only as much as its evidence justifies (§3.2).
- Every warning-only check has an owner and a condition that ends the warning period (§3.4).

**The plan.** The plan below meets those requirements with:
- one workflow file;
- three tools that are already in use or need one `pip install` (`pytest`, `ruff`, `pip-audit`);
- one GitHub setting.

Anything more complex is listed under "Later".

**Why the whole suite runs on every PR here, unlike in the lecture.** The lecture's final design for DocAble runs only cheap checks at landing and the full suite on a timer behind it, with a red result blocking new dispatch. That design answers DocAble's problem: a suite of about thirty minutes and many agents landing in parallel. This repo has 277 tests and no fleet of parallel agents landing work, so running everything at the PR is the proportionate choice. Revisit it if the suite gets slow enough that waiting for it becomes the bottleneck (`mage-engineering-env.md` §7). The lecture's rule still applies: "Local hooks are a convenience layer; CI is the control layer" (deck 2-7, S20).

### Summary

| # | Must implement | Blocks merges? | Effort |
|---|---|---|---|
| C1 | One workflow file, `.github/workflows/ci.yml`, that runs on every PR and every push to `main` | – | One file |
| C2 | `pytest` with a coverage report | **Yes** | Already written |
| C3 | `ruff check` for lint | **Yes** | One config line |
| C4 | `pip-audit` for known vulnerable dependencies | **Yes** | One command |
| C5 | `drifter check` on the tool's own code | Warning only, until C8 says otherwise | Run `drifter init` once and commit `/models` |
| C6 | Branch protection on `main`: C2–C4 must pass and one review is required | – | GitHub settings |
| C7 | Ownership fix with tests, plus a `CODEOWNERS` file | **Yes** (through C2) | Small code change and 3 tests |
| C8 | Owner and a tally of red `drifter check` results | Decides when C5 starts blocking | A markdown table |

### C1. The workflow file

The whole pipeline is one file. Every PR runs all the checks, and a failing step fails the PR.

```yaml
# runs the tests, lint, dependency audit and the tool's own drift check on every PR
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0              # drifter check reads git history
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"      # same as the Dockerfile
      - run: pip install -r requirements.txt . ruff pip-audit
      - run: ruff check Source tests
      - run: pip-audit -r requirements.txt
      - run: coverage run -m pytest
      - run: coverage report
      - name: drifter check (warning only until C8 is met)
        if: github.event_name == 'pull_request'
        continue-on-error: true
        run: drifter check HEAD --base ${{ github.event.pull_request.base.sha }}
```

- **Tests that prove it:**
  - Open a throwaway PR that breaks one unit test. It must turn red.
  - Open a PR with no code change. It must turn green.
- **Done when:** both throwaway PRs behave as expected.

### C2. Unit and automated tests block merges

- **Must implement:** nothing new. The 277 existing tests run in C1. They are deterministic, so they have enough evidence to block from day one.
- **Note:** `tests/connector/test_golden.py` skips itself when GitHub is unreachable. GitHub runners are online, so it runs in CI. Check the log once to confirm that it was not skipped.
- **Coverage:** report it only and set no minimum. MAGE treats a number as useful only when someone acts on it, so add a floor later, once there is a baseline.

### C3. Static analysis: `ruff`

- **Must implement:** add `[tool.ruff]` to `pyproject.toml`, using ruff's default rules. Fix or `# noqa` the existing findings once, in a single commit.
- **Test that proves it:** a PR that adds an unused import turns red.
- **Why only ruff:** it is one fast tool with no setup. `mypy` is listed under Later.

### C4. Security: `pip-audit` and GitHub secret scanning

- **Must implement:**
  - The `pip-audit` step in C1. It fails when a dependency has a known vulnerability.
  - Turn on GitHub **secret scanning** and **Dependabot alerts** in the repository settings. These are two switches, with no code.
- **Test that proves it:** a PR that pins a dependency to a known vulnerable version turns red.
- **Security unit tests:** the ownership tests in C7 are the security tests that matter most for this tool, and they run inside `pytest`.

### C5. The tool checks its own code

- **Must implement:**
  - Run `drifter init` once and commit `/models`.
  - Keep the C1 step as warning only (`continue-on-error: true`).
- **Rule:** a "no verdict" result (exit `2`) means the check could not finish (REQ-05). Never read it as a pass. While the step is warning only, the reviewer reads its output.
- **Tests that prove it:**
  - `drifter check` exits `0` on `main` right after `/models` is committed.
  - A PR that adds an import between modules, without `drifter update`, shows drift in the step's log.

### C6. Branch protection on `main`

- **Must implement:** in GitHub, go to Settings → Branches → `main` and set:
  - Require the `ci / test` status check to pass.
  - Require one approving review.
  - Block direct pushes.
- **Why:** without this setting, a red check is only a warning (§3.4, "correct judgment without enforcement"). This setting is the gate.
- **Note:** `drifter check` is `continue-on-error`, so it does not fail the job. The required check therefore enforces C2–C4 only.
- **It also closes the deploy gap.** Railway deploys every push to `main`. With direct pushes blocked and `ci / test` required, only commits that passed CI reach `main`, so only those deploy.
- **Optional second line:** check whether Railway's GitHub integration can wait for CI checks to pass before it deploys. If it can, turn it on. *(Not verified here.)*

### C7. Close the ownership self-grant hole (con 5)

This is the project's one real *ought* (§3.2). It must block merges, so its tests live in `pytest` and are enforced by C2.

- **Must implement:**
  - Read `ownership.json` at the PR **base**, not at the head.
  - Add a `CODEOWNERS` file that names the owners of `models/ownership.json`. GitHub then requires their review, which is authenticated, unlike the author email.
- **Tests to write** (each one failing first, per `AGENTS.md`):
  - A non-owner adds themselves to `ownership.json` and edits an owned file in the same push. Expected: violation.
  - A non-owner edits only `ownership.json`. Expected: violation.
  - An owner under the base rules edits an owned file. Expected: no violation.
- **Done when:** the three tests pass in CI and `CODEOWNERS` is committed.

### C8. When `drifter check` starts blocking

- **Must implement:**
  - Name one **owner** in this file.
  - Keep a short table in `docs/state/` with one row per red `drifter check`: the PR, and whether it was *true drift*, a *false alert* or an *accepted change*.
- **Exit condition:** fewer than 10 false alerts in 100 red checks (spec Risk 1). When it is met, delete `continue-on-error` from C1. The drift check then blocks merges too.
- **Lecture match:** this is the promotion the lecture describes at Cloudflare, policies moving "from advisory guidance to enforced requirements", which it calls "an Alignment decision". Promote on measured evidence, not on a schedule.

### C9. The agent loop

- **Must implement:** one line in `AGENTS.md`: "Run `pytest` and `drifter check` before declaring a task done."
- **Why:** if an agent skips this step, CI still catches the failure at the PR.

### Later (not needed for a working pipeline)

Each item below is a conscious choice for the team, not part of the minimal plan:

- `mypy` type checks.
- `bandit` code scanning.
- A coverage minimum.
- Generating `CODEOWNERS` from `ownership.json` automatically.
- An authored architecture rule, such as a table of forbidden imports (suggested change 3).
- A docs-drift test (con 8).
- A weekly scheduled `pip-audit` run.

## Open questions

- On a real repository, how often is drift accepted with `drifter update` rather than fixed in code (spec §7.3)? A very high acceptance rate would suggest reviewers are rubber-stamping.
- What does a reviewer see on a medium-sized refactor: how many entries, and can they act on them? Is a summary at module level needed for the PR comment?
- Does the pod contract leave the team authority to change the shared interface if the diagnosis calls for it (§6.3 scope condition 3)?
- Does any consumer actually use the Annex XI framing, or is it motivation only?

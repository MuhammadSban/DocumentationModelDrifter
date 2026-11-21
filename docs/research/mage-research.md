# Deep Research: How MAGE sets up an engineering environment for agents

Source material: James C. Davis, *Model-Based Agentic Engineering* (Edition 1, 2026), and its companion repository. Researched 2026-11-04 from a full clone of the repository (commit `a92e6de`) and the published book index. Every repository path below is relative to <https://github.com/davisjam/model-based-agentic-software-engineering/blob/main/>.

**Updated 2026-11-05** against the course lecture **"Building with Agents"** (<https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/>, decks 2-5 to 2-7). Where the lecture changes a finding, a **Lecture update** note says so. Where they differ, the lecture is the newer account.

Companion to `mage-engineering-env.md` (the lecture notes, rewritten for clarity) and `mage_take.md` (the review of this project against MAGE).

## Executive Summary

MAGE starts from one premise: "Commodity intelligence makes implementation abundant relative to engineering judgment" (`book/part1/00-part-intro.md`). When agents write code cheaply, the scarce things become judgment, representation, evidence and enforcement. MAGE answers with two principles. **Modeling** writes the knowledge an agent would otherwise rediscover into explicit, purposeful models. **Alignment** turns selected obligations into mechanisms (constraints, sensors, validators and gates) so that meeting them "does not depend on the agent remembering, agreeing, or self-certifying each time" (`book/part1/1.4-the-new-engineering-problem.md`). A third loop, **governance conversion**, turns each recurring failure into durable structure.

The companion repository shows how this works in practice for a fleet of coding agents. An orchestrator session plans with templates (Epic → design doc → brief) and dispatches typed roles (a strong model plans and reviews, a cheaper model does mechanical work) into isolated git worktrees. Every hand-off is checked by a deterministic mechanism. A brief lint blocks a malformed dispatch. A **sentinel first commit** aborts an agent in a broken worktree within a minute. A pre-commit hook runs changed-file lints and fast tests and requires commit trailers. A **merge train** lands non-conflicting batches. (The lecture's final account separates landing from the full test run: cheap checks decide landing, a timed sweep tests `main` behind it, and a red sweep stops new dispatch; see finding 11.) An Epic **definition of done** closes only after a fresh, independent reviewer re-runs everything at HEAD. Agent lifecycle hooks (turn-stop, pre-compaction, session-start, a 30-minute reflection) keep the loop moving and bank state before memory is lost. Nothing relies on the model's memory: state lives in committed, dated files.

The main gap for this project (DocumentationModelDrifter) is not modeling. Its models, docs map and glossary are strong. The gap is **enforcement and orchestration**. It has no installed git hooks, no agent hooks, no Epic or brief templates, no typed agent roles, no CI, and no file that survives an agent's memory loss (a work-items file or an orchestrator log). `mage_take.md` reached the same conclusion about the product: "a well-built sensor and validator with a governance plan that exists only on paper."

## Key Findings

1. **The book names two problems, not "hallucination and memory loss".** The *Representation Problem*: how to represent a large system so an engineering question can be answered "without continually reconstructing [it] from implementation." The *Enforcement Problem*: how to enforce intent so that obligations do not depend on the agent remembering them (`book/part1/1.4-the-new-engineering-problem.md`). The underlying model properties are "bounded working state" and "probabilistic output" (`book/part1/1.3-the-agentic-substrate.md`). The word "hallucination" does not appear in the book.
2. **Guidance is not enforcement.** "Guidance influences behavior; enforcement determines what the environment will permit or accept" (`book/part3/3.1-where-obligations-can-be-enforced.md`). CLAUDE.md, skills and injected context are guidance. Hooks, gates and types are enforcement.
3. **Place each check at the earliest boundary where the obligation is legible and decidable** (`book/part3/3.2-models-and-the-semantic-gap.md`). The boundaries are reasoning input, the action (tool call or hook), the work unit (task, PR, build) and the artifact/runtime. A cheap file check belongs in pre-commit. A model-to-code drift check belongs at agent return. An intent review belongs at Epic close (`agent/governance-doc-controls/semantic-level-enforcement.md`).
4. **There are four roles of control.** A **constraint** removes an action the system could take. A **sensor** produces evidence and does not judge. A **validator** evaluates evidence against an obligation. A **gate** decides whether work may cross a boundary (`book/part3/3.3-constraints-sensors-validators-gates.md`). "A validator should not receive more gating power than its evidence surface warrants" (3.2).
5. **Agreement is not correctness.** A drift check proves that two representations agree, not that either is right. "Enforcement requires something against which the work can actually be wrong" (3.2). This is the point `mage_take.md` makes against this project.
6. **The planning template is the roadmap.** The Epic template (`downloads/EPIC-TEMPLATE-starter.md`, `docs/epics/*/main.md`) has a status header and these sections: §1 Rationale, §1.1 Models & invariants, §1.2 Closest related functionality, §1.3 Risks & blast radius, §2 Cost calibration, §3 Phases (each with acceptance and prerequisites), §4 Phase notes, §5 Definition of Done, §6 Open questions, §G Open forks for the user, §7 Cross-references, §8 Tag. "Phase 1 is ALWAYS planning/design … Never dispatch implementation speculatively." The talk says each design surfaced "between one and about eight judgment-call questions" for the human (`book/anl-talk-transcript.cleaned.md` L217).
7. **Model tiers are an engineering decision.** From the talk: "The first phase, maybe have a Fable-grade model do that, a really expensive one. The second phase, it's all just make-work, have a Sonnet do this one. The third phase is a little tricky, maybe an Opus will have to do it" (L161). The repository's typed roles are `opus` (architecture, root-cause analysis, multi-file work), `sonnet-active` (mechanical work), `lint-runner` and `commit-slave` (`agent/context-and-dispatch/role-typed-dispatch.md`). Founding designs get a second, independent review by a model that did not write them, and "the reviewer wins" (`agent/governance-doc-controls/independent-design-review.md`). **Lecture update:** the reviewer "refers whatever it cannot resolve back to the engineer"; it does not settle every open question itself. Epic close needs a "Final-Opus trust-nothing" review at HEAD (`agent/governance-doc-controls/epic-definition-of-done.md`).
8. **The brief is the agent's whole world, so it is linted.** Before launch, the dispatch path checks the worktree-isolation marker, the dispatch id, the mandatory snippets, the role, real `file:line` citations and the declared file footprint. Exit 1 means do not launch (`agent/context-and-dispatch/brief-linting.md`). The brief template has these sections: Role & model, Time budget, Scope (allowlist + non-goals), Pre-work context, Execution, Verification, Acceptance, Hand-back ("Trust nothing on my behalf") (`downloads/agent-brief-starter.md`).
9. **Context is pushed, not pulled.** Dynamic context injection takes the files an agent will touch and pulls the rules that apply to them into the brief. It runs in reverse in CI to report "only what you broke" (`agent/context-and-dispatch/dynamic-context-injection.md`). The model query CLI is `repo-query` (`book/appendix-fills/models-bridge/query-surface.md`). This is the "query-repo" in the notes.
10. **The sentinel first commit turns a 60-minute failure into a 1-minute abort.** On an agent's first commit, the hook checks that the worktree root, the per-agent marker, the branch `worktree-agent-<id>` and the working directory are all correct (`agent/gates-and-merge-train/sentinel-first-commit.md`). New checks ship audit-only first and become blocking after a clean session.
11. **Tests run in tiers, not constantly.** "commit → cron → merge-train → deploy" (`agent/gates-and-merge-train/pre-commit-hook.md`). Pre-commit runs changed-file lints and unit tests under a "1-second rule". It writes a marker keyed by the tree's SHA, and the merge check refuses an agent commit without one. The merge train rebuilds and re-tests the actual merged tree, batch by batch (`agent/gates-and-merge-train/merge-train-mis-batching.md`). Deploys go through a canary with no traffic, smoke tests and then promotion (`agent/gates-and-merge-train/staged-deploy-gates.md`). Tests are serialized with a host lock so parallel agents do not corrupt each other's runs (`agent/mediators-and-resource-locks/test-serializer.md`).
    **Lecture update ("Improving the infrastructure").** DocAble first validated batches of finished changes at regular intervals; that is the "main in the last hour" design in the notes. As the suite grew to about thirty minutes, validation became the limit on integration, and validating on every land overloaded the host. The final design: cheap admission checks run synchronously and decide landing; a broad sweep runs on its own timer over `main`; a failing sweep records an alert, and a pre-dispatch gate refuses new agents until it is handled. The gate must fail closed, and "acknowledgment is not health": only a passing sweep shows `main` is healthy.
12. **Commits carry metadata.** Agent commits need a `Commit-of i/N` trailer (pre-commit-hook.md) and a `caused-by: epic:<id> | reflection:<id> | ad-hoc` field from a closed list (`agent/lifecycle-and-observability/caused-by-provenance.md`). A commit message names its area and ends with what was verified (`CLAUDE.md`, sole commit).
13. **Agent hooks keep the loop alive.** "These are hard controls. Claude can't cheat, it has to run it" (talk L141–147). **Lecture update:** read this narrowly. A hook's *firing* is guaranteed, but only a hook that can block is a control. The lecture labels the pre-dispatch hook "deterministic" and the start and return hooks "prompt reminders": "A reminder raises the probability that an agent follows a procedure and guarantees nothing." Known uses: a turn-stop hook that refuses to rest while ratified work remains; a pre-compaction hook that writes a hand-off; a session-start hook that reads unacknowledged alerts; a pre-tool guard that denies edits outside the worktree; and a reflection hook that fires every 30 minutes and asks the agent whether it has hit a recurring issue (`agent/lifecycle-and-observability/lifecycle-hooks.md`; talk L209).
14. **Dead agents are recovered from a registry, not by guessing.** An append-only JSONL registry records every dispatch. Recovery classifies each orphan worktree as LANDABLE, ALREADY-LANDED, EMPTY or AMBIGUOUS. "Report first; never auto-destroy." Tombstone commits record what happened to abandoned branches (`agent/lifecycle-and-observability/agent-registry.md`, `tombstone-commits.md`, `plugin/mage/skills/self-operations/examples/runbook-recover-the-fleet.md`).
15. **Memory lives in files.** `WORK-ITEMS-<date>.md` is "the file to read first after an outage or a compaction". Items leave it only when landed and verified. `ORCHESTRATOR-TODO-<date>.md` holds append-only session deltas "banked against compaction". `PLAN.md` is the durable spine: "the orchestrator's todo list is a view of it, not the source" (`workbench/`).
16. **CLAUDE.md is an index of rules, each pointing to its enforcement.** A rule earns its place only if it is regression-preventing, non-derivable from the local file and non-local. "A rule without an enforcement pointer is a hope, not a gate" (`agent/governance-doc-controls/claude-md-rule-index.md`, `downloads/CLAUDE-starter.md`).
17. **Governance conversion is the learning loop.** "A failure exposes a recurring class, engineering identifies what was missing, and the environment encodes the lesson as durable structure… The repair fixes this instance. Conversion changes the environment" (`book/part3/3.4-governance-conversion.md`). The missing piece lands in one of five places: model, obligation, sensor, validator, or constraint/gate.
18. **The human keeps responsibility.** "Delegating a decision to a machine does not delegate the responsibility." The engineer "must retain informed control over the resulting system" (`book/part7/7.4-the-engineer.md`). The talk contrasts three stances: autonomy (fast, no controls), oversight-centric (review every snippet) and governance-centric (the human writes policy into the environment) (talk ~L55–70).

## Detailed Analysis

### 1. Orchestration: who does what

| Concern | Mechanism | Source |
|---|---|---|
| Plan before building | Epic Phase 1 is always read-only design, then human ratification | `downloads/EPIC-TEMPLATE-starter.md` |
| Choose the model per phase | Typed roles; expensive model for planning, review and audit; cheap model for make-work | talk L161; `role-typed-dispatch.md` |
| Question the plan | Phase-1b review by a fresh model that did not author it; verdict RATIFY or REVISE; reviewer wins | `independent-design-review.md`; `docs/epics/*/phase-1b-review-*.md` |
| Isolate parallel work | One git worktree per agent; disjoint file footprints per wave | `brief-linting.md`; `AGENTS.md` §1 |
| Land work safely | Merge train: conflict graph, maximum independent set per tick; hot files cap the batch at 1 | `merge-train-mis-batching.md` |
| Close honestly | DoD re-run at HEAD by a trust-nothing reviewer; every cited commit must be reachable from main | `epic-definition-of-done.md` |
| Recover dead agents | Registry → classify → land / tombstone / surface | `runbook-recover-the-fleet.md` |

The repository also tells the orchestrator to verify, not trust: a closing report is unreliable, so check the disk (`git log`, `git status`) after an agent returns (`CLAUDE.md`, fleet section).

### 2. Roadmap: the document chain

The roadmap is a chain where each document has one job: "the Epic is the effort, the design doc is the plan, the brief is the dispatch" (`brief-linting.md`). Around it sit:

- **Open decisions → ruled decisions.** `OPEN-DECISIONS.md` lists what the author must rule on. Each ruling is recorded verbatim in `DECISIONS-RULED-<topic>-<date>.md` "so an implementing wave cites a decision rather than re-deriving one."
- **Phase checkpoints.** `DONE-phase-<X>.md` records the branch, base SHA, footprint, gate results, and "decisions taken that the spec left open", each pinned by a test and waiting for a ruling.
- **Dated audits** replace present-tense gap lists, because "a gap list asserts the PRESENT TENSE… so it is false the moment the system moves" (`CLAUDE.md`).

### 3. Alignment through tests and hooks

The pattern is to inject the rule at the start and enforce it at the end. Dynamic context injection gives the agent the rules for its files. The pre-commit hook then checks the same rules (talk L169–171). Git hooks guard what is written; lifecycle hooks guard what the loop does (`pre-commit-hook.md`, "Counterpart").

On test-first versus test-after, the book's stance is evidence-first, not strict TDD. "Validate the change, not the producer's story" and "Done is a claim, not a stored fact" (`book/part4/4.4-engineering-the-environment.md`). It prefers property tests to single examples and derives the required test set from the model (the **test-obligation census**, `book/appendix-engineering-moves/derive-the-obligation-set.md`). This matches the notes: tests must be good and independent of the implementation's story. Whether they are written first matters less.

### 4. Ten engineering moves (Appendix B)

1. **Make one source authoritative**: one machine-readable source; consumers query or derive from it.
2. **Derive; don't copy**: a copy silently strips the source of its authority.
3. **Keep representation and reality in correspondence**: check both ways, including whether reality has things the model does not.
4. **Derive what must be assured**: derive the required evidence set from the model, then diff it against what exists.
5. **Enforce where the property becomes legible**: the earliest decidable boundary; re-check at the last safe one.
6. **Close the action surface**: consequential actions go through a small set of named verbs.
7. **Deliver knowledge where the decision occurs**: push rules into the brief.
8. **Make cause travel with consequence**: `caused-by` at commit time.
9. **Externalize recurring operational judgment**: runbooks and playbooks.
10. **Make hidden dependencies queryable**: blast radius as a query.

### 5. Operating the environment

- The **daily review** asks five questions: did durable work move; did a trusted representation become doubtful; did an obligation escape enforcement; what did a human have to decide again; what should the environment learn (`book/appendix-operators-reference/daily-review.md`).
- **Brownfield adoption** goes Audit → Drain → Promote. Recover latent models from the code before inventing new ones (`book/part4/4.3-brownfield-engineering.md`).
- **Engineering capital** is durable structure that lowers the future cost of change. It depreciates, so each control needs an owner and a retirement condition (`book/part3/3.4-governance-conversion.md`).

## Contrarian Views And Risks

- **The tower of governance.** Davis warns against it himself: "You can go too far on this. So you need to find the sweet spot" (talk L189). The self-governance skill says "default to skip". Every control has a carrying cost and can collide with another control (`book/part3/3.5-when-guardrails-collide.md`).
- **Single-author evidence.** Most numbers come from one engineer's factory (DocAble). The book flags its counts as snapshots that will move (`book/part6/6.3-scope-conditions.md`).
- **Tests cost compute and agent bandwidth.** Pre-commit latency "creates pressure to bypass" (`pre-commit-hook.md`). The book's answer is tiering and serializing tests, not running everything on every edit.
- **Self-review is not assurance.** "another probabilistic judgment from the same productive substrate does not automatically create engineering assurance" (`book/part1/1.3-the-agentic-substrate.md`). A second agent review helps, but deterministic checks are what make it hard.
- **Agents optimize locally.** The autoscaler story in §5.2: "for weeks the agents made it better and better, with every improvement colliding with the same boundary." That boundary was an architectural decision a human had to make.

## Open Questions

- Several phrases in the lecture notes do not appear in the published talk or book. The 2026-11-05 lecture now accounts for three of them:
  - a second Fable that questions the first is the **independent design review**;
  - the "validation agent" and "audit Fable" are the **Definition of Done audit** ("an agent reporting done is not the process accepting done");
  - "main in the last hour" is DocAble's **first, abandoned** test design (finding 11).

  Still unsourced: "Impromptu LLMs" (the lecture's nearest is its VISION → WORK / PROCESS / INFRASTRUCTURE slide), "fleet of moderately competent interns" and "go until you lose control". They may come from a Q&A. The rewritten notes keep them as the notes state them.
- The planner's tier is not fixed. The talk says "Fable-grade" for planning at L161 and "the Opus-grade model that's doing the planning" at L233. An earlier decision log notes that Fable was not dispatchable by the harness at the time and that an "Opus second opinion" stood in.
- Haiku does not appear in the repository's role table.

## Sources

- Course lecture "Building with Agents" (Act II, unit 05): <https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/>, with decks 2-5 (Agentic Workshop), 2-6 (Software Factories) and 2-7 (Inside an Agentic Software Factory). The newest account; used for the Lecture update notes.
- Book index: <https://davisjam.github.io/model-based-agentic-software-engineering/book/mage-book/index.html>. Chapter list; confirms the clone matches the published edition.
- `book/part1/*`: premise, substrate, the two problems.
- `book/part2/*`: modeling principle, model classes, correspondence (derive / generate / trace).
- `book/part3/*`: alignment, boundaries, the four roles, governance conversion, guardrail collisions.
- `book/part4/4.1, 4.3, 4.4`: active/passive alignment, brownfield, engineering the environment.
- `book/part5/5.2`: inside DocAble's software factory.
- `book/part7/7.4, 7.5`: the engineer; what cannot be delegated.
- `book/anl-talk-transcript.cleaned.md`: the talk (model tiers, hooks, reflection hook, templates).
- `book/appendix-engineering-moves/*`: the ten moves.
- `book/appendix-operators-reference/*`: daily review, dashboard, engineering capital, model health.
- `agent/**`: 30 mechanism entries in five families.
- `hooks/pre-commit`, `hooks/pre-push`, `hooks/pre-merge-commit`, `hooks/_hook_root.py`: the repository's own git hooks.
- `downloads/EPIC-TEMPLATE-starter.md`, `downloads/design-doc-template-starter.md`, `downloads/agent-brief-starter.md`, `downloads/CLAUDE-starter.md`, `downloads/op-playbook-starter.md`: starter templates.
- `plugin/mage/skills/{self-governance,self-operations,self-communicate}`: the MAGE Claude Code plugin.
- `CLAUDE.md`, `AGENTS.md`, `workbench/PLAN.md`, `workbench/ORCHESTRATOR-TODO-*.md`, `workbench/DECISIONS-RULED-*.md`, `docs/epics/*`: how the repository runs its own agents.

## Rerun Inputs

```
workflow: firecrawl-deep-research
topic: MAGE agent orchestration, roadmap templates, tests and hooks for alignment
depth: exhaustive
output: markdown
note: Firecrawl CLI was not installed; collection used a git clone of the repository, Exa for the web book, and four parallel readers over the clone.
```

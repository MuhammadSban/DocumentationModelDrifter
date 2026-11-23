# Engineering the environment for agents (MAGE lecture notes)

Lecture notes on how James C. Davis runs coding agents under MAGE (*Model-Based Agentic Engineering*), rewritten for clarity. The primary authority is now the course lecture **"Building with Agents"** (MAGE course, Act II, unit 05) and its three slide decks. Each section keeps the handwritten notes' meaning. Where the lecture adds or corrects something, an **In the lecture** block says so. Below that, an **In MAGE** block adds what the book and the example repository say about the same point.

- Lecture page and decks: [Lecture], [Deck 2-5] (hands-on workshop), [Deck 2-6] (software factories), [Deck 2-7] (inside DocAble, Davis's own factory). Slide numbers are written "S#".
- Cited research, with sources: §14 below.
- How this project scores against MAGE, and the CI plan (C1–C9): `mage_take.md`.

Notation:
- *Margin* marks a handwritten side note.
- *Corrected* marks a statement from the handwritten notes that the lecture contradicts. The corrected version is the one given.
- **Not found in the sources** marks a point from the notes that the lecture, talk, book and repository do not contain. Those points are kept as the notes stated them. The handwritten notes may come from a different session than the three decks.

---

## 0. Framing: the software factory

The lecture changes what "setting up the environment" means. The question is no longer "which of Davis's mechanisms do we copy?" It is "for each obligation, what independent check refuses a violation, and at which boundary?"

- **Software factory:** "an engineered production system for repeatedly producing controlled changes to software" ([Lecture]). Agents make implementation cheap. So the scarce asset becomes the environment: the knowledge, guidance, controls and validation that direct, evaluate and admit changes. In the decks' words, "agents build, so verification sets the pace" ([Deck 2-6], S26).
- **Two engineering problems** ([Lecture]):
  - **Process design (P):** "how work is decomposed and sequenced, what information and tools reach the fabricator, where decisions are made, and how products move through inspection and admission." Instruction files, skills, templates, briefs and reminder hooks live here.
  - **Tolerance (T):** "what variation in the product is acceptable": a memory bound, an architectural dependency rule, an invariant or a behavioral requirement. Lints, tests, gates and the Definition of Done live here.
  - The two are paired, not alternatives. "A project instruction may guide an agent away from an architectural violation, while a dependency check independently rejects the violation if it occurs… A more capable agent may need less guidance, but the architectural obligation remains." A factory "can improve one without necessarily improving the other."
- **Delegation as four decisions** (from the Delegation unit, recapped in [Lecture]): **BOUND → EQUIP → AUTHORIZE → VERIFY**. Decide what work to delegate, supply the information and means to do it, limit the consequences the agent may produce, and establish what evidence justifies accepting the result.
- **Three layers of capability:** "the underlying foundation model supplies reasoning capability, while the agent harness manages context, tools, and actions over time. The engineering environment supplies the repository, specifications, tests, build systems… An agent's effectiveness therefore depends on more than its underlying foundation model" ([Lecture]). This note is about the third layer, and about the harness hooks that connect it to the second.
- **The one practical rule:** every consequential instruction needs an executable check behind it. "A deterministic check rejects an operation that violates a stated condition. A reminder raises the probability that an agent follows a procedure and guarantees nothing" ([Lecture]). Deck summary: "Guidance aims, gates refuse, queries prevent, audits verify" ([Deck 2-7], S14).
- **Everything depreciates.** "Instructions can become stale, models can diverge from implementation, and tests can cease to represent the properties they were intended to check. These resources are engineering capital only while they continue to help future work" ([Lecture]).

How the rest of this note maps onto the four decisions:

| Decision | Question | Sections |
|---|---|---|
| BOUND | What work should the agent do? | §1 vision, §3 strategy, epic, design doc, brief |
| EQUIP | What does it need to succeed? | §2 equipping, §6 `query-repo`, §8 planning |
| AUTHORIZE | What consequences may it produce? | §2 capability vs authority, §5 hooks, §7 admission |
| VERIFY | What evidence justifies acceptance? | §4 Definition of Done, §7 tests, §10 measurement |

## 1. The vision ("Impromptu LLMs")

The setup has three parts:

1. **A to-do list** of the work that needs doing.
2. **Structured templates and processes** that every piece of work follows.
3. **Enough infrastructure** to remove all reasoning that can be avoided, and to direct the reasoning that remains.

> **In the lecture.** The three parts match Deck 2-7's "Three Requirements for Productive Agents": 1. WORK (strategy, priorities, dependencies), 2. PROCESS (templates, lifecycle, validation), 3. INFRASTRUCTURE (tools, hooks, test infrastructure). All three rest on a prerequisite, VISION: "What are we trying to build?" The goal is to "make necessary engineering reasoning the bottleneck" ([Deck 2-7], S3). The page adds: "Without that vision, more implementation capacity produces more software whose correctness nobody can establish" ([Lecture]).

> **In MAGE.** "Leverage moves into the environment" (§1.1). The talk: "eliminate the need for reasoning if you can… When you need to reason, you should tell it what to reason about and how to reason about it."

## 2. Equipping the agent

*New section; the handwritten notes do not cover it. Source: [Lecture], "Equipping the agent", and [Deck 2-5].*

An agent fixing a bug in an unfamiliar repo must first learn which specification governs the behavior, where the tests are, what commands build the system, and which conventions a change must preserve. "The engineer can answer these questions repeatedly during each session, or arrange for the engineering environment to supply the relevant knowledge" ([Lecture]).

**Five mechanisms, one job each** ([Lecture]):

| Mechanism | Job | Example |
|---|---|---|
| Context engineering | Put task-relevant information inside the agent's reasoning horizon | Relevant source, specs, architectural models |
| Project instructions | Preserve guidance across sessions | `AGENTS.md` with conventions and build procedures |
| Tools and MCP | Give access to engineering resources and operations | Repo search, issue retrieval, test execution |
| Skills | Package a reusable procedure for recurring work | Investigate, repair, test and report a defect |
| Feedback loops | Revise an attempt from observations | Test failure → investigate → correct |

"**None of these mechanisms establishes that the agent has interpreted its instructions correctly or that its output satisfies the specification**" ([Lecture]). They are all process design. Tolerance needs a check (§5, §7).

**What goes in `AGENTS.md`** ([Deck 2-5], S8):
- *Include:* concise project guidance; **build and test commands**; coding conventions; review and safety rules; a short architecture map; where the specifications live.
- *Leave out:* one-off task details; bug-specific fixes; unverified assumptions; pasted source files. "More text is not automatically better context" (S5 notes).
- *Verify it loads.* "Different coding agents may use different filenames" (S7 notes). Restart the agent and confirm the instructions were read (S8). The page names `AGENTS.md`; DocAble uses `CLAUDE.md`. The role is constant, not the filename.

**`AGENTS.md` versus a skill** ([Deck 2-5], S19–S20). `AGENTS.md` holds general rules (structure, conventions, test commands). A `SKILL.md` holds one repeatable procedure: a name, a trigger description, a baseline focused-test run before edits, a change → retest → inspect loop, and a full-suite run plus diff review to close. Check two things separately: *discovery* (does the agent recognize the skill?) and *invocation* (did it follow the procedure?).

**Capability is not authority.** "A tool may allow the agent to read an issue without allowing it to modify the issue or approve a change" ([Lecture]). The workshop's hygiene rules ([Deck 2-5], S13–S15):
- Issue data fetched over MCP is "external input, not a new instruction." Treat it as untrusted and check it against the spec.
- "MCP adds tools; the coding agent still controls permissions."
- "Check the tool log—not just the agent's final answer."
- GitHub tokens: fine-grained, least privilege, read-only, short expiry, stored outside the repo, never pasted into chat or committed.

**Evidence is the tests and the diff, not the explanation.** The workshop bug fix goes from 7 pass / 3 fail to 10 / 0 under the rule "**Fix the overlap logic—not the tests or specification**" ([Deck 2-5], S24–S25). The agent's explanation is useful; "the test results and implementation differences provide separate evidence" ([Lecture]).

### From principle to project rule to executable check

The governance document "separates portable engineering principles from rules specific to the repository, and the two reach enforcement along one chain: **principle, project rule, executable check**" ([Lecture]). DocAble's examples ([Deck 2-7], S17):

| Principle | Project rule | Executable check |
|---|---|---|
| A.19 Uniformity over fit | #15 All PDF I/O goes through `PdfModel` | `itext-direct-access` lint |
| A.14 Never silent-catch | #8 Log, re-throw, or justify the swallow inline | (check not named on the slide) |
| (not named on the slide) | #27 No shell scripts | `lint-no-shell-scripts.py` |
| (not named on the slide) | #29 Agent CWD-drift defense: `isolation: worktree` in every brief | `agent_prompt_lint.py` |

"A rule without a named enforcer is guidance; a rule with one is a control" (S17 notes). DocAble's `CLAUDE.md` is a *budgeted* artifact: a mission, 24 portable principles and 66 numbered project rules, never renumbered, with a lint capping it at 1,300 lines / 100 KB because "every bullet costs context on every dispatch." A rule earns a place only if it is regression-preventing, non-derivable from the code, and non-local (S16).

**Starter templates.** The course publishes these artifacts in its `downloads/` directory: `CLAUDE-starter.md`, `EPIC-TEMPLATE-starter.md`, `design-doc-template-starter.md`, `agent-brief-starter.md`, and a runnable `governance-lint-example.py`, among 18 starters ([downloads]; [Lecture]). They are one practitioner's mature setup, offered as a menu, not a requirement.

> **In MAGE.** "A rule without an enforcement pointer is a hope, not a gate" (§14, KF 16). The repository ships three skills: `self-governance`, `self-operations` and `self-communicate`.

## 3. STRATEGY.md and the work artifacts

`STRATEGY.md` lists what we should be working on:

- **Deploy gates**: work that must be finished before the next deployment.
- **Near-term items.**
- **Long-term items.**

*Margin:* an Epic template (`epic-template.md`) is copied to `docs/active/<thing>/` for each new piece of work.

**The Epic template.**

- It is written for Opus to read and fill in.
- A "Description" section is followed by a "Validation" section that says how we will know the work is right.
- It asks: **which files will this work touch?**
- *Margin:* filling it in forces the agent to elaborate the system models. If the models are incomplete, it adds the models or details needed to express the work.

**The design document.** It is a separate artifact from the Epic, not a section of it. The Epic answers "what must change?"; the design document answers "**what must remain true?**" It covers intended structure, invariants, failure modes, observability, and the controls that preserve the system's obligations ([Lecture]).

**Delegating the phases.** The template splits the work into phases and draws them as a schedule diagram, so independent phases can run at the same time.

- For each phase, it states which model may do it: Haiku, Sonnet or Opus.
- Fable does the planning step. Opus does the later steps.
- The orchestrator launches a **second Fable** to question the first Fable's models and design. *Corrected:* the notes said it "resolves every open question." The lecture's reviewer "challenges questionable decisions, and **refers whatever it cannot resolve back to the engineer**" ([Lecture]). The engineer rules on what review cannot settle.

> **In the lecture.**
> - **Strategy:** a work queue with deploy gates, near-term and long-term items. "The strategy records what should be done, not yet how." The engineer edits it in natural language (or asks the orchestrator to); the agent maintains the structure; "the orchestrator never invents priorities" ([Deck 2-7], S4).
> - **Epic:** "a persistent work order, not a prompt." It lives in `docs/active/<epic>/` with `epic.md`, one folder per phase, and `dod/` (S5). It "identifies the relevant system models, proposes new ones where necessary, describes the affected components and types, specifies how the result will be validated, and decomposes implementation into phases with their dependencies" ([Lecture]). "The validation plan targets intended properties, not the implementation" (S7). "An Epic with no explicit definition-of-done is done by assertion" (S8 notes).
> - **Design doc sections** (S9): context and the failure it kills; genre check ("who solved this before"); the design; type-system posture; invariants with stable IDs; dynamics ("what breaks at T+100"); observability; as-built vs design; enforcement ("maps every invariant to the test that pins it"); analyses; open questions. "Each required section earns its place because omitting it caused an incident."
> - **The engineer's three decisions:** prioritize, decide what plan review cannot resolve, accept. "Everything between those three decisions is delegated" ([Lecture], Figure 2).
> - **Model tiers.** "Spend expensive reasoning on planning and review. Implementation can use cheaper models" ([Deck 2-7], S10). The page names no specific models; the decks use "strong / middle-grade / cheapest model" (S11) and the brief template says "Opus or Sonnet" (S18). The Haiku and Fable assignments above come from the talk, cited in §14.
> - "Independent review is a control, not a correctness proof… a reviewer that shares the author's context shares the author's blind spots" (S10).

> **In MAGE.**
> - The chain is "the Epic is the effort, the design doc is the plan, the brief is the dispatch."
> - Epic sections are Rationale, Models & invariants, Related functionality, Risks & blast radius, Cost, Phases (each with acceptance and prerequisites), Definition of Done, Open questions, and Open forks for the user.
> - "Phase 1 is ALWAYS planning/design… Never dispatch implementation speculatively."
> - Talk: "The first phase, maybe have a Fable-grade model do that… The second phase, it's all just make-work, have a Sonnet do this one. The third phase is a little tricky, maybe an Opus will have to do it."
> - The second reviewer is the **independent design review**: a strong model that did not write the design re-derives it from the code, rules RATIFY or REVISE, and "the reviewer wins". (My reading, unverified: "reviewer wins" settles disputes between the two agents, while the Epic's "Open forks for the user" still go to the human, which fits the lecture.)
> - In the repository, `STRATEGY.md` is the file the pre-compaction hook writes ("bank the strategy and hand-off"), so a session can be rebuilt after memory loss.

## 4. Running the queue

- **Push** triggers checks. *Corrected:* in the lecture's final design, landing runs only the cheap admission checks; the full suite runs on its own timer (§7).
- **Commit** may carry metadata. *(Left as an open question in the notes; answered below.)*
- Once the template is filled in, the phases become scheduled tasks. Whenever one finishes, the agent reads the next block of work, does it, and fills in the same template for the tasks after it.
- A **validation agent** checks that every commit the plan expects is actually present.
- Later, an **audit Fable** checks that everything is in order.
- Sometimes an agent simply dies. Some nudging is needed to keep the process going and to make sure reasoning is written down. The setup still needs high-level human oversight.

> **In the lecture.** The validation agent and audit Fable are the lecture's **Definition of Done audit**: "a separate agent checks the Definition of Done, confirms that the expected changes were integrated, and reviews the evidence offered for completion" ([Lecture]). It checks "Commits present? Work complete? Tests passing? Evidence sufficient?" and "frequently discovers additional issues." "**An agent reporting done is not the process accepting done**" ([Deck 2-7], S24). Each dispatch is bounded by a brief with scope, non-goals, a hard time cap ("document what you found and stop") and acceptance criteria. "A partial result with an honest report beats a run that claims success" (S18–S19).

> **In MAGE.**
> - Commit metadata is real: agent commits carry a `Commit-of i/N` trailer and a `caused-by: epic:<id> | reflection:<id> | ad-hoc` field from a closed list.
> - The "validation agent" matches `epic_close.py`, which checks that every cited commit is reachable from `main`.
> - The "audit Fable" matches the Definition of Done's "Final-Opus trust-nothing" review at HEAD. The names "validation agent" and "audit Fable" are the notes' own; the generic mechanism is now published in the lecture.
> - Dead agents: an append-only agent registry, tombstone commits, and a recovery runbook ("Report first; never auto-destroy").
> - Nudging: a turn-stop hook that refuses to let the loop rest while approved work remains.

## 5. Git hooks, CI and agent hooks

Git verbs: `git switch`, `pull`, `commit`, `push`, `status`.

- *Corrected:* the notes said "code must pass all tests before it is pushed." The lecture: "a pre-push hook runs **inexpensive** checks before allowing a push" ([Lecture]). Cheap checks pass before push; CI enforces for everyone.
- Git hooks make these checks run automatically.
- The hook lives at `.git/hooks/pre-push` (or in a versioned folder set with `core.hooksPath`). *(The notes wrote `prepush.sh`; git looks for the exact name `pre-push`, with no extension. "A misnamed file simply never runs, which is a silent process failure" ([Deck 2-7], S20 notes).)*
- If the hook is present, git must run it. Exit code 0 means everything is fine. A non-zero exit code (for example 1) means git refuses the push.
- Commit message format: a subject line under 50 characters, then a body that justifies the change and ends with the issue it closes, e.g. `Fixes #17`. A `commit-msg` hook "requires traceability information" ([Lecture]).

*Margin:* this is similar to GitHub Actions.

- A CI/CD pipeline on GitHub runs before anything is pushed to production.

> **In the lecture.** Local hooks are "cheap, fast checks / immediate feedback / **can be bypassed**." Hosted CI gives "broader validation / shared evidence / **enforced for everyone**." "Local hooks are a convenience layer; CI is the control layer" ([Deck 2-7], S20). The lecture names no CI product; GitHub Actions is the notes' choice.

> **In MAGE.**
> - The repository's hooks are `pre-commit` (changed-file lints, fast tests, then a marker keyed by the tree's SHA), `pre-merge-commit` (read-only checks) and `pre-push` (builds and test tiers, scoped by changed paths).
> - Hooks are installed with `git config core.hooksPath hooks`, so they are versioned with the code.
> - The CI rule: "Moving a check between stations is allowed; deleting one is not."

### Claude hooks (*margin*), labelled by authority

Agents support the same kind of hook, "one layer up" ([Lecture]). The lecture's key point is that hooks differ in **authority**: some refuse, some only remind.

| Hook | What it does | Authority |
|---|---|---|
| **Pre-dispatch** | Confirms the isolated worktree exists, the work order is valid, and the brief was built from the template and linted | **Deterministic.** "Exit 1, no launch" |
| Traceability check | Confirms the work traces to an Epic | Deterministic, if implemented as a lint |
| **Start** | Gives the agent its task-specific instructions | Reminder |
| **Return** | *Corrected:* the notes said "forcibly notify the orchestrator." The lecture: "a hook **reminds** the orchestrator to examine the result, integrate what is acceptable, and dispatch the next phase" | **Reminder.** Guarantees nothing |
| Reflection (§8) | Asks the agent to reflect every 30 minutes | Reminder |

- If the work is well-formed, merge it and start the next step.
- Give subagents the context they need, especially when the next phase starts.

> **In the lecture.** Pre-dispatch is labelled "deterministic" and start/return "prompt reminders" ([Deck 2-7], S21). The brief linter `agent_prompt_lint.py` "checks every brief before spawn: exit 1, no launch." "A malformed brief cannot be dispatched, not merely unlikely to be. The bypass is human-only and audit-logged" (S18–S19). Why it matters: "At a handful of dispatches, forgetting is tolerable / At thousands, it is a routine (and preventable!) failure" (S15).

> **In MAGE.**
> - Talk: "These are hard controls. Claude can't cheat, it has to run it." Read this narrowly: the hook's *firing* is guaranteed, but only a blocking payload is a control. The course starter says the same: "Its firing is hard… Its payload is either — a hard block… or soft guidance" (`CLAUDE-starter.md`, A.3.7). The quote holds for pre-dispatch and the brief lint, not for return or reflection reminders.
> - Events used: before/after a subagent, before stop, before/after compaction, session start, before a tool call.
> - Dispatch-time checks are done by a **brief lint**: worktree marker, dispatch id, mandatory snippets, role, real `file:line` citations, declared file footprint. Exit 1 means do not launch.

## 6. The first commit, progress commits and `query-repo`

- The git `commit-msg` hook checks that every commit message is well-formed.
- When an agent starts work, its **first commit** must:
  - state the plan;
  - refine the list of target files (*margin:* "tgt" means target files);
  - name those target files in the commit message.

  The agent has to work out the specifics itself.
- **Later commits report progress against that first commit.** This is what the first commit is *for*: it "lets the orchestrator tell completed work from an agent that stopped early" ([Lecture]). "Progress is measured against the declared plan, not against claims" ([Deck 2-7], S22).
- `query-repo <file>` answers, for one file: which models and static analyses cover it, which tests cover it, and which invariants and properties it must obey.
- If the first commit does not follow the format, the hook reminds the agent of the process.
- Subagents verify and improve the system.
- Automate, and build the intelligence into the system, so it regulates itself. *Corrected:* the notes added "and keeps moving without a human." The lecture keeps three decisions with the engineer (prioritize, rule on unresolved review items, accept), and "recognizing that the factory itself needs redesign… remains the engineer's responsibility" ([Lecture]). The factory runs *between* human decisions, not without them. §4 and §9 already say this.

> **In the lecture.** Query Repo "retrieves the models, tests, static analyses, and invariants associated with a file, so an agent about to modify that file can collect the relevant obligations before it changes anything… The factory simply stops charging it for knowledge the engineering organization already holds" ([Lecture]). "Constraints are learned before they are violated, not from failed tests" ([Deck 2-7], S23). DocAble's `pre-commit` hook rejects any agent commit without a `Commit-of: i/N` trailer (S22 notes).

> **In MAGE.**
> - This is the **sentinel first commit**. On the first commit it checks the worktree root, the per-agent marker, the branch name and the working directory, and aborts at once if any is wrong. That turns a 60-minute failure into a 1-minute one.
> - `query-repo` is the repository's `repo-query` CLI. **Dynamic context injection** uses it to push "the rules for the files you are about to touch" into the brief, and runs it in reverse in CI to report only what the agent broke.
> - "Bake intelligence into the system" is **governance conversion**: each recurring failure becomes a model, a sensor, a validator or a gate.

## 7. Testing and admission: block cheaply, sweep behind, fail closed

- We optimize as engineers.
- A single GitHub Action is not the whole story for running a test suite.
- Limit what data GitHub is allowed to access.
- Use separate staging clusters so tests run separately, in separate phases.
- Running tests constantly is not productive: it costs compute and agent bandwidth. *(Arrow in the notes: this follows from "we optimize as engineers".)*

**What DocAble tried first, and abandoned.** The notes recorded: ★ "Every commit gets a test-suite run before it lands. To save cost, run the suite only over the commits that reached `main` in about the last hour, as one batch." The lecture confirms this was real, and that it was **the first design, later replaced**. DocAble "originally validated batches of completed changes at regular intervals." As the suite grew to about thirty minutes, validation became the limit on how fast work could be integrated. Validating in the background on every land "replaced one bottleneck with another" and overwhelmed the host (a load average of 206 or higher) ([Lecture]; [Deck 2-7], S26 notes).

**The final design** ([Lecture], "Improving the infrastructure"):

1. **Cheap admission checks run synchronously** and decide whether a change may land.
2. **A broad validation sweep runs on its own timer**, so its cost does not scale with how often work lands.
3. **When the sweep finds a blocking failure on `main`, it records an alert, and a pre-dispatch gate refuses to launch further agents** until the condition is handled, "so no agent silently inherits a known-bad main."

**The obligations this design creates** ([Lecture]):
- The sweep must actually be scheduled and running. In DocAble the cron job "was declared in the environment's cron manifest but had never actually been installed… A manifest entry is not an installed job" ([Deck 2-7], S27 notes).
- Alerts must be handled, not merely dismissed.
- The gate must fail closed. **Acknowledgment is not health:** "Acknowledging the alert reopens the gate without establishing that main is healthy… only a passing sweep establishes that main is healthy" (page figure caption and alt text). DocAble still has this weakness: "the factory's own controls must be validated like any other engineered component" (S28 notes).
- The sweep interval "bounds the nominal delay until the next sweep starts. It does not bound the time until a defect is detected" (S28 notes).

The engineering judgment is "which checks must block a change, which may run behind it, and what recovery the factory owes when a late check fails" ([Lecture]). DocAble's tiers: local checks at commit, cheap checks at landing, the periodic sweep over `main`, and the deploy sequence, which re-runs everything ([Deck 2-7], S28 notes).

> **In MAGE.**
> - Tests run as a staircase: "commit → cron → merge-train → deploy." The "cron" stage is the lecture's timed sweep.
> - Pre-commit tests follow a "1-second rule".
> - The **merge train** lands batches of non-conflicting agent branches and re-tests the merged tree once per batch. This differs from the lecture's final account, where the broad sweep is decoupled from landing. Treat the lecture as current.
> - Deploys pass a canary with no traffic, then smoke tests, then promotion.
> - A host lock runs one test suite at a time, so parallel agents do not corrupt each other's results.

## 8. Fable's planning process

It needs good engineering models, developed inside `epic-template.md`.

- The planner must **not** spend all its time reasoning and rediscovering the constraints.
- Make the agent's rediscovery of everything **deterministic**.
- Let the agent focus on making the code work.
- Don't spend all the time waiting for the test suite or re-deriving facts. Make as much as possible deterministic.

**Testing.**

- Should tests be written first? That way they are not biased by the implementation: they describe what must be built without constraining how.
- In practice, it makes no real difference whether tests come before or after.
- Tests just need to be good. Before or after is irrelevant.
- The tests are part of the planning template (the Epic template).

*Margin:* Jira and GitLab integration is not done.

**Skills.** Davis has written some skills but does not really use them. *This is a personal anecdote, not advice against skills.* The lecture treats skills as one of the five standard equipping mechanisms (§2), and writing one is the workshop's required exercise ([Deck 2-5], S21). Shopify is cited as improving merge rates partly through "reusable project instructions and skills" (self-reported; [Lecture]).

**Another hook: reflection.**

- It is attached to the return step. If more than 30 minutes have passed since it last ran, the agent reflects on what is going on and works to fix the issue. (A reminder, not a gate; see §5.)
- Sometimes the agent fails to land other agents' work, deletes the worktree, and then must update the logs and redo everything.

**What agents are and are not good at.**

- They are fairly good at course-correcting, but bad at making changes.
- They optimize the existing environment and the way the code is done. They do not throw out the idea and leap to a different one.
- They are bad at insightful leaps.
- They can see that something is not working and find new ways to make it work, but they cannot get out of a rut.

> **In the lecture.**
> - "Determinize what you can / Spend reasoning on problems that require reasoning." Avoidable reasoning: "reconstruct constraints · rediscover tests · repeat mistakes." Justifiable reasoning: "planning, design, diagnosis, engineering decisions." "Eliminate reconstruction and waiting, not engineering reasoning" ([Deck 2-7], S29).
> - On tests, the workshop's loop is *baseline first*: run focused tests before editing, then change → retest → inspect, then close with the full suite and a diff review ([Deck 2-5], S20, S26). Never edit tests or the spec to make them pass (S25). Anthropic's harness likewise keeps features "marked failing until verified" and tells the agent "not to delete or edit tests to make them pass" ([Deck 2-6], S16 notes).
> - The rut: agents "will often keep optimizing an inadequate process rather than proposing a different one" ([Lecture]). Inner loop, "agents repair"; outer loop, "the engineer redesigns." "The factory will not notice its own wrong shape" ([Deck 2-7], S31).

> **In MAGE.**
> - "Improve the representation before buying more inference."
> - Models answer an engineering question "without continually reconstructing [it] from implementation".
> - On tests, the book is evidence-first, not strict TDD: "Validate the change, not the producer's story", prefer property tests, and derive the required test set from the model (the **test-obligation census**).
> - Reflection hook, from the talk: "The hook fires every 30 minutes… 'Have you run into any recurring issue in the last 30 minutes, or any architectural anti-pattern… please call the self-governance skill.'"
> - The rut matches the autoscaler story: "for weeks the agents made it better and better, with every improvement colliding with the same boundary." Only a human architectural decision fixed it.

## 9. The human engineer

- The system amplifies the professor's own engineering expertise.
- It would not work well without that expertise.
- Without it, he could not push the system in the right direction to make it better.
- Don't use agents when you are lost. You should feel like a **commander in charge of a fleet of moderately competent interns**.
- Engineers are the people society trusts to exercise informed control over systems.
- When lost, ask: "I'm lost. Tell me what concepts I need for this to make sense."
- Work until you lose control. Then pause, retreat until you are back in control and understand the system, and resume.

> **In the lecture.** "Engineers are the people society entrusts to exercise informed control over complex systems." "The goal is not maximum autonomy. It is productive delegation under informed control" ([Deck 2-7], S31). "People move to where judgment has the most leverage: intent, architecture, and the gates" ([Deck 2-6], S26).

> **In MAGE.**
> - "Delegating a decision to a machine does not delegate the responsibility." The engineer "must retain informed control over the resulting system" (§7.4).
> - The talk names three stances: autonomy (fast, no controls), oversight (review every line), and **governance** (the human writes policy into the environment). MAGE is the third.
> - The "interns" and "lose control, retreat" phrasings are **not found in the sources**.

## 10. Measuring the factory

*New section; the handwritten notes do not cover it. Source: [Lecture], "Measurement for decision-making".*

The question is "how economically can the organization produce acceptable changes to its software?" The lecture's measurements:

1. **End-to-end cost and latency of accepted changes.**
2. **Amount of human supervision required.**
3. **Frequency of rejected or reverted changes.**
4. **Failures observed after deployment.**

These are traded against each other: "stronger checks may reduce defects but increase latency, while faster admission may reduce waiting at the cost of additional diagnosis and recovery" ([Lecture]).

- **Review is the usual bottleneck.** Spotify and Uber both found verification and review becoming the constraint. "Increasing implementation capacity does not automatically increase the capacity to evaluate and admit changes", so the factory "must allocate scarce supervisory attention as deliberately as it allocates implementation capacity" ([Lecture]).
- **Promote checks on evidence.** Cloudflare promoted policies "from advisory guidance to enforced requirements"; the lecture calls that "an Alignment decision" ([Lecture]).
- **No maturity ladder.** The industrial cases "are not stages of a universal maturity model" ([Lecture]).
- **Instruction-only upgrades are suspect.** "Upgrades that only add more agent instructions, without a way to check results, are worth questioning." A strong upgrade names "a measurable signal, such as fewer regressions caught late or less time from issue to deployed change" ([Deck 2-6], S24 notes).

**For this repo** *(my suggestions, not the lecture's)*: the cheapest signals already exist in git and the deployment. Count reverts and fix-up commits on `main`; note each failed `/system/health` after a deploy; and keep `mage_take.md` C8's tally of red `drifter check` results (fewer than 10 false alerts in 100 before the check becomes blocking). That tally is the repo's one existing measurement, and it is a Cloudflare-style advisory-to-enforced promotion.

---

## 11. The principles in one place

Tags: **P** = process design (how work is routed and equipped), **T** = tolerance (what variation is accepted, and what refuses the rest). **P+T** = the principle spans both. Tags follow the lecture's definitions ([Lecture]); rows 1, 3 and 15–17 are my classification.

| # | Principle | Tag | What it means for agents | Mechanism you can run |
|---|---|---|---|---|
| 1 | **Modeling**: externalize knowledge into purposeful models | P+T | The agent queries facts instead of rediscovering them; models also state what checks enforce | `query-repo <file>`, models in `docs/diagrams/` |
| 2 | **Alignment**: enforce selected obligations | T | Rules hold even when the agent forgets them | hooks, gates, CI |
| 3 | **Guidance ≠ enforcement** | P+T | `AGENTS.md` informs (P); a check decides (T). A reminder guarantees nothing | rule index where every rule points to its check |
| 4 | **Earliest decidable boundary** | T | Cheap checks at commit/push, drift at agent return, intent at Epic close | pre-push → CI → DoD |
| 5 | **Constraint / sensor / validator / gate** | T | Each check has one role; gates need adequate evidence | control catalogue |
| 6 | **Agreement ≠ correctness** | T | A drift check needs an independent "ought" | invariants file (`INV-*`) |
| 7 | **Plan first, by template** | P | Phase 1 is always design; the engineer rules on unresolved items | Epic, design-doc and brief templates (`downloads/`) |
| 8 | **Typed roles and model tiers** | P | Strong models plan and review; cheaper models implement | `.claude/agents/*` with `model:` |
| 9 | **Independent review** | P | A non-author reviews the plan; review is a control, not a proof | plan review, final DoD audit |
| 10 | **Isolation** | P | One worktree per agent; disjoint file footprints | brief lint, sentinel first commit |
| 11 | **Block cheaply, sweep behind, fail closed** | T | Cheap checks decide landing; a timed full sweep guards `main`; a red `main` stops dispatch until a passing sweep | pre-push, CI, timed sweep, pre-dispatch gate |
| 12 | **Provenance** | P | Every commit says why it exists; progress is measured against the first commit | `Commit-of i/N`, `caused-by:` |
| 13 | **Memory lives in files** | P | Rebuild state after compaction or a dead agent | `WORK-ITEMS.md`, orchestrator log, registry |
| 14 | **Lifecycle hooks, labelled by authority** | P | Pre-dispatch refuses; start, return and reflection only remind | dispatch lint (gate); `SubagentStop`, `Stop`, `PreCompact`, `SessionStart` (mostly reminders) |
| 15 | **Governance conversion** | P+T | A recurring failure becomes structure, not a reminder | conversion log, self-governance skill |
| 16 | **Engineering capital depreciates** | P+T | Instructions, models and tests go stale; controls need an owner and a retirement condition | daily review, control catalogue |
| 17 | **Responsibility stays human** | P+T | The engineer prioritizes, rules on open forks, accepts, and redesigns the factory | open-decisions file, ruled-decisions file |
| 18 | **Principle → project rule → executable check** | T | A rule without a named enforcer is guidance | numbered rule index + lint per rule (e.g. `itext-direct-access`) |
| 19 | **Capability ≠ authority** | T | A tool may read without being allowed to write, merge or deploy; MCP data is untrusted input | least-privilege tokens, harness permissions |
| 20 | **Measure the factory** | P+T | Judge changes by cost, latency, supervision, reverts and post-deploy failures | §10 |

## 12. This repo: setting up and running tests locally

*Verified against the repository on 2026-11-05 by reading files. Neither `README.md` nor `AGENTS.md` documents these commands. I derived them from the files named, and did not run the install or the server.*

- **Python:** 3.12 or later (`pyproject.toml`: `requires-python = ">=3.12"`; `Dockerfile`: `python:3.12-slim-trixie`).
- **Dependencies:** `pip install -r requirements.txt` (the `Dockerfile` does this; the list is fastapi, uvicorn, pydantic-settings, pyyaml, coverage, pytest, jsonschema). The service also needs `git` on the path, since the connector shells out to it.
- **Tests:** run `pytest` from the repository root. `tests/conftest.py` puts `Source/` on the import path, so no install step is needed for tests. On 2026-11-05, `pytest --collect-only` collected **277 tests**. Pass status was not checked.
- **The `drifter` CLI:** `pyproject.toml` declares `drifter = "drifter.cli:main"`, so `pip install -e .` should provide the command *(unverified)*.
- **The web service:** the `Dockerfile` starts it with `uvicorn --app-dir Source GitHub_Connector.api:app --port ${PORT:-8000}`. It writes runs to `DRIFTER_RUNS_DIR`. Running this locally is *unverified*.
- **Deployment:** `README.md`: Railway deploys "automatically on every push to `main`". Nothing checks a change before it does (§13, row 1).

The lecture says build and test commands belong in `AGENTS.md` ([Deck 2-5], S8). They are missing there; adding them is row 4 below.

## 13. What DocumentationModelDrifter is missing, in priority order

Checked against the repository on 2026-11-04 and re-checked on 2026-11-05. **What it already has** is strong process design: `AGENTS.md` with house rules; `docs/README.md` (a docs map that says which doc wins); `GLOSSARY.md`; ADRs; modeling rules (`docs/agents/modeling.md`); three schema-validated models with golden tests; a ticket folder; 277 tests; and a draft `STRATEGY.md` with raw notes from this lecture. **What it lacks is tolerance:** no `.github/`, no `.claude/`, no `CLAUDE.md`, only sample files in `.git/hooks`, no `core.hooksPath`. `STRATEGY.md` and all of `docs/deviations/` are untracked. In the lecture's terms, the `AGENTS.md` rule "don't call it done until the checks pass" is a reminder with no gate behind it.

The order follows the lecture: first, a gate on the path to production; then the cheap steps that make rules checkable and progress visible. The heavier DocAble machinery comes last. It pays off at fleet scale, and the lecture presents DocAble as "one working system… not a claim that every organization should reproduce it" ([Deck 2-7], S1).

### Do first

| # | Missing piece | Why it matters | Fix / where to look |
|---|---|---|---|
| 1 | **No admission gate before an auto-deploying `main`.** Every push to `main` goes to production, with no hook, CI or branch protection in front of it. | A change reaches production with no automated check at any boundary. This is the one gap the lecture would treat as urgent. | `mage_take.md` **C1–C4** (one PR workflow running `pytest`, `ruff`, `pip-audit`) and **C6** (branch protection as the gate). The lecture's "inexpensive admission checks run synchronously" ([Lecture]). Branch protection cannot be seen from the clone *(unverified)*. |
| 2 | **Installed git hooks.** `.git/hooks` holds only samples, and nothing sets `core.hooksPath`. | No fast local feedback; no commit-message traceability. A convenience layer, not the control (CI is). | A versioned `pre-push` running fast tests and a `commit-msg` check, installed via `core.hooksPath`. Example: `hooks/`, `scripts/setup.sh`. |
| 3 | **No measurement.** Nothing records the cost or latency of accepted changes, reverts, or post-deploy failures. | Without numbers, there is no basis for making a check blocking or for removing one. | §10. `mage_take.md` C8's false-alert tally is the one existing measurement. |
| 4 | **Rule index with enforcement pointers.** `AGENTS.md` rules have no check behind them, and it omits build/test commands. | "A rule without a named enforcer is guidance; a rule with one is a control." | Add test commands (§12) to `AGENTS.md`; number rules and name each one's check. `downloads/CLAUDE-starter.md`, `governance-lint-example.py`. |
| 5 | **An independent "ought".** No invariants file; drift compares "is" with "previous is" (`mage_take.md`). The tool does not run on its own repo. | The tool can say "changed", not "wrong". | `mage_take.md` C5 (`drifter check` on its own code, warning only) and C7; authored forbidden-import rule. Example: `docs/invariants/INVARIANTS.md`. |
| 6 | **`STRATEGY.md` as a tracked queue**, and a **stale doc map**: `docs/README.md` still calls `contract/model-golden-outputs.json` "not yet written". | The strategy is raw jottings, not a queue with deploy-gate, near-term and long-term items. The stale entry is the lecture's "instructions can become stale" in practice. | Restructure and commit `STRATEGY.md`; fix the doc-map line. |

### Do when work grows past one agent at a time

| # | Missing piece | Why it matters | Where to look |
|---|---|---|---|
| 7 | **Epic / design-doc / brief templates** and a `docs/active/` area. | `STRATEGY.md` describes them, but they do not exist. | `downloads/EPIC-TEMPLATE-starter.md`, `design-doc-template-starter.md`, `agent-brief-starter.md`; example repo `docs/templates/`, `docs/active/`. |
| 8 | **Independent plan review and DoD audit.** | No second agent questions the plan; "done" is self-certified. | `phase-1b-review` template, `bin/mage epic close`. |
| 9 | **Agent hooks.** No `.claude/settings.json`. | No pre-dispatch gate, no return reminder, no pre-compaction bank, no reflection. Only the pre-dispatch gate is a control. | `.claude/settings.json`, `.claude/hooks/`. |
| 10 | **`query-repo` and context injection.** | Agents grep for rules instead of receiving them. The tool's own models could serve this. | `bin/mage query-repo`, `bin/mage constraints-for`. |

### Fleet-scale DocAble machinery (lowest priority here)

| # | Missing piece | Why it can wait | Where to look |
|---|---|---|---|
| 11 | Timed full sweep with alert and fail-closed dispatch gate | Only needed when the suite is slow and agents land faster than it runs; 277 tests can run synchronously in CI today *(suite run time unverified)*. | [Lecture], "Improving the infrastructure" |
| 12 | Typed agent roles with model tiers | Model choice is ad hoc per session, which is fine with one agent at a time. | `.claude/agents/` |
| 13 | Memory files: work-items file, orchestrator log, agent registry | Needed when agents die or compact mid-epic. | `docs/state/` |
| 14 | Governance conversion log and daily review | Lessons stay in chat instead of becoming structure. | `docs/governance/`, `docs/operations/daily-review.md` |
| 15 | Open-questions and ruled-decisions files | Judgment calls get re-derived. | `docs/decisions/` |

A fitting closing point: DocumentationModelDrifter is a drift detector, and the lecture's deepest point is that models and instructions depreciate unless something checks them against reality. Pointing the tool at its own `docs/` and `AGENTS.md` claims would be the project's natural Query Repo and its first real tolerance check. Making that check blocking only once its false-alert rate is measured (row 3, `mage_take.md` C8) would apply the lecture's Alignment decision to the project's own product.

## 14. Appendix: the cited research

The deep research behind these notes, merged in from the former `mage-research.md`. Its key findings are numbered; the notes above cite them as "KF n".

Source material: James C. Davis, *Model-Based Agentic Engineering* (Edition 1, 2026), and its companion repository. Researched 2026-11-04 from a full clone of the repository (commit `a92e6de`) and the published book index. Every repository path below is relative to <https://github.com/davisjam/model-based-agentic-software-engineering/blob/main/>.

**Updated 2026-11-05** against the course lecture **"Building with Agents"** (<https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/>, decks 2-5 to 2-7). Where the lecture changes a finding, a **Lecture update** note says so. Where they differ, the lecture is the newer account.

### Executive Summary

MAGE starts from one premise: "Commodity intelligence makes implementation abundant relative to engineering judgment" (`book/part1/00-part-intro.md`). When agents write code cheaply, the scarce things become judgment, representation, evidence and enforcement. MAGE answers with two principles. **Modeling** writes the knowledge an agent would otherwise rediscover into explicit, purposeful models. **Alignment** turns selected obligations into mechanisms (constraints, sensors, validators and gates) so that meeting them "does not depend on the agent remembering, agreeing, or self-certifying each time" (`book/part1/1.4-the-new-engineering-problem.md`). A third loop, **governance conversion**, turns each recurring failure into durable structure.

The companion repository shows how this works in practice for a fleet of coding agents. An orchestrator session plans with templates (Epic → design doc → brief) and dispatches typed roles (a strong model plans and reviews, a cheaper model does mechanical work) into isolated git worktrees. Every hand-off is checked by a deterministic mechanism. A brief lint blocks a malformed dispatch. A **sentinel first commit** aborts an agent in a broken worktree within a minute. A pre-commit hook runs changed-file lints and fast tests and requires commit trailers. A **merge train** lands non-conflicting batches. (The lecture's final account separates landing from the full test run: cheap checks decide landing, a timed sweep tests `main` behind it, and a red sweep stops new dispatch; see finding 11.) An Epic **definition of done** closes only after a fresh, independent reviewer re-runs everything at HEAD. Agent lifecycle hooks (turn-stop, pre-compaction, session-start, a 30-minute reflection) keep the loop moving and bank state before memory is lost. Nothing relies on the model's memory: state lives in committed, dated files.

The main gap for this project (DocumentationModelDrifter) is not modeling. Its models, docs map and glossary are strong. The gap is **enforcement and orchestration**. It has no installed git hooks, no agent hooks, no Epic or brief templates, no typed agent roles, no CI, and no file that survives an agent's memory loss (a work-items file or an orchestrator log). `mage_take.md` reached the same conclusion about the product: "a well-built sensor and validator with a governance plan that exists only on paper."

### Key Findings

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

### Detailed Analysis

#### 1. Orchestration: who does what

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

#### 2. Roadmap: the document chain

The roadmap is a chain where each document has one job: "the Epic is the effort, the design doc is the plan, the brief is the dispatch" (`brief-linting.md`). Around it sit:

- **Open decisions → ruled decisions.** `OPEN-DECISIONS.md` lists what the author must rule on. Each ruling is recorded verbatim in `DECISIONS-RULED-<topic>-<date>.md` "so an implementing wave cites a decision rather than re-deriving one."
- **Phase checkpoints.** `DONE-phase-<X>.md` records the branch, base SHA, footprint, gate results, and "decisions taken that the spec left open", each pinned by a test and waiting for a ruling.
- **Dated audits** replace present-tense gap lists, because "a gap list asserts the PRESENT TENSE… so it is false the moment the system moves" (`CLAUDE.md`).

#### 3. Alignment through tests and hooks

The pattern is to inject the rule at the start and enforce it at the end. Dynamic context injection gives the agent the rules for its files. The pre-commit hook then checks the same rules (talk L169–171). Git hooks guard what is written; lifecycle hooks guard what the loop does (`pre-commit-hook.md`, "Counterpart").

On test-first versus test-after, the book's stance is evidence-first, not strict TDD. "Validate the change, not the producer's story" and "Done is a claim, not a stored fact" (`book/part4/4.4-engineering-the-environment.md`). It prefers property tests to single examples and derives the required test set from the model (the **test-obligation census**, `book/appendix-engineering-moves/derive-the-obligation-set.md`). This matches the notes: tests must be good and independent of the implementation's story. Whether they are written first matters less.

#### 4. Ten engineering moves (Appendix B)

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

#### 5. Operating the environment

- The **daily review** asks five questions: did durable work move; did a trusted representation become doubtful; did an obligation escape enforcement; what did a human have to decide again; what should the environment learn (`book/appendix-operators-reference/daily-review.md`).
- **Brownfield adoption** goes Audit → Drain → Promote. Recover latent models from the code before inventing new ones (`book/part4/4.3-brownfield-engineering.md`).
- **Engineering capital** is durable structure that lowers the future cost of change. It depreciates, so each control needs an owner and a retirement condition (`book/part3/3.4-governance-conversion.md`).

### Contrarian Views And Risks

- **The tower of governance.** Davis warns against it himself: "You can go too far on this. So you need to find the sweet spot" (talk L189). The self-governance skill says "default to skip". Every control has a carrying cost and can collide with another control (`book/part3/3.5-when-guardrails-collide.md`).
- **Single-author evidence.** Most numbers come from one engineer's factory (DocAble). The book flags its counts as snapshots that will move (`book/part6/6.3-scope-conditions.md`).
- **Tests cost compute and agent bandwidth.** Pre-commit latency "creates pressure to bypass" (`pre-commit-hook.md`). The book's answer is tiering and serializing tests, not running everything on every edit.
- **Self-review is not assurance.** "another probabilistic judgment from the same productive substrate does not automatically create engineering assurance" (`book/part1/1.3-the-agentic-substrate.md`). A second agent review helps, but deterministic checks are what make it hard.
- **Agents optimize locally.** The autoscaler story in §5.2: "for weeks the agents made it better and better, with every improvement colliding with the same boundary." That boundary was an architectural decision a human had to make.

### Open Questions

- Several phrases in the lecture notes do not appear in the published talk or book. The 2026-11-05 lecture now accounts for three of them:
  - a second Fable that questions the first is the **independent design review**;
  - the "validation agent" and "audit Fable" are the **Definition of Done audit** ("an agent reporting done is not the process accepting done");
  - "main in the last hour" is DocAble's **first, abandoned** test design (finding 11).

  Still unsourced: "Impromptu LLMs" (the lecture's nearest is its VISION → WORK / PROCESS / INFRASTRUCTURE slide), "fleet of moderately competent interns" and "go until you lose control". They may come from a Q&A. The rewritten notes keep them as the notes state them.
- The planner's tier is not fixed. The talk says "Fable-grade" for planning at L161 and "the Opus-grade model that's doing the planning" at L233. An earlier decision log notes that Fable was not dispatchable by the harness at the time and that an "Opus second opinion" stood in.
- Haiku does not appear in the repository's role table.

### Sources

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

### Rerun Inputs

```
workflow: firecrawl-deep-research
topic: MAGE agent orchestration, roadmap templates, tests and hooks for alignment
depth: exhaustive
output: markdown
note: Firecrawl CLI was not installed; collection used a git clone of the repository, Exa for the web book, and four parallel readers over the clone.
```

---

Lecture: <https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/>. Example repository: <https://github.com/davisjam/model-based-agentic-software-engineering>. Book: <https://davisjam.github.io/model-based-agentic-software-engineering/book/mage-book/index.html>.

[Lecture]: https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/
[Deck 2-5]: https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/2-5-Agentic-Workshop.pptx
[Deck 2-6]: https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/2-6-Software-Factories.pptx
[Deck 2-7]: https://davisjam.github.io/model-based-agentic-software-engineering/teach/lectures/act-2-delegation-and-control/05-building-with-agents/2-7-Inside-an-Agentic-Software-Factory.pptx
[downloads]: https://github.com/davisjam/model-based-agentic-software-engineering/tree/main/downloads

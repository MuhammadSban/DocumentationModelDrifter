# Drift tools gate deterministically against authored intent

Research on how architecture-model ↔ code drift tools are built, and what that means for this repository. Written 2026-11-02 from seven research notes (Archyl, Erode, Overarc and Tentra, Sruja, established tools, the AI-era doc-sync landscape, academic work). Proposals here are proposals: per `AGENTS.md`, choosing among them is a decision for the team.

**Evidence labels.** **[verified]** means the note's author read it in published source code. **[vendor]** means it comes only from the product's own site, docs or marketing. **[inference]** means it is reasoning, not a sourced fact. Unlabelled claims about established tools and papers come from their primary docs or papers.

## Executive Summary

Every tool in this space that actually blocks anything uses a deterministic check, and every one that compares code to an *authored* model, rule or contract can say "the code is wrong", not just "the code changed". Archyl keeps its LLM for proposing model elements and makes its drift score and conformance rules LLM-free ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy), [Archyl conformance](https://www.archyl.com/docs/features/conformance-rules)). Sruja diffs a reviewed `repo.sruja` against a Tree-sitter code graph and keeps its grader LLM-free even though the rest of the product is now an LLM agent ([Sruja README](https://github.com/sruja-ai/sruja/blob/main/README.md)). Tentra's drift diff is plain heuristics with the "agent as LLM" ([tentra-mcp source](https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/sync.ts)). Overarc claims to compile its diagram into deterministic CI tests ([Overarc](https://overarc.io)). The one LLM-judged tool, Erode, defaults to *not* failing builds ([Erode action.yml](https://github.com/erode-app/erode/blob/main/action.yml)). DocumentationModelDrifter already sits at the strong end on determinism: pure generators, byte-identical models, id-based diffs, exit codes 0/1/2. Its gap is the same one MAGE flagged: for structure and behavior, the committed models are a *baseline* (the last accepted "is"), not an *ought*. In industry and in the reflexion-model literature, the ought is a separate, small, human-authored artifact: allowed/forbidden edges, layer contracts, policies. The derived snapshot is used only as a ratchet of tolerated deviations. The simplest path for this repo is not a rewrite. Wire the existing check into CI on its own code, read authored inputs at the PR base, and add one authored rule file evaluated against the structural edges it already derives. All five named products are young (2025–26), small and mostly single-maintainer, so treat them as design signals, not market proof.

## Key Findings

1. **LLMs propose; deterministic code gates; humans accept.** Archyl says its drift check uses no AI because "AI can produce different results on the same codebase … File path existence is binary" [vendor] ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy)). Its LLM discovery output lands as Pending elements that a person approves [vendor] ([Archyl AI Discovery](https://www.archyl.com/docs/features/ai-discovery)). Sruja: "The deterministic layer (drift, lint, verify-task, intent check) is the independent grader" [verified in README] ([Sruja README](https://github.com/sruja-ai/sruja/blob/main/README.md)). Erode, the LLM-judged exception, sets no temperature or seed [verified] and leaves `fail-on-violations` false by default [verified] ([Erode action.yml](https://github.com/erode-app/erode/blob/main/action.yml)). Research backs this: a 2025 review found LLM-based architecture conformance checking "underexplored" ([Schmid et al. 2025](https://doi.org/10.48550/arxiv.2505.16697)), and naive LLM doc–code checks flag over 90% of functions as inconsistent ([DocPrism, FSE 2025](https://doi.org/10.1145/3832248)).

2. **A snapshot diff measures change, not correctness, and the vendors who ship one say so.** Archyl calls its drift score "a good measure of whether your model still describes the same system, and a weak measure of whether it describes it correctly" [vendor] ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy)). Tentra's `sync_architecture` diffs a saved diagram against a re-scan and tells you to update the diagram, so code always wins [verified] ([tentra-mcp index.ts](https://github.com/rdanieli/tentra-mcp/blob/main/src/index.ts)). That is the same shape as this repo's structural and behavioral check. The reflexion-model paper names the alternative: an engineer-authored high-level model, an extracted source model and a declarative mapping produce convergences, divergences and absences ([Murphy, Notkin, Sullivan, FSE'95](https://www.cs.ubc.ca/~murphy/papers/rm/reflexion_model_fse95.pdf)).

3. **Mature conformance tools pair authored rules with a derived baseline used as a ratchet.** ArchUnit's FreezingArchRule records today's violations in a committed text store, reports only new ones, removes fixed ones automatically, and by default forbids CI from creating the store ([ArchUnit user guide](https://www.archunit.org/userguide/html/000_Index.html)). dependency-cruiser ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)), jQAssistant ([manual](https://jqassistant.github.io/jqassistant/current/)) and Semgrep ([findings in CI](https://docs.semgrep.dev/semgrep-ci/findings-ci)) do the same with a file or a baseline commit. This repo's committed `/models` already works like a commit-based baseline. The authored-rule half is what is missing.

4. **Stable identity is the hard engineering problem.** Archyl admits "a move looks exactly like a deletion" [vendor] ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy)). Structurizr's creation-order ids lose layout on reorder ([Structurizr manual layout](https://docs.structurizr.com/ui/diagrams/manual-layout)). Sruja matches model to code by `canonical_id`, then aliases, then source paths, then id [verified] ([sruja compare.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/compare.rs)). Semgrep keys findings on rule id, file, syntactic context and index, with no line numbers ([Semgrep findings](https://docs.semgrep.dev/semgrep-ci/findings-ci)). This repo already drops line numbers. Its module ids are file paths, so a file move still shows up as REMOVED plus ADDED.

5. **Gates are opt-in thresholds with a distinct "could not judge" result.** Terraform's `plan -detailed-exitcode` returns 0 (no diff), 1 (error) or 2 (diff) ([Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)). act101 returns 2 for "could not judge" and says it "must never be painted green" ([act101 playbook](https://act101.ai/library/ai-architecture-drift-playbook)). Archyl's drift-score Action defaults to a threshold of 0, which never fails [vendor] ([Archyl GitHub Actions](https://www.archyl.com/docs/features/github-actions)). Sruja's `drift-pr` reports only violations new in a PR [verified in docs] ([Sruja KNOWN_LIMITATIONS](https://github.com/sruja-ai/sruja/blob/main/docs/KNOWN_LIMITATIONS.md)). This repo's exit codes (0 aligned, 1 drift, 2 no verdict) already match the best practice.

6. **The core is pure and every surface is a thin adapter.** Erode reaches its model through an adapter interface, the LLM through a provider interface and the VCS through a platform interface, and puts every side effect in a final publish phase [verified] ([Erode analysis pipeline](https://erode.dev/docs/reference/analysis-pipeline/), [architecture-adapter.ts](https://github.com/erode-app/erode/blob/main/packages/core/src/adapters/architecture-adapter.ts)). import-linter uses a `GraphBuilder` port with a grimp adapter and `Contract` plugins whose `check()` is a query over the graph ([import-linter independence.py](https://github.com/seddonym/import-linter/blob/main/src/importlinter/contracts/independence.py)). Sruja turns both the authored DSL and the code scan into one `Graph` type before diffing [verified] ([sruja convert.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/convert.rs)).

7. **Agent integration ranges from a big MCP server to a skill file, and passive context shows weak evidence.** Archyl reports 100 to 200+ MCP tools, depending on the source [vendor] ([agent-skills repo](https://github.com/archyl-com/agent-skills)), and Tentra 32 to 37 [verified repo, counts inconsistent] ([tentra-mcp](https://github.com/rdanieli/tentra-mcp)). Erode has no MCP server, only a skill that shells out to `erode check --format json` [verified] ([Erode Claude Code docs](https://github.com/erode-app/erode/blob/main/packages/web/src/content/docs/docs/integrations/claude-code.md)). An ETH Zurich study found repository context files "do not generally improve task success rates, while increasing inference cost by over 20%" ([arXiv 2602.11988](https://arxiv.org/abs/2602.11988)). Active checks that return violations suit agents better than context dumps [inference].

8. **No tool derives authoritative ownership; all of them author it.** Tentra stores CODEOWNERS-style rules (longest match wins) per workspace [verified] ([tentra-mcp index.ts](https://github.com/rdanieli/tentra-mcp/blob/main/src/index.ts)). Sruja makes `owner` an authored attribute that a policy can require [verified] ([Sruja language spec](https://sruja.ai/reference/language-spec.html)). Backstage requires `spec.owner` in an authored descriptor ([Backstage descriptor format](https://backstage.io/docs/features/software-catalog/descriptor-format)). This supports the repo's choice of ownership as an authored rule.

9. **Behavioral drift is the field's blind spot.** Archyl calls it "the largest blind spot" [vendor] ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy)). None of the five products checks behavior against code. In research, behavioral conformance is done dynamically, by aligning execution traces with an authored state machine or sequence diagram ([de Leoni, Maggi, van der Aalst, BPM 2012](https://www.math.unipd.it/~deleoni/documenti/BPM12.pdf), [Gan, Chechik et al. 2007](https://doi.org/10.1145/1321211.1321217)).

10. **Automated recovery of "the architecture" is unreliable; extracted facts are not.** Six clustering techniques reached 38–59% MoJoFM against expert ground truth, and different techniques "return different results as 'the architecture' for the same system" ([Garcia et al., ASE 2013](https://doi.org/10.1109/ase.2013.6693106)). Package structure "is a limited indicator" of architecture ([Le et al., MSR 2015](https://behnamghader.net/publications/emparch_msr15.pdf)). Extracting imports and calls is sound. Grouping them into components should be authored, not inferred [inference].

## Per-product design breakdowns

### Archyl (archyl.com): SaaS C4 model with three separate checks

Archyl is a closed-source, multi-tenant SaaS built on the C4 model. It was founded in 2025 by one person and launched in January 2026. Its stack is Go, Next.js and PostgreSQL ([founder resume](https://vincent.composieux.fr/resume), [LinkedIn company](https://linkedin.com/company/archyl)). It runs four separate pipelines, and the split is the lesson. First, **LLM discovery**: a non-AI file and import scan, then chunked LLM analysis returning JSON, then an LLM-plus-heuristics reconcile ("It's imperfect"), then C4 mapping and a pending review queue [vendor] ([Archyl discovery blog](https://www.archyl.com/blog/ai-powered-architecture-discovery)). Second, a **deterministic drift score**: one git tree API call with no file contents. It matches containers to top-level directories, presumes components valid if their parent's directory exists, and requires a code element's `filePath` to exist. The score is `floor((matched + 0.5×partial)/total×100)` [vendor] ([Archyl drift score](https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy)). Third, **conformance rules**: seven typed rule kinds made of globs and regexes, such as layer boundaries and forbidden source→target path pairs. They are evaluated on changed files (the first 200 lines of each), and the check fails on critical or high severity [vendor] ([Archyl conformance](https://www.archyl.com/docs/features/conformance-rules), [conformance-check README](https://github.com/archyl-com/conformance-check)). Fourth, **Change Requests** with optimistic concurrency on a per-project model version, returning `409` on a stale base [vendor] ([Archyl many agents](https://www.archyl.com/blog/many-agents-one-architecture)).

Its "Reality" feature keeps three planes, Model ("the intent. Only you change it"), Reality ("the facts") and Binding, and scanners "only ever write to the Reality and Binding planes" [vendor] ([Archyl Reality](https://www.archyl.com/docs/features/reality)). Agents get a hosted MCP server, Claude Code skills, a generated `archyl.txt` and a `PreToolUse` Guard hook that is **fail-open** locally ("A governance tool that can break someone's editing session gets uninstalled in a week") while CI fails closed [vendor] ([Archyl harness blog](https://www.archyl.com/blog/archyl-harness-work-sessions-for-ai-coding-agents)). The model lives in Archyl's database. `archyl.yaml` is an optional git mirror with `dsl diff --exit-code` for CI [vendor] ([Archyl CLI](https://www.archyl.com/docs/guides/cli)). Weak points the vendor admits: name matching "is generous", component accuracy "is inherited, not verified", and there is no per-element accept or suppress mechanism.

### Erode (erode.dev): LLM drift judge over an authored LikeC4 model

Erode is an MIT TypeScript CLI and GitHub Action by one maintainer (57 stars) with no SaaS. You bring your own LLM key ([Erode repo](https://github.com/erode-app/erode)). Its source of truth is a **hand-written LikeC4 or Structurizr model** of declared service-to-service edges, usually in its own repo. Each component maps to code through a repository URL, and components without one "are invisible to the analysis" [verified] ([Erode LikeC4 docs](https://erode.dev/docs/diagrams/likec4/)). The pipeline is diff-only. Deterministic glob filtering comes first. Then a cheap model resolves the component, a cheap model extracts dependency changes as JSON, and a stronger model judges them against the declared edges. An optional stage writes a deterministic DSL patch, with an LLM helping with placement. Every stage boundary is Zod-validated, and LLM text is limited by a "safe DSL text" regex that blocks DSL injection [verified] ([dependency-extraction prompt](https://github.com/erode-app/erode/blob/main/packages/core/src/analysis/prompts/dependency-extraction.md), [common.schema.ts](https://github.com/erode-app/erode/blob/main/packages/core/src/schemas/common.schema.ts)). A final publish phase handles all side effects ([Erode analysis pipeline](https://erode.dev/docs/reference/analysis-pipeline/)).

Accepting drift is a **draft model-update PR** that a reviewer triggers with `/erode update-model`. Additions are generated, removals are "informational only", and the model PR closes itself if re-analysis finds nothing [verified] ([Erode CLI commands](https://erode.dev/docs/reference/cli-commands/), [Erode GitHub Actions guide](https://github.com/erode-app/erode/blob/main/packages/web/src/content/docs/docs/integrations/github-actions.md)). Its stated philosophy is awareness: "Erode does not exist to enforce rules or block merges" ([Erode why it matters](https://erode.dev/docs/why-it-matters/)). Its limits: the LLM assigns severity, a diff-only check never sees drift that existed before the model was written, large diffs are truncated at 50 files and 5,000 lines, and it checks dependencies between services only, not layering inside a service.

### Overarc (overarc.io): authored diagram compiled into CI tests (claims only)

Overarc is the cleanest *design* on paper and the least verifiable. Everything here is **[vendor]** from a single landing page; no docs, pricing, repo or reviews exist ([Overarc](https://overarc.io)). The claimed design is a collaborative multi-level diagram of modules, components, interfaces, dependencies and "scoped architecture rules". Its "diagram schema is synced to your codebase and enforced through deterministic tests that can run in CI/CD", so "when the code drifts from the design, tests fail". Sync goes both ways: code structure can be pulled into the diagram, and code-side changes come back as a diff to review "before merging". Architecture changes are branched, reviewed and merged inside the hosted app. The schema format, the generated tests, the test framework, the rule vocabulary and whether an LLM generates models from code are all unpublished. The founder is unconfirmed: the demo link names "nick-addison", and the likely LinkedIn profile does not mention Overarc ([LinkedIn](https://linkedin.com/in/nick-addison-42a90012a)).

### Tentra (trytentra.com): MCP-first diagram workspace with a heuristic drift report

Tentra has an MIT MCP client (6 stars, one contributor), a closed hosted backend, and Free, $19 and $49/seat plans ([tentra-mcp](https://github.com/rdanieli/tentra-mcp), [Tentra pricing](https://trytentra.com/pricing)). The drift tool `sync_architecture` [verified] works like this. It fetches the saved diagram from the API. It walks the repo, detecting services from docker-compose, package.json, pom.xml, go.mod, pyproject and Kubernetes or Terraform files. It infers connections with fixed confidences (for example `depends_on` gets 0.9 and a shared DB technology 0.7). It maps saved services to detected ones by exact, then fuzzy, id. It reports added, removed and changed services and connections with a 0–100 score, as **markdown with no failure status** ([sync.ts](https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/sync.ts), [connections.ts](https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/connections.ts)). Python detection is substring matching on manifest text, so one `pyproject.toml` becomes one service ([python.ts](https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/detectors/python.ts)). A separate Tree-sitter code graph (SQLite locally, Postgres with pgvector when hosted) feeds `get_spec_alignment`, an advisory per-changed-file check that returns declared edges and ADRs to the agent mid-task. Tentra runs no LLM itself: "the agent in your IDE does the semantic work" [vendor] ([Tentra](https://trytentra.com)). The one independent review notes that there is "no accuracy figure for drift detection" ([Hlido](https://hlido.eu/reviews/rdanieli-tentra-mcp/)). Two flaws follow from the code [inference]: confidences are computed but ignored by the diff, and free-text `responsibility` fields compared as strings will produce systematic noise.

### Sruja (open source, sruja-ai/sruja): Rust DSL, rule engine and graph diff

Sruja is a Rust workspace of 16 crates, dual-licensed Apache-2.0/MIT, with 25 stars and about 800 commits from one human ([Sruja repo](https://github.com/sruja-ai/sruja)). Its focus has moved from "ESLint for System Design" to an autonomous coding agent, and the DSL file is now optional ([Medium intro](https://medium.com/@koladilip/sruja-architecture-as-code-for-the-ai-era-b135f6015017), [FEATURE_TIERS.md](https://github.com/sruja-ai/sruja/blob/main/docs/FEATURE_TIERS.md)). The drift core is still the most complete open reference design [verified]. It has three tiers. Generic structural rules (cycles, god modules, orphans) need no model. An authored `repo.sruja` is diffed against the Tree-sitter code graph. Declarative policies such as `rule deny edge from { kind "external_api" } to { kind "database" }`, with `enforcement "required"` mapping to Error, state the ought ([policy_evaluation.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-engine/src/rules/policy_evaluation.rs)). Both sides become one `Graph` type before `compare_graphs` matches nodes by canonical id, aliases, source paths and id ([compare.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/compare.rs)). Each DSL rule implements a pure `Rule` trait over the AST and returns diagnostics with stable codes, and violations carry `rule_id`, `suppressed` and `baseline_delta` fields ([sruja-diff types.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/types.rs)). It **dogfoods**: its own CI runs `sruja drift -r . -a repo.sruja -f github-actions` on every PR ([sruja-drift.yml](https://github.com/sruja-ai/sruja/blob/main/.github/workflows/sruja-drift.yml)). It also keeps `repo.sruja.draft` (derived) apart from `repo.sruja` (reviewed). Weak spots to avoid: a hard-coded layer hierarchy with name-based layer guessing, relation labels mapped to edge kinds by keyword, and free-text constraints silently ignored unless they match `"<x> -> <y> forbidden"` ([custom_constraints.rs](https://github.com/sruja-ai/sruja/blob/main/crates/sruja-engine/src/rules/custom_constraints.rs)).

### Comparison table

| | Archyl | Erode | Overarc | Tentra | Sruja | **This repo today** |
|---|---|---|---|---|---|---|
| Source of truth | Curated C4 model on server (intent) + ADRs + conformance rules | Hand-written LikeC4/Structurizr model (allowed edges) | Authored diagram [vendor] | Saved diagram is a baseline; code wins | Code graph (evidence) + optional reviewed `repo.sruja` (intent) | Code; committed `/models` is the accepted baseline; ownership is authored |
| Model format | C4; `archyl.yaml` with JSON Schema | LikeC4 / Structurizr DSL → small internal graph | Unpublished "diagram schema" | Hosted JSON: 5 service types, 4 connection types | Own C4-style DSL with policies, flows, state machines | Canonical JSON (structural, behavioral, ownership, scope) |
| Extraction | Non-AI scan + LLM chunks + reconcile | LLM reads the diff | "Generate from code", method unknown | Manifest parsing + heuristic edges; Tree-sitter graph | Tree-sitter + manifests (+ SCIP) | Python `ast`, pure generators |
| LLM vs deterministic | LLM proposes; checks deterministic | LLM extracts and judges | Deterministic tests [vendor] | Deterministic; LLM only via calling agent | Deterministic grader | Deterministic, no LLM |
| Drift check | Path/name existence score; regex rules on changed files | LLM classifies new edges against declared edges | Generated tests | Id-matched diff + 0–100 score | Graph diff + policy rules + structural rules | Id set-difference (ADDED/REMOVED/MODIFIED) + ownership VIOLATION |
| Where it runs | SaaS, Actions, CLI, MCP, hook | CLI, Action, GitLab/Bitbucket, skill | Hosted app + repo CI | MCP stdio/SSE, post-commit hook | Single binary, CI, LSP, MCP | CLI, hosted API; Action planned |
| Gate | Score threshold (default 0 never fails); severity ≥ high | Opt-in `fail-on-violations` (default off) | CI test failure [vendor] | None | `drift --fail-on`, `drift-pr` new-only | Exit 0/1/2; **not wired** |
| Accepting drift | Approve discoveries, edit UI, push YAML, merge CR | Merge auto-drafted model PR | Branch/merge model in app | Call `update_architecture` | Review and commit `repo.sruja` | Commit regenerated `/models` |
| Open / closed | Closed core; MIT CLI, Actions, skills | MIT | Closed | MIT client; closed backend | Apache-2.0/MIT | Course project |

## Cross-cutting design patterns

**Reflexion: authored model + mapping + extracted facts.** The original technique computes convergence (the code has an edge the model predicts), divergence (the code has an edge the model does not predict) and absence (the model predicts an edge the code lacks) from three inputs ([Murphy et al. FSE'95](https://www.cs.ubc.ca/~murphy/papers/rm/reflexion_model_fse95.pdf)). Later work found that the *mapping* is "the most time-consuming activity" ([Koschke, JSEP 2013](https://doi.org/10.1002/smr.542)), and that absences are not always violations. An allowed edge means "may depend", but tools apply "must" semantics, which raises false alarms ([Passos et al., IEEE Software 2010](https://professores.dcc.ufla.br/~terra/publications_files/2010_ieeesw.pdf)). Commercial descendants are Sonargraph's `.arc` artifacts with include patterns and its list of unassigned components ([Sonargraph docs](https://eclipse.hello2morrow.com/doc/standalone/content/architecture_definition.html)) and ArchUnit's "PlantUML diagrams as rules" ([ArchUnit user guide](https://www.archunit.org/userguide/html/000_Index.html)). Rule DSLs such as DCL and Dicto use the modalities must, cannot, only-can and can-only, and they allow *incremental* specification with no full model ([Caracciolo et al., Dicto 2014](https://scg.unibe.ch/archive/papers/Cara14b-Dicto.pdf), [DCL manual](http://rterrabh.github.io/DCL/manual/)).

**Python's closest template is import-linter.** Contracts are authored in TOML (`forbidden`, `layers`, `independence`, `protected`, `acyclic siblings`). `ignore_imports` exceptions fail by default when they no longer match anything, so stale exceptions surface. `layers` has an `exhaustive` mode that fails when a new, unlisted module appears ([import-linter contract types](https://import-linter.readthedocs.io/en/stable/contract_types/), [layers.md](https://github.com/seddonym/import-linter/blob/main/docs/contract_types/layers.md)). Each contract is a plugin whose `check(graph)` is a query over a grimp import graph ([grimp usage](https://grimp.readthedocs.io/en/stable/usage.html)).

**Baselines and ratchets.** File baselines (ArchUnit store, `.dependency-cruiser-known-violations.json`, `jqassistant-baseline.xml`) and commit baselines (Semgrep `--baseline-commit`) both subtract known violations and shrink when violations are fixed ([dependency-cruiser cli](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md), [Semgrep CI vars](https://docs.semgrep.dev/semgrep-ci/ci-environment-variables)). ArchUnit defaults `allowStoreCreation` to false so CI cannot silently create a baseline. Terraform's `apply -refresh-only` is the clearest "accept actual into recorded state" step ([Terraform drift tutorial](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)). In the AI-era doc-sync tools, the designs closest to this repo are also baseline designs: Swimm Verify ([Swimm GitHub App](https://swimm.io/blog/how-swimms-github-app-works)), CodeBoarding's merge-base `review` plus committed `sync` state ([CodeBoarding-action](https://github.com/CodeBoarding/CodeBoarding-action/blob/main/README.md)) and archdrift's structural hash ([archdrift](https://github.com/EvertDeveloper/archdrift/blob/main/README.md)).

**Stable ids and canonical bytes.** Derive ids from code-anchored semantic keys, never traversal order. Strip volatile parts such as ArchUnit's line numbers and lambda `$n`. Sort before serialising. Provide a `format --check` canonicaliser ([LikeC4 CLI](https://likec4.dev/tooling/cli/)). repowise argues for byte-identical output "so PR diffs show only architecture change", and for generating only a `model {}` fragment that a human-owned file `!include`s [vendor] ([repowise C4 guide](https://repowise.dev/blog/guides/generate-c4-diagrams-from-code)).

**Named checks, severity and exit codes.** oasdiff gives every check a stable id and an ERR/WARN/INFO level, with per-check overrides and `--fail-on` ([oasdiff BREAKING-CHANGES](https://github.com/oasdiff/oasdiff/blob/main/docs/BREAKING-CHANGES.md)). dependency-cruiser's exit code equals the number of error-severity violations ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)). Terraform and act101 keep "diff present" and "error / could not judge" as separate codes.

**Adapters and stages.** The shape is extract → (enrich) → evaluate → subtract baseline → report. dependency-cruiser runs extract → analyze → report ([commit 817b870](https://github.com/sverweij/dependency-cruiser/commit/817b8706fef2fec9077e7fe1965cd1596bb8b0dc)). jQAssistant scans artifacts into a graph, enriches it with "concepts" and checks "constraints" ([jQAssistant manual](https://jqassistant.github.io/jqassistant/current/)). Erode separates model adapters, providers, platforms and a publish phase. CodeBoarding keeps its Action a thin wrapper around the core.

**Intent clarification for ambiguous drift.** When a new package appears, KIT's Vitruvius prototype asks the developer whether it is a new component, and plans a task list of postponed decisions ([Kramer/Langhammer et al., KIT report](https://publikationen.bibliothek.kit.edu/1000045654/3515404)). ArDoCo frames inconsistencies as things to "fix or tolerate" ([Keim, KIT 2025](https://doi.org/10.5445/ir/1000179534)).

**MCP and agent surfaces.** MCP read surfaces are everywhere: DeepWiki ([CognitionAI/deepwiki](https://github.com/CognitionAI/deepwiki)), Structurizr ([Structurizr AI](https://docs.structurizr.com/ai)), Port and OpsLevel ([Port MCP](https://docs.port.io/guides/all/build-port-with-mcp/), [OpsLevel MCP](https://docs.opslevel.com/docs/mcp)), Archyl, Tentra and Sruja. The cheaper patterns are a skill or `AGENTS.md` line that runs the CLI (Erode, Sigrid) and a hook that checks each edit (archlint, Archyl Guard). Sigrid admits that "an instruction is followed most of the time" ([Sigrid docs](https://docs.sigrid-says.com/workflows/agents/preventing-architecture-drift.html)), which is why CI stays the real gate.

## Implications for DocumentationModelDrifter's architecture

### What the repo already has, and what the evidence says about it

From a light read of `docs/base/specifications.md` §5.2 and §7.1, `docs/base/structure.md` and `Source/`: pure generators (`Source/models/structural_model.py`, `behavioral_model.py`) take `files` and return a dict. `Source/drifter/check.py` holds the orchestrator (`answer`), the id set-difference (`differences`), the readers (`LocalReader`, a `Reader` protocol) and `check_ownership`. `Source/drifter/cli.py` exposes `init`, `update` and `check` with exit codes 0, 1 and 2. Models are canonical JSON with sorted ids, no line numbers and a `schema_version`. **Evidence:** every one of these choices matches what the strongest tools do. Pure deterministic extraction (Findings 1, 10), id-based diffs without line numbers (Finding 4), a distinct no-verdict code (Finding 5), authored ownership (Finding 8) and a human committing the accepted state (Erode, Swimm, Terraform) are all industry patterns. There is no case for rewriting the core.

**Evidence of the gap:** no gate is wired; the structural and behavioral checks compare against a baseline, not an ought; ownership rules are read at the head commit, so a change can rewrite its own rule ([mage_take.md](mage_take.md), cons 1, 5 and 6). These are the same three gaps the industry tools close with CI wiring, authored rules, and keeping authored intent out of the scanner's reach (Archyl's "only you change it").

### Proposed pipeline shape (recommendation)

The proposal adds one authored input and one pure step beside the existing ones, and keeps the output as one answer. Nothing below replaces existing code.

```
                       READ (git, only place with I/O)      PURE                                 SIDE EFFECTS
                       ──────────────────────────────      ────                                 ────────────
repo @ head  ─► Reader ─► files ─► generators ─► fresh models (the "is") ─┬─► diff vs baseline ─► ADDED/REMOVED/MODIFIED
                                                                          │
repo @ base  ─► Reader ─► /models/structural.json, behavioral.json ───────┘   (accepted baseline: "was")
             └► Reader ─► /models/rules.json   (NEW, authored "ought") ─────► rule check over fresh edges ─► VIOLATION (rule id)
             └► Reader ─► /models/ownership.json (authored "ought") ───────► ownership check over commits ─► VIOLATION

all differences ─► one answer {aligned, structural[], behavioral[], ownership[], (+ rules[])} ─► reporters ─► exit 0 / 1 / 2
                                                                                             (text, JSON, GitHub annotations, job summary)
```

Three properties matter. Authored inputs (rules, ownership) are read at the **base** of the PR, so the change under review cannot rewrite them; changes to them need an owner's review through `CODEOWNERS`. The diff against the baseline stays as it is: "an architecture change nobody has acknowledged yet" is still useful information. Reporters only format the answer; they never decide anything (Erode's publish phase, CodeBoarding's thin Action).

### Prioritized changes, simplest first

Each item says what the evidence shows and what is recommended. Items 1–3 are small and close the MAGE gaps; the rest are optional.

1. **Wire the existing check on this repo, advisory first.** *Evidence:* Sruja gates its own PRs on `drift -a repo.sruja` ([sruja-drift.yml](https://github.com/sruja-ai/sruja/blob/main/.github/workflows/sruja-drift.yml)); Archyl, Erode and Sruja all ship advisory-by-default gates. *Recommendation:* do `mage_take.md` C1 and C5 as written: commit `/models` for `Source/`, run `drifter check` in a PR workflow with `continue-on-error`, and treat exit 2 as never green. The code is already there.

2. **Read authored inputs at the PR base.** *Evidence:* Archyl lets scanners write only to the facts plane, never the intent plane ([Archyl Reality](https://www.archyl.com/docs/features/reality)); ArchUnit stops CI from creating its own baseline. *Recommendation:* load `ownership.json` (and later `rules.json`) from the base commit; put both under `CODEOWNERS`. This is `mage_take.md` C7, and it turns ownership into a real obligation.

3. **Add one authored rule file, checked against structural edges.** *Evidence:* the ought in every conformance tool is a small authored list: import-linter `forbidden`/`layers`, dependency-cruiser `forbidden`, Archyl's Dependency Rule, Sruja's `deny edge`, DCL's `cannot-dep`. *Recommendation:* the minimum is a `models/rules.json` with a list of `{id, from, to, allow|forbid}` over module-id prefixes, evaluated as a pure function over the fresh structural `imports` edges, emitting `VIOLATION` with the rule id. It reuses the existing answer shape and exit codes. Use "may" semantics (a missing allowed edge is not a violation), per Passos et al. **Flag what is missing:** no `exceptions` list, no `layers` shorthand, no "must" edges, no stale-rule alert. Add them only if real rules need them. Before writing a custom checker, the team should decide whether to run import-linter itself on the target repo instead, since it already does this for Python.

4. **Give every difference a stable check id and record why drift was accepted.** *Evidence:* oasdiff and Semgrep key on stable ids; the erosion literature names knowledge vaporization as a main cause ([Li et al., JSEP 2022](https://onlinelibrary.wiley.com/doi/10.1002/smr.2423)). *Recommendation:* use a rule id on rule violations (item 3), and add a convention, not code, that a commit updating `/models` says why in its message. The git history is already the provenance record (REQ-03).

5. **Report new top-level packages as their own category.** *Evidence:* import-linter `exhaustive`, Sonargraph "unassigned components", Vitruvius intent clarification. *Recommendation:* only once rules exist: a module that matches no rule's prefix is "unmapped", so a reviewer decides rather than accepting it silently. Not needed before item 3.

6. **Add a GitHub-annotation and job-summary reporter.** *Evidence:* Sruja `-f github-actions`, oasdiff `::error::` annotations, Archyl's sticky PR comment. *Recommendation:* one function from the existing answer to `::error file=…::` lines plus a markdown summary. Keep it out of `check.py`.

7. **Reduce noise before promoting the gate.** *Evidence:* ARCADE shows change differs across granularities ([Le et al., MSR 2015](https://behnamghader.net/publications/emparch_msr15.pdf)); Mintlify moved to batching after PR noise ([Mintlify changelog](https://www.mintlify.com/docs/changelog.md)); `mage_take.md` measured 358 nodes and 48 edges on this repo. *Recommendation:* measure first (C8's tally). If function-level noise dominates, add a module-level summary in the reporter before changing the model grain. Changing the grain is a schema change and a bigger decision.

8. **Agent surface: an `AGENTS.md` line and JSON output, not an MCP server.** *Evidence:* Erode integrates with only a skill plus `--format json`; passive context files show no reliable benefit ([arXiv 2602.11988](https://arxiv.org/abs/2602.11988)); instructions are followed "most of the time" (Sigrid). *Recommendation:* "Run `drifter check` before declaring done" (`mage_take.md` C9). An MCP server is listed as missing, not proposed.

**Later, and only by conscious decision:** an LLM drafting `rules.json` or classifying unmapped modules, always committed by a person (the academic "LLM at authoring time" pattern; generated design tests sometimes "passed assertions but deviated from the intended rule", so each rule needs human review ([Lucena et al., SBES 2025](https://doi.org/10.5753/sbes.2025.11100))); recording the generator version beside `schema_version` so a tool upgrade is not read as code drift [inference]; checking behavioral models against test traces instead of mined snapshots; a co-change-based ownership signal ([Cataldo et al., ESEM 2008](https://herbsleb.org/web-pubs/pdfs/cataldo-socio-2008.pdf)); multi-language adapters.

**What not to copy.** Percentage drift scores with thresholds, because drift can pile up below the line (Archyl, Tentra). Fuzzy name matching. LLM-assigned severity (Erode). Markdown-only output with no exit code (Tentra). A hosted model store as the source of truth, which drew lock-in criticism ([HN thread](https://news.ycombinator.com/item?id=46778428)). Free-text constraints that are silently ignored (Sruja).

## Contrarian Views and Risks

**The baseline design is legitimate on its own.** Terraform's refresh-only step, Swimm Verify, CodeBoarding and archdrift all treat "unacknowledged change" as the signal and sell it. Reflexion's authors themselves describe "exploiting rather than removing the drift" ([Murphy et al., TSE 2001](https://doi.org/10.1109/32.917525)). A team that only wants reviewers to *notice* architecture changes may not need rules at all. The MAGE critique matters most if the tool is meant to *enforce*.

**Rules don't write themselves.** Archyl says exactly that [vendor] ([Archyl many agents](https://www.archyl.com/blog/many-agents-one-architecture)). An empty `rules.json` changes nothing, and rules go stale too, which is why import-linter fails on unmatched ignores. Authoring cost is the main adoption risk of item 3.

**LLM tools catch things this design cannot.** Erode reads any language and recognises an HTTP client call or a queue subscription as a dependency. A Python import graph sees neither. Deterministic extraction has known blind spots: dynamic imports, DI and reflection, framework routing ([Sruja KNOWN_LIMITATIONS](https://github.com/sruja-ai/sruja/blob/main/docs/KNOWN_LIMITATIONS.md); [Thomas, Nicolaescu, Lichter 2017](http://publications.rwth-aachen.de/record/711734)).

**Gating noise breeds rubber-stamping.** If most red checks are noise, people accept everything with `drifter update`, which is the spec's own Risk 1. That argues for item 7's measurement before any promotion to blocking.

**The industry evidence is thin.** All five products are 2025–26, have one maintainer or a tiny team, and have no published accuracy data. Their marketing contradicts their code: Tentra advertises 9 lint rules and the source has 15 [verified], and tool counts vary by source for both Archyl and Tentra. Overarc is a landing page. The established tools (ArchUnit, import-linter, dependency-cruiser) and the academic results carry more weight than any of the five.

**Agent-context evidence is mixed, not negative.** The ETH study measured context *files*; secondary coverage reports slightly different numbers ([InfoQ](https://www.infoq.com/news/2026/03/agents-context-file-value-review/)), and a second ablation found no effect either way ([ACL REALM 2026](https://aclanthology.org/2026.realm-1.5.pdf)). Neither tested a callable drift check.

## Open Questions

- Would the team rather adopt import-linter for the authored rules on Python targets than write `rules.json` handling? It already has contracts, exceptions and exhaustive layers.
- What is the first real rule for this repo's own `Source/`? `mage_take.md` suggests "`models` must not import `GitHub_Connector`". Is that true today?
- Should acceptance stay "regenerate the whole file", or should a known-violations list (ArchUnit-style) cover rule violations the team tolerates for now?
- At what grain do reviewers act on structural differences: module, class or function? Only the C8 tally can answer this.
- Is there a behavioral question worth an *authored* state model checked against traces, or should the behavioral miner be dropped (mage_take suggestion 5)?
- Overarc's design (authored model compiled into tests) cannot be checked without a demo. Is it worth one?

## Sources

**Archyl**
- https://www.archyl.com/ — product home; positioning as C4 docs "true to your code".
- https://www.archyl.com/docs/features/ai-discovery — LLM discovery phases, pending review, incremental discovery.
- https://www.archyl.com/blog/ai-powered-architecture-discovery — founder's description of the discovery pipeline and its limits.
- https://www.archyl.com/blog/architecture-drift-score-measure-documentation-accuracy — deterministic drift score algorithm, formula, admitted blind spots.
- https://www.archyl.com/docs/features/conformance-rules — seven rule types, severities, packs, "no LLM" claim.
- https://www.archyl.com/features/conformance-rules — marketing page for model-level rules.
- https://github.com/archyl-com/conformance-check — Action mechanics: changed files, first 200 lines, fail-on.
- https://www.archyl.com/docs/features/reality — Model / Reality / Binding planes.
- https://www.archyl.com/blog/many-agents-one-architecture — Change Requests, 409 concurrency, lexical retrieval, "Rules don't write themselves".
- https://www.archyl.com/docs/guides/harness — harness protocol, binding vs advisory records.
- https://www.archyl.com/blog/archyl-harness-work-sessions-for-ai-coding-agents — Guard hook, fail-open rationale.
- https://www.archyl.com/docs/guides/cli — CLI: drift --fail-under, dsl diff --exit-code, push never deletes.
- https://www.archyl.com/docs/features/github-actions — drift-score Action, threshold default 0, generate-context.
- https://www.archyl.com/blog/architecture-as-code-define-your-c4-model-in-yaml — archyl.yaml as source of truth, reference resolution, validation.
- https://www.archyl.com/docs/features/export — archyl.yaml schema.
- https://github.com/archyl-com/agent-skills — skills, MCP tool count, drift-fix modes.
- https://www.archyl.com/pricing — per-editor pricing, BYO model.
- https://news.ycombinator.com/item?id=46778428 — launch thread; lock-in and security criticism.
- https://vincent.composieux.fr/resume — founder resume; stack.
- https://linkedin.com/company/archyl — company size.
- https://www.archyl.com/blog/architecture-drift-detection-guide — vendor's described drift loop.

**Erode**
- https://erode.dev/ — tagline and example output.
- https://github.com/erode-app/erode — repo, licence, stars.
- https://erode.dev/docs/why-it-matters/ — awareness-not-enforcement philosophy.
- https://erode.dev/docs/diagrams/likec4/ — model as source of truth; components need repo links.
- https://erode.dev/docs/diagrams/structurizr/ — Structurizr adapter, id resolution.
- https://erode.dev/docs/how-it-works/ — pipeline stages, file filtering.
- https://erode.dev/docs/reference/analysis-pipeline/ — stages and publish phase.
- https://erode.dev/docs/reference/cli-commands/ — commands, hooks, model-update flow.
- https://erode.dev/docs/reference/configuration/ — diff limits, config precedence.
- https://github.com/erode-app/erode/blob/main/action.yml — fail-on-violations default false.
- https://github.com/erode-app/erode/blob/main/packages/core/src/adapters/architecture-adapter.ts — adapter interface.
- https://github.com/erode-app/erode/blob/main/packages/core/src/analysis/prompts/dependency-extraction.md — Stage 2 prompt.
- https://github.com/erode-app/erode/blob/main/packages/core/src/schemas/common.schema.ts — output guardrails, safe DSL text.
- https://github.com/erode-app/erode/blob/main/packages/web/src/content/docs/docs/integrations/github-actions.md — /erode update-model flow.
- https://github.com/erode-app/erode/blob/main/packages/web/src/content/docs/docs/integrations/claude-code.md — skill and hook integration, no MCP.

**Overarc**
- https://overarc.io — only public source; all claims about design, tests, sync.
- https://linkedin.com/in/nick-addison-42a90012a — possible founder profile, unconfirmed.

**Tentra**
- https://trytentra.com — product claims, agent-as-LLM, FAQ.
- https://trytentra.com/pricing — plans and tier features.
- https://github.com/rdanieli/tentra-mcp — open-source MCP client, README.
- https://github.com/rdanieli/tentra-mcp/blob/main/src/index.ts — sync_architecture, get_spec_alignment, ownership rules.
- https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/sync.ts — diff and score computation.
- https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/connections.ts — heuristic edges with confidences.
- https://github.com/rdanieli/tentra-mcp/blob/main/src/analyzer/detectors/python.ts — Python detection by substring.
- https://hlido.eu/reviews/rdanieli-tentra-mcp/ — independent (automated) critical review.

**Sruja**
- https://github.com/sruja-ai/sruja — repo, crates, stars, contributors.
- https://github.com/sruja-ai/sruja/blob/main/README.md — positioning, MCP, deterministic grader.
- https://medium.com/@koladilip/sruja-architecture-as-code-for-the-ai-era-b135f6015017 — original "ESLint for System Design" framing.
- https://github.com/sruja-ai/sruja/blob/main/docs/FEATURE_TIERS.md — draft vs reviewed DSL, repositioning.
- https://sruja.ai/reference/language-spec.html — DSL, owner attribute, policies.
- https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/compare.rs — node matching order, violations.
- https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/convert.rs — DSL to graph conversion.
- https://github.com/sruja-ai/sruja/blob/main/crates/sruja-diff/src/types.rs — violation and drift report types.
- https://github.com/sruja-ai/sruja/blob/main/crates/sruja-engine/src/rules/policy_evaluation.rs — deny-edge and require rules.
- https://github.com/sruja-ai/sruja/blob/main/crates/sruja-engine/src/rules/custom_constraints.rs — free-text constraints mostly ignored.
- https://github.com/sruja-ai/sruja/blob/main/.github/workflows/sruja-drift.yml — dogfooded CI drift gate.
- https://github.com/sruja-ai/sruja/blob/main/docs/KNOWN_LIMITATIONS.md — drift-pr, extraction blind spots.

**Established tools and analogies**
- https://docs.structurizr.com/ui/diagrams/manual-layout — order-based ids, layout merge.
- https://docs.structurizr.com/ai — Structurizr MCP and AI workflows.
- https://likec4.dev/tooling/cli/ — format --check, validate.
- https://www.archunit.org/userguide/html/000_Index.html — FreezingArchRule, PlantUML rules.
- https://import-linter.readthedocs.io/en/stable/contract_types/ — contract types, ignore_imports alerting.
- https://github.com/seddonym/import-linter/blob/main/docs/contract_types/layers.md — exhaustive layers.
- https://github.com/seddonym/import-linter/blob/main/src/importlinter/contracts/independence.py — contract plugin shape.
- https://grimp.readthedocs.io/en/stable/usage.html — grimp import graph queries.
- https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md — exit codes, known-violations baseline.
- https://github.com/sverweij/dependency-cruiser/commit/817b8706fef2fec9077e7fe1965cd1596bb8b0dc — extract/analyze/report pipeline.
- https://jqassistant.github.io/jqassistant/current/ — scan/concept/constraint pipeline, baseline file.
- https://eclipse.hello2morrow.com/doc/standalone/content/architecture_definition.html — Sonargraph architecture DSL.
- https://backstage.io/docs/features/software-catalog/descriptor-format — authored owner in catalog.
- https://docs.semgrep.dev/semgrep-ci/findings-ci — finding identity without line numbers.
- https://docs.semgrep.dev/semgrep-ci/ci-environment-variables — baseline commit.
- https://github.com/oasdiff/oasdiff/blob/main/docs/BREAKING-CHANGES.md — named checks, severities, fail-on.
- https://developer.hashicorp.com/terraform/cli/commands/plan — detailed exit codes.
- https://developer.hashicorp.com/terraform/tutorials/state/resource-drift — refresh-only acceptance of drift.

**AI-era landscape**
- https://swimm.io/blog/how-swimms-github-app-works — Swimm Verify check and approval commit.
- https://github.com/CodeBoarding/CodeBoarding-action/blob/main/README.md — review vs merge base, committed sync state.
- https://github.com/EvertDeveloper/archdrift/blob/main/README.md — structural drift hash, exit 1.
- https://act101.ai/library/ai-architecture-drift-playbook — exit 0/1/2, "could not judge".
- https://repowise.dev/blog/guides/generate-c4-diagrams-from-code — byte-identical output, generated fragment included by human file.
- https://www.mintlify.com/docs/changelog.md — move from per-change to scheduled batching.
- https://docs.sigrid-says.com/workflows/agents/preventing-architecture-drift.html — instruction-based guardrails followed "most of the time".
- https://github.com/CognitionAI/deepwiki — DeepWiki MCP server.
- https://docs.port.io/guides/all/build-port-with-mcp/ — Port MCP.
- https://docs.opslevel.com/docs/mcp — OpsLevel read-only MCP.
- https://arxiv.org/abs/2602.11988 — context files do not improve agent success, cost +20%.
- https://www.infoq.com/news/2026/03/agents-context-file-value-review/ — coverage of the context-file study.
- https://aclanthology.org/2026.realm-1.5.pdf — second ablation: no effect from context strategy.

**Academic**
- https://www.cs.ubc.ca/~murphy/papers/rm/reflexion_model_fse95.pdf — original reflexion models.
- https://doi.org/10.1109/32.917525 — reflexion models TSE 2001, "exploiting rather than removing the drift".
- https://doi.org/10.1002/smr.542 — incremental reflexion; mapping is the costly part.
- https://professores.dcc.ufla.br/~terra/publications_files/2010_ieeesw.pdf — comparison of DSM, .QL, reflexion; may vs must.
- http://rterrabh.github.io/DCL/manual/ — DCL dependency constraint language.
- https://scg.unibe.ch/archive/papers/Cara14b-Dicto.pdf — Dicto rule DSL with adapters, incremental specification.
- https://onlinelibrary.wiley.com/doi/10.1002/smr.2423 — erosion mapping study; knowledge vaporization.
- https://doi.org/10.1109/ase.2013.6693106 — recovery techniques have low accuracy.
- https://behnamghader.net/publications/emparch_msr15.pdf — ARCADE; package structure a limited indicator.
- https://publikationen.bibliothek.kit.edu/1000045654/3515404 — Vitruvius intent clarification.
- https://doi.org/10.5445/ir/1000179534 — Keim dissertation; fix or tolerate inconsistencies.
- https://doi.org/10.48550/arxiv.2505.16697 — SLR: LLM conformance checking underexplored.
- https://doi.org/10.1145/3832248 — DocPrism: naive LLM over-flags >90%.
- https://doi.org/10.5753/sbes.2025.11100 — LLM-generated design tests sometimes test the wrong rule.
- https://www.math.unipd.it/~deleoni/documenti/BPM12.pdf — process-mining conformance checking.
- https://doi.org/10.1145/1321211.1321217 — runtime monitoring against sequence diagrams.
- http://publications.rwth-aachen.de/record/711734 — static vs dynamic evidence for reflexion.
- https://herbsleb.org/web-pubs/pdfs/cataldo-socio-2008.pdf — socio-technical congruence; logical dependencies matter most.

**This repository (read, not modified)**
- `docs/research/mage_take.md` — MAGE review: no gate, baseline not ought, ownership self-grant.
- `docs/base/specifications.md` — exit codes, change kinds, architecture table.
- `docs/base/structure.md` — structural model ids and canonical layout.

## Rerun Inputs

```
workflow: firecrawl-deep-research + deep-research
topic: architecture drift tool designs
depth: exhaustive
output: markdown
```

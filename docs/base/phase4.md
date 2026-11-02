# Phase 4 build plan: drift checker

Oct 31, 2026 · @Kaan Kanadasi

## Summary

Revised 2026-10-31: the three teammates own the structural, behavioral and ownership formats, so this plan builds everything that does not depend on them first and leaves one narrow seam for their work. Revised 2026-11-01: the roadmap v1, v1.1, v1.2 below replaces build steps A to G.

Team 16's package matches docs/contract/ exactly where it should: golden-outputs.json and mapping-v1.1.yaml are byte-identical, and the system OpenAPI differs only by our two documented deviations plus three small test-route additions. Six smaller mismatches are listed below; none blocks a working tester against Team 16.

What can be built now, with no model format: the hosted service aligned to the contract (T-01 to T-21), the tester (all 33 tests, with T-24 to T-33 reporting skip until goldens exist), and a model-agnostic core: canonical writer, generic comparison by id, orchestrator, CLI and drift_error handling. The teammates then plug in three generators behind one interface.

## Alignment check

I compared Team 16's v1.1 package (SPEC.md, openapi-system-v1.1.yaml, mapping, goldens) with docs/contract/, docs/base/specifications.md, the course PDF and the eight diagrams in docs/models/. The shared parts match; six mismatches need a one-line fix each, none in Team 16's code.

What matches: golden-outputs.json and mapping-v1.1.yaml are byte-identical to ours. Every v1.1 schema field, enum and status code is the same in pod-contract.openapi.yml; the only differences are reworded descriptions, our optional drift, drift_error, /generate, and the test-route items below. The diagrams agree with the spec and contract (ids in them are marked illustrative).

| # | Mismatch | Where | Who fixes | Suggested fix |
| --- | --- | --- | --- | --- |
| 1 | unmapped is "added or modified" in v1.1's OpenAPI but also includes RENAMED, COPIED, TYPE_CHANGED in v1.1 SPEC §6.1; golden c3 lists the renamed src/evaluate.py, so the goldens follow SPEC, against v1.1's own "OpenAPI wins" rule | Team 16 package | Team 16 (tell them) | our contract already uses the SPEC wording; ask Team 16 to align their OpenAPI text |
| 2 | AC ids mean two things: contract §5 counts AC-01 to AC-10 "as in v1.1 SPEC §10", but T-24 to T-33 and spec §6.1 use Team 15's meanings (Team 15 AC-05 is "commit updated models, next check true"; v1.1 AC-05 is review decisions, Phase 5) | spec §4.1, §6.1; contract §5 | Team 15 | state in the contract that coverage uses v1.1's list, and in the spec map Team 15 ACs onto it |
| 3 | spec AC-10 says three runs; contract T-17 and v1.1 AC-10 say five | spec §4.1 | Team 15 | change spec to five runs |
| 4 | Finding.documentation_file description is an unquoted YAML string with a comma, so it parses as an extra key even when it does not exist | both OpenAPI files | both | quote the description |
| 5 | system /test/setup caps session_id at 200 characters and /test/report adds minLength: 1; neither is in contract §9's list of differences | pod-contract.openapi.yml | Team 15 | add both to §9 (harmless: testers send UUIDs) |
| 6 | spec §4.2 already fixes element kinds in the expected answers (L2 "node", L3 and L7 "edge", L4 "state" and "transition") although §3.2 leaves kinds open | spec §3.2 vs §4.2 | teammates | treat these four kind names as constraints on their formats, or revise §4.2 with them |

**Status 2026-10-31:** #2 and #3 are fixed in the spec (§4.1 now uses the pod's AC meanings, see GLOSSARY.md); #4 and #5 are fixed in contract 2.3.0, not yet agreed with Team 16; #1 is Team 16's to fix and is recorded in contract §9; #6 is fixed for structural (spec §4.2 uses the kinds in structure.md) and, since 2026-11-01, for behavioral (L4's kinds `state` and `transition` hold, see behavioral.md). Contract 2.4.0 is proposed and pending Team 16's agreement: §1's example kind becomes "method", tests skip instead of failing on a missing feature (T-18, T-19, T-21 on our system), and §5 lists the acceptance criteria.

Not a mismatch but a gap: our current GitHub_Connector does not meet either OpenAPI file (see Inputs). That is the main risk to a working tester run with Team 16, and it is ours to fix.

## Inputs and starting point

The spec (§3.2, §5.2, §6.1, §7.1) fixes what each piece must output; the contract (§3, §4, §6) fixes how it is tested. What already exists in the repo covers only the git reading.

| Source | What it fixes for Phase 4 |
| --- | --- |
| spec §3.2 | four files in /models; canonical layout (sorted keys, 2-space indent, LF, one trailing newline, lists sorted by id, schema_version); scope defaults `**/*.py` minus `tests/**`; ownership = ordered rules, first match wins, author email only |
| spec §5.2 | four-field answer; drift_error codes; drift stays null with status: SUCCESS; CLI exit codes 0, 1, 2 |
| spec §7.1 | generators are pure (no git, clock, network); only the git readers run git (the connector's clone, and the core's `LocalReader` for the CLI); one orchestrator behind CLI, Action and hosted service |
| contract §4 | T-24 to T-31 compare the whole drift object including order; T-32 compares drift and drift_error.code; T-33 compares three file texts byte for byte (structural, behavioral, scope; not ownership) |
| contract §6 | 90 s per project call, 600 s per tester run, no retries |
| pod-tester.openapi.yml | tester routes /test/setup, /test/run, /test/report and the suite report shape |

What exists on `main` (2026-11-01):

- **Reusable, in Source/GitHub_Connector:** fetch.py (clone, resolve short SHA, first parent, diff, read blobs, timeouts), runs.py (write-once run files), course.py (system /test/setup and /test/report with line coverage), api.py routing.
- **Started, outside the plan's layout:** `Source/models/` holds `common.py` (`parse_files`, `write_model`), `structural_model.py` (the structural generator) and `ownership_model.py` (propose and check); `Source/drifter/check.py` (moved from `Source/orchestration.py`) runs a check with scope, diff by id and the ownership check, on a local checkout or on a GitHub repository through the connector's blobless clone (#18), and since #31 regenerates behavioral too, from `Source/models/behavioral_model.py`; `Source/Tester/` serves the tester at /tester; `tests/` holds the connector, structural, common, tester and diagram tests.
- **Contract 2.4.0:** run files now survive a redeploy on the Railway volume (#27). (Done on `main`, merged from contract-alignment: features in /health, mapping-v1.1.yaml, config_version mapping-v1.1, unmapped, contract error codes, one skip reason, 80 s deadline, CHANGE_LIMIT_EXCEEDED, one active test session; all 10 golden cases pass. The console path already points at Frontend.)
- **Still missing:** every model's `*.schema.json`. (`Source/drifter/`, the CLI, `drift` on /analyze, /generate, packaging, the durable store and the behavioral generator are done; see the tables below.)

## Roadmap: v1, v1.1, v1.2

Decided 2026-11-01 in a design session (decisions D1 to D12 below). It replaces build steps A to G. Each version ends in checks anyone can run; a version is done only when its checks pass. Phase 5 (release tag, GitHub Action, T-22, T-23) is out of this roadmap.

| Who | Owns |
| --- | --- |
| Kaan | core (`Source/drifter/`, `Source/models/common.py`; Muhammad may edit `check.py` too), hosted service, CLI, model fixture and goldens |
| Enrique | structural model (`Source/models/structural_model.py`) and the tester |
| Barshan | behavioral model (`Source/models/behavioral_model.py`) |
| Muhammad | ownership model (`Source/models/ownership_model.py`, moved from `Source/Modelers/`) |

The model owners start now, in parallel with v1 (D8). Behavioral comes first: fixture L0 to L7, and so T-24 to T-31 and T-33, wait on its format.

### v1: the contract service (Kaan)

Needs no model format. Builds on `main` (contract-alignment is merged), where /health features, contract error codes, mapping-v1.1.yaml, the 80 s deadline, CHANGE_LIMIT_EXCEEDED and one active session are done.

| Item | Done when |
| --- | --- |
| Durable store (D6): a Railway volume behind `runs.py`; `runs_dir` from `RAILWAY_VOLUME_MOUNT_PATH`; on Railway without a volume the app refuses to start; /health reports `storage: volume` (or `ephemeral` locally); the container starts as root, hands the volume to `drifter`, then drops to it with `setpriv` (fallback `RAILWAY_RUN_UID=0`); scheduled volume backups on | a result saved before a redeploy is returned byte for byte after it (T-14, T-16); /health says `volume` on Railway. **Done** (#27, tracker-gaps row 17) |
| Base image (D11): from `python:3.12-slim` to `FROM python:3.12-slim-trixie`, which brings git 2.47 (`GIT_NO_LAZY_FETCH` needs 2.44 or later) | `git --version` in the container is 2.44 or later. Image pinned to `slim-trixie` (#26) |
| Fresh blobless clone per check, no clone cache (D11) | step A's old "one clone per repository" check is dropped |
| Our tester against Team 16's system, and against ours | T-01 to T-17 pass on both; one full run is timed and logs each call's time |

### v1.1: the drift core (Kaan, with structural plugged in)

Spec: issue #12. Status as of 2026-11-01, after #13 closed and Muhammad's push of the remote reader and `drift` on /analyze.

| Item | Done when | Status |
| --- | --- | --- |
| Shared glob (#13): one matcher for mapping-v1.1.yaml, scope.json and ownership rules, importable without the web service | glob, scope and ownership tests; the 10 golden cases pass | **done** (#13 closed): `glob` in `models/common.py`, with `\` to escape; init escapes `\`, `*`, `?` in proposed paths; history read with `git log -z` so no quoted path escapes a rule |
| File reader (D11, #18): after `ls-tree` at head, fetch every needed blob in one `git fetch --filter=blob:none --stdin`; read with lazy fetching off, so a failed batch is 500 ANALYSIS_FAILED at once | a local test: reading succeeds after the batch and fails without it; the clone holds exactly 2 promisor packs | **done** (#18): `tests/connector/test_fetch.py` checks, on a local bare repo, the same sources as `LocalReader`, ANALYSIS_FAILED with the batch skipped, 2 promisor packs per `read()`, and the deadline and per-call timeout with the clone deleted; a whole check still downloads twice (tracker-gaps row 3), and timings on Railway are unmeasured |
| Seam (D9, `docs/models/model-seam.md`, #14): reuse `parse_files` and `write_model`; flatten each model's top-level lists to `{id: element}`; diff by id (ADDED, REMOVED, MODIFIED) | fake-plugin tests in tests/ cover each change type | **done** (#14): `_elements` flattens every top-level list; `GENERATORS` registers structural; fake-plugin tests in `tests/drifter/test_cli.py` |
| Orchestrator, starting from `Source/drifter/check.py` (#15): scope.json, the four drift_error codes, the four-field answer | a test per drift_error code; aligned true only when all three lists are empty | **done** (#15): all four codes tested through /analyze and through `drifter check` (exit 2); INVALID_MODELS covers bad JSON, the element rule (`id`, `kind`, `file`, unique ids), a malformed scope.json and ownership rules without a pattern and owners, not yet owner schemas (none written); in-scope files judged one by one in path order, so the first bad file wins |
| `drift` and `drift_error` on every /analyze (#19), POST /generate (#20) | T-32 passes at L-pre (MODELS_NOT_FOUND) | /analyze **done** (#19): `tests/connector/test_analyze_drift.py` runs TestClient against a local bare repo for an aligned commit (saved result included), MODELS_NOT_FOUND at a commit with no `/models`, `drift` byte-identical to `drifter check`, and a real drifted verdict under CHANGE_LIMIT_EXCEEDED. /generate **done** (#20): `analysis.generate` runs `generate_models` on the blobless clone and saves nothing; byte-equal to `drifter init`, 400/404 codes and the contract's `GenerateResult` tested through TestClient in `tests/connector/test_generate.py` |
| Ownership checker and commit log (D10, #16): `CommitRecord` in `ownership_model.py` (sha, lowercase author email, parents, paths as `PathTouch`; no `author_login`, no date, no prefix); first matching rule wins; no rule means anyone; a rename is judged under its old path; one glob matcher shared with mapping-v1.1.yaml | scripted-author repo: a non-owner gives one VIOLATION, an owner none | **done** (#16): every acceptance criterion tested through `drifter check` on scripted-author repos in `tests/drifter/test_cli.py`: non-owner and owner, merge, rename, no rule, first rule wins, mixed-case email, sort order, outside scope, default base and root commit. The checker's own merge skip and lowercasing sit behind the history reader, which lists no paths for a merge and lowercases emails, so `tests/ownership/test_ownership_model.py` tests those two directly |
| CLI (D12, #14, #17): `drifter init`, `update`, `check` on a local checkout (commit defaults to HEAD); `pyproject.toml` with a `drifter` entry point | `pip install -e .`; check exits 0, 1 and 2 in tests | **done**: `drifter check` (#14) prints the answer as canonical JSON and exits 0, 1 or 2, tested (#15); the `drifter` entry point is tested without FastAPI; `init` and `update` (#17) read the code at a commit and write the checkout's top-level `/models`, `init` refusing (exit 1) without `--force`, all five acceptance criteria tested in `tests/drifter/test_cli.py`; `generate_models` in `check.py` is what `/generate` (#20) reuses |
| Shared seam test in tests/common/ (#21): element rule, unique ids, sorted lists, valid against the schema, `write_model` round trip | passes for structural | **done** (#21): `tests/common/test_seam.py`, one line per generator in `SEAM_GENERATORS`; reuses `_element_rule`, so the test and INVALID_MODELS agree; a schema is read from `Source/models/<name>.schema.json` and its check skipped until it exists |
| Timing on real repositories, generators included (#22, a person) | on Railway, one full check of pytest and of Django each finishes; Django under 60 s | **not started** |

### v1.2: all three models and the drift tests

| Item | Who | Done when |
| --- | --- | --- |
| `structural.schema.json` | Enrique | seam test passes; byte-identical on Linux and Windows |
| Behavioral format, `generate_behavioral`, `behavioral.schema.json` | Barshan | own snippet goldens and the seam test pass; byte-identical on Linux and Windows. Generator, snippet goldens and seam test done and registered (#31), format in `docs/base/behavioral.md`; `behavioral.schema.json` not written yet |
| `propose_ownership(head_sha, records)` returning spec §3.2's rule list (done in PRs #7 and #9: `[bot]` emails, no `email:` prefix, `pattern` key, window 10, vendored folders, lowercase emails, renames under the old path; settings stay constants in the module); `ownership.schema.json` | Muhammad | own goldens pass; output validates against the schema |
| Model fixture `MuhammadSban/doc-tracker-model-fixtures`, public, commits L-pre to L7 (spec §4.2) | Kaan | contract §3 checklist done |
| `docs/contract/model-golden-outputs.json`, contract version bump | Kaan | Team 16 told; tester turns on T-24 to T-33 |
| Full suite against our system | Enrique, Kaan | T-24 to T-33 pass |

### Left out, flagged (each needs a conscious decision)

- A retry of the batch blob fetch after a dropped connection.
- A GitHub token for higher anonymous rate limits.
- A clone cache per repository; a per-session warm-up in /test/setup.
- Detecting a file over 1 MB before downloading it.
- A shallow clone for structural and behavioral if a real repository passes the deadline; `--no-renames` for /generate over long history.
- A Storage Bucket instead of the volume, for zero-downtime deploys or replicas; `runs.py` is the only file to change.

### Needs a person, not code

- Muhammad invites Barshan to the repository, so issues can be assigned.
- The model fixture repository must exist and be public before L-pre (T-32).
- Team 16: registry URL (contract §8), the session-release rule, the cover message, tickets 3, 4 and 11, and agreement to a contract version.

### Decisions of 2026-11-01

| # | Decision |
| --- | --- |
| D1 | Team 15's design work stops at the seam; each model's kinds, ids, attributes, mining rules and schema belong to its owner. |
| D2 | Owners as in the table above. |
| D3 | The roadmap covers v1, v1.1 and v1.2 only. |
| D4 | Work continues on `durable-store`, rebased onto `contract-alignment`. Since then contract-alignment is merged into `main` and `durable-store` was never created, so v1 branches from `main`. |
| D5 | Q1 to Q8 below are decided as recommended, except: generators take `{path: text}` as spec §3.2 says (not parsed trees); models live in `Source/models/`, the core in `Source/drifter/`. |
| D6 | Results on a Railway volume behind `runs.py`, failing loudly without one. Not horizontally scalable, deliberately: the spec caps checks at 2 at once. |
| D7 | This roadmap lives here; one GitHub issue per item, labelled `ready-for-human`. |
| D8 | Model owners start now; behavioral first. |
| D9 | The seam in `docs/models/model-seam.md`. |
| D10 | Kaan writes the ownership checker and the commit log; `CommitRecord` is the shared type. |
| D11 | A fresh blobless clone per check, one batched blob fetch, reads with lazy fetching off (`docs/models/file-fetch.md`). Measured: fixture 1 to 3 s, pytest 9 to 13 s, Django 38 to 41 s per check; reading blob by blob took 163 to 221 s on pytest. |
| D12 | CLI as in v1.1. |

## Contract test map

Against our system, 21 of 33 tests need only v1 and the tester; the ten drift tests need v1.1 and v1.2; two are Phase 5.

| Tests | Needs | Against our system | Against Team 16 |
| --- | --- | --- | --- |
| T-01 to T-16 | v1 | pass | pass |
| T-17 (five runs) | v1 | pass | pass |
| T-18 to T-21 (prose findings) | none | skip (no prose_detector) | pass |
| T-22, T-23 | none | skip (Phase 5) | skip |
| T-24 to T-31 (L0 to L7) | v1.2 | skip until v1.2, then pass | skip (no model_drift) |
| T-32 (L-pre, MODELS_NOT_FOUND) | v1.1 and the L-pre commit | passes at v1.1 | skip |
| T-33 (/generate at L0) | v1.2 | skip until v1.2 | skip (no model_drift) |

The tester runs every row on day one; until v1.2 it reports T-24 to T-33 as skip with "expected answers not yet published".

## Design questions

Decided 2026-11-01 as recommended, with the exceptions in D5 and D11 above; kept for the reasoning. Each question below says what is being decided, why it matters, the options with their costs, and the recommendation. Answer in the thread with the question number.

### Q1 Who compares the models

**The decision.** A check regenerates a model from the code and diffs it against the committed one. Somebody must write that diff. Either the core diffs every model the same way, or each teammate writes the diff for their own model.

**Why it matters.** The diff output is fixed by the contract: each difference is {change, file, id, kind}, sorted by id, and T-24 to T-31 compare it byte for byte with the expected answer, order included. Three separate diffs mean three chances to sort differently or to call the same thing MODIFIED in one model and REMOVED plus ADDED in another.

| Option | Teammate writes | Cost |
| --- | --- | --- |
| Core diffs (recommended) | elements(model): turns their model into a flat map id -> (kind, file, attributes) | teammates must give every element a unique id and a file; the core decides MODIFIED as "same id, different attributes" |
| Each plugin diffs | compare(old, new) -> differences | three implementations of one rule; the tester's byte-for-byte comparison makes any drift between them a failing test |

**Recommendation:** core diffs. It also means the spec's table (ADDED, REMOVED, MODIFIED) is coded once. Teammates keep full control of what an element is and what its id looks like.

### Q2 Who parses the Python files

**The decision.** Structural and behavioral generators both read Python source. Either the core reads, checks and parses each file once and hands the plugins the result, or each plugin opens and parses files itself.

**Why it matters.** The spec fixes three failures that must happen before any model is built: a file over 1 MB gives FILE_TOO_LARGE, a binary or non-UTF-8 file gives PARSE_FAILED, and a syntax error gives PARSE_FAILED with the file and line (spec §5.2, one-check diagram). It also says no file may be skipped, because a skipped file would show up as fake REMOVED drift (spec §3.3). If each plugin parses, both must raise the same error, in the same order, with the same message, or repeatability (AC-10) and the CLI's exit code 2 become inconsistent.

| Option | Plugin receives | Cost |
| --- | --- | --- |
| Core parses once (recommended) | {path: (text, ast.Module)} for in-scope files | commits everyone to Python's built-in ast; a teammate who wants a different parser (for example LibCST) must ask for it |
| Core checks size and encoding only | {path: text} | the core still owns the first two errors; each plugin must turn its own syntax error into PARSE_FAILED the same way |
| Plugins do everything | paths only | all three errors duplicated |

**Recommendation:** core parses once with ast. It is in the standard library, never imports or runs the code (REQ-06), and halves the parse time, which helps the 90 s limit. The middle option is a fine fallback if a teammate needs another parser.

### Q3 Who owns scope.json and the path pattern rules

**The decision.** Three things match file paths against patterns: classification by mapping-v1.1.yaml (contract), scope.json (which files feed the generators) and ownership.json (who owns a path). Spec Q11 lists "path pattern rules for scope.json and ownership.json" as still open. The question is whether that belongs to the teammates with their formats, or to the core.

**Why it matters.** scope.json is not a model; it is input to all generators, and it is one of the three files /generate must reproduce byte for byte (T-33). Ownership rules are judged by the core's checker (step D), so the core must understand the pattern syntax. If patterns mean different things in different files, `src/**` could match in classification but not in ownership.

| Option | Who decides | Cost |
| --- | --- | --- |
| Core owns, reuses the mapping glob (recommended) | core: `**/` is zero or more folders, `**` anything, `*` one segment, as in mapping-v1.1.yaml | teammates live with that syntax; nothing new to invent |
| Core owns, uses gitignore / CODEOWNERS syntax | core | familiar to developers (spec compares ownership to CODEOWNERS), but a second matcher beside the contract's |
| Teammates own scope and ownership formats | the ownership teammate | core checker blocked until they decide; scope has no natural owner |

**Recommendation:** core owns scope.json and one matcher shared with classification. The ownership teammate still owns the rest of ownership.json and what init proposes.

### Q4 Where new code goes

**The decision.** Today Source/ holds GitHub_Connector (the v1 service) and Frontend. Phase 4 adds the core, the CLI, plugins, the tester and tests.

**Why it matters.** Spec §7.1 says one codebase runs as CLI, GitHub Action and hosted service, and §7.1 adoption says a repository installs drifter with pip from a release tag. So the core must be importable without FastAPI or the web app, and must not live inside the web service folder.

| Option | Layout | Cost |
| --- | --- | --- |
| New package (recommended) | Source/drifter/ (core, CLI, plugins/structural.py, behavioral.py, ownership.py), Source/Tester/, top-level tests/, one pyproject.toml with a drifter entry point | drifter must call git; it imports GitHub_Connector.fetch, or fetch.py moves into drifter later |
| Everything inside GitHub_Connector | one folder | the CLI would depend on the web service; harder to pip install |
| Separate repositories | core, service, tester apart | more setup, versions to keep in step |

**Recommendation:** new Source/drifter/ package, plugins one file each so each teammate owns one file. Gives clean ownership of code too.

### Q5 Fix GitHub_Connector in place, or rewrite it

**The decision.** The v1 service was built for an LLM prose check. It could not start (it imported LLM_Shell, which is not in the repo; that import is now removed) and it differs from contract 2.4.0 in about ten places (see Inputs).

**Why it matters.** T-01 to T-21 grade exactly this service. It is the shortest path to a working run with Team 16.

| Option | Work | Cost |
| --- | --- | --- |
| Fix in place (recommended) | remove the LLM call; swap path_rules.json for mapping-v1.1.yaml; add unmapped; rename error codes; one skip reason; 80 s deadline; durable store | keeps tested code (fetch.py clone, short SHA, timeouts; runs.py write-once; course.py coverage); some v1 comments and settings become stale |
| Rewrite from the v1.1 SPEC | new service built from Team 16's §5 pipeline | cleaner, but repeats work that already handles git edge cases |

**Recommendation:** fix in place, one change per contract item, each proven by the golden test for the 10 cases. AGENTS.md's "surgical changes" rule points the same way.

### Q6 Where saved results live

**The decision.** Every /analyze result must be saved write-once and returned unchanged by GET /analysis/{id}, "also after the system restarts or is redeployed" (contract §1, REQ-04, T-14 to T-16). Today run files go to a folder that is wiped on every redeploy (settings.py says so).

**Why it matters.** A tester run against us after a redeploy would fail T-14 and T-16 for any result saved before it. Staff may also look up an old analysis_id.

| Option | How | Cost |
| --- | --- | --- |
| Railway volume (recommended) | mount a persistent volume at runs_dir; code unchanged | needs a volume on the Railway service (a setting, no code); data lives with one host |
| GitHub repository as store | commit each result as a file to a results repo; Health reports storage: github | survives anything, auditable, but needs a token, is slower and adds rate limits |
| Hosted database (Postgres, SQLite on volume) | store rows | more code and a new dependency for a write-once file store |

**Recommendation:** Railway volume, since runs.py already writes one file per result atomically. Confirm we deploy on Railway (settings.py reads RAILWAY_GIT_COMMIT_SHA, so it looks like it).

### Q7 Does the tester get its own deployment

**The decision.** The course registry lists a tester URL and a system URL per team. The tester calls the other team's system; the system is called by their tester.

**Why it matters.** The tester's run can take up to 600 s and makes many outbound calls; the system has a limit of 2 checks at once and its own coverage measurement (course.py counts lines run per session).

| Option | How | Cost |
| --- | --- | --- |
| Same app, /tester router (recommended) | one FastAPI app serving /system/\* and /tester/\* | one deploy; but the tester's own lines must be left out of /system/test/report coverage, and a long tester run shares the machine with incoming checks |
| Separate service | second Railway service from the same repo | clean coverage and resources; one more deploy and URL to keep alive |

**Recommendation:** same app, as long as coverage counts only the system package (it already lists packages explicitly). Switch to a separate service if a 600 s tester run slows our own checks.

### Q8 When to change the contract for the mismatches

**The decision.** The Alignment check found six mismatches. Two are in our spec only (AC-10 "three runs", AC meanings). Others touch docs/contract/, and contract §10 says any change there bumps the version and needs Team 16's agreement.

**Why it matters.** Each contract bump costs a round of agreement with Team 16. The model goldens will force a version bump anyway (contract §3 checklist).

| Option | When | Cost |
| --- | --- | --- |
| Spec now, contract with goldens (recommended) | edit specifications.md today; queue contract items 2, 4, 5 for 2.3.0; tell Team 16 about item 1 and 4 now as a heads-up | one agreement round; the contract carries the small inaccuracies a bit longer |
| Bump now, again later | 2.3.0 now, 2.4.0 with goldens | two rounds of agreement |
| Never | leave as is | the AC ambiguity can make coverage numbers differ between the two testers |

**Recommendation:** spec now, contract once with the goldens.

Left to the teammates, not asked here: element kinds, id scheme, mining rules, the JSON Schemas and what init proposes for ownership.

Phase 4 build plan: drift checker
Oct 31, 2026 · @Kaan Kanadasi
Summary
Revised 2026-10-31: the three teammates own the structural, behavioral and ownership formats, so this plan builds everything that does not depend on them first and leaves one narrow seam for their work.
Team 16's package matches docs/contract/ exactly where it should: golden-outputs.json and mapping-v1.1.yaml are byte-identical, and the system OpenAPI differs only by our two documented deviations plus three small test-route additions. Six smaller mismatches are listed below; none blocks a working tester against Team 16.
What can be built now, with no model format: the hosted service aligned to the contract (T-01 to T-21), the tester (all 33 tests, with T-24 to T-33 reporting skip until goldens exist), and a model-agnostic core: canonical writer, generic comparison by id, orchestrator, CLI and drift_error handling. The teammates then plug in three generators behind one interface.
Alignment check
I compared Team 16's v1.1 package (SPEC.md, openapi-system-v1.1.yaml, mapping, goldens) with docs/contract/, docs/base/specifications.md, the course PDF and the eight diagrams in docs/models/. The shared parts match; six mismatches need a one-line fix each, none in Team 16's code.
What matches: golden-outputs.json and mapping-v1.1.yaml are byte-identical to ours. Every v1.1 schema field, enum and status code is the same in pod-contract.openapi.yml; the only differences are reworded descriptions, our optional drift, drift_error, /generate, and the test-route items below. The diagrams agree with the spec and contract (ids in them are marked illustrative).
#
Mismatch
Where
Who fixes
Suggested fix
1
unmapped is "added or modified" in v1.1's OpenAPI but also includes RENAMED, COPIED, TYPE_CHANGED in v1.1 SPEC §6.1; golden c3 lists the renamed src/evaluate.py, so the goldens follow SPEC, against v1.1's own "OpenAPI wins" rule
Team 16 package
Team 16 (tell them)
our contract already uses the SPEC wording; ask Team 16 to align their OpenAPI text
2
AC ids mean two things: contract §5 counts AC-01 to AC-10 "as in v1.1 SPEC §10", but T-24 to T-33 and spec §6.1 use Team 15's meanings (Team 15 AC-05 is "commit updated models, next check true"; v1.1 AC-05 is review decisions, Phase 5)
spec §4.1, §6.1; contract §5
Team 15
state in the contract that coverage uses v1.1's list, and in the spec map Team 15 ACs onto it
3
spec AC-10 says three runs; contract T-17 and v1.1 AC-10 say five
spec §4.1
Team 15
change spec to five runs
4
Finding.documentation_file description is an unquoted YAML string with a comma, so it parses as an extra key even when it does not exist
both OpenAPI files
both
quote the description
5
system /test/setup caps session_id at 200 characters and /test/report adds minLength: 1; neither is in contract §9's list of differences
pod-contract.openapi.yml
Team 15
add both to §9 (harmless: testers send UUIDs)
6
spec §4.2 already fixes element kinds in the expected answers (L2 "node", L3 and L7 "edge", L4 "state" and "transition") although §3.2 leaves kinds open
spec §3.2 vs §4.2
teammates
treat these four kind names as constraints on their formats, or revise §4.2 with them
Status 2026-10-31: #2 and #3 are fixed in the spec (§4.1 now uses the pod's AC meanings, see CONTEXT.md); #4 and #5 are fixed in contract 2.3.0, agreed with Team 16; #1 is Team 16's to fix; #6 is open.
Not a mismatch but a gap: our current GitHub_Connector does not meet either OpenAPI file (see Inputs). That is the main risk to a working tester run with Team 16, and it is ours to fix.
Inputs and starting point
The spec (§3.2, §5.2, §6.1, §7.1) fixes what each piece must output; the contract (§3, §4, §6) fixes how it is tested. What already exists in the repo covers only the git reading.
Source
What it fixes for Phase 4
spec §3.2
four files in /models; canonical layout (sorted keys, 2-space indent, LF, one trailing newline, lists sorted by id, schema_version); scope defaults **/*.py minus tests/**; ownership = ordered rules, first match wins, author email only
spec §5.2
four-field answer; drift_error codes; drift stays null with status: SUCCESS; CLI exit codes 0, 1, 2
spec §7.1
generators are pure (no git, clock, network); only the GitHub integration runs git; one orchestrator behind CLI, Action and hosted service
contract §4
T-24 to T-31 compare the whole drift object including order; T-32 compares drift and drift_error.code; T-33 compares four file texts byte for byte
contract §6
90 s per project call, 600 s per tester run, no retries
pod-tester.openapi.yml
tester routes /test/setup, /test/run, /test/report and the suite report shape
What exists today in Source/GitHub_Connector (v1, built for an LLM prose check):
• Reusable: fetch.py (clone, resolve short SHA, first parent, diff, read blobs, timeouts), runs.py (write-once run files), course.py (system /test/setup and /test/report with line coverage), api.py routing.
• Not contract 2.2.0: imports LLM_Shell, which is not in the repo, so the app cannot start; classifies with path_rules.json instead of mapping-v1.1.yaml; config_version is a hash, not mapping-v1.1; no unmapped; error codes TIMEOUT, WRITE_FAILED, LLM_UNAVAILABLE instead of ANALYSIS_FAILED, STORAGE_FAILED; skip reasons beyond UNSUPPORTED_FILE_TYPE; deadline 120 s, not 90 s; run files are lost on redeploy; the console path points at Source/Frontend, which is now Frontend_Archive.
• Missing entirely: generators, comparison, orchestrator, CLI, /generate, the tester, tests, packaging.
Architecture: one seam for the teammates
The core never looks inside a model. Each model is a plugin the teammates write; the core only asks it four things, so their format can change without touching the core, the CLI, the service or the tester.
The plugin interface (structural and behavioral; proposed names):
Member
What it does
Who decides its content
name
"structural" or "behavioral", the file stem and the key in drift
fixed by spec
schema
JSON Schema for the file; failing it gives INVALID_MODELS
teammate
generate(files) -> dict
pure function, in-scope files in, model out; no git, clock or network (spec §7.1)
teammate
elements(model) -> {id: (kind, file, attrs)}
flattens a model so comparison can diff by id
teammate
Ownership is different (spec §3.2): it is never regenerated. Its plugin gives schema, propose(history) -> dict for init, and rules(model) -> [(pattern, owners)]. The core's checker turns rules plus the commit log into VIOLATION entries, whose shape the contract already fixes.
Format-free core (buildable now):
Module
Job
Fixed by
canonical
writes any dict with the spec's layout: sorted keys, 2-space indent, LF, one newline, lists sorted by id
spec §3.2
compare
ADDED, REMOVED, MODIFIED by id from two elements() maps, sorted by id
spec §3.2 table
ownership_check
judges each non-merge commit base..head against rules()
spec §3.2, contract OwnershipViolation
check (orchestrator)
reads /models, validates against each schema, reads in-scope files, raises the four drift_error codes, calls the plugins, builds the four-field answer
spec §5.2, one-check diagram
cli
init, update, check, exit codes 0, 1, 2
spec §5.2
hosted wiring
drift and drift_error on every /analyze, POST /generate
contract §1
Until the plugins exist, core tests use a tiny fake plugin that lives only in tests/, so no format is invented in product code.
Build steps
Steps A to D need no model format and can start today, in parallel. Steps E to G wait for the teammates.
Step
What
Needs
Done when
A
Align the hosted service to contract 2.2.0: mapping-v1.1.yaml, config_version: mapping-v1.1, unmapped, contract error codes, one skip reason, issues: [], 90 s deadline, durable store, drop the LLM_Shell import
nothing
all 10 cases of golden-outputs.json match on the nine compared fields
B
Tester: /test/setup, /test/run, /test/report; tests as a table of (id, components, criteria, run); golden comparator; 90 s per call, no retry, 600 s budget
nothing
runs against Team 16's deployed system; report validates against pod-tester.openapi.yml
C
Format-free core: canonical, compare, check, drift_error codes, plugin interface, CLI, drift key, /generate
A for the hosted part
fake-plugin tests: aligned, each change type, each drift_error, exit codes 0, 1, 2
D
Ownership checker engine and the git commit log in fetch.py
pattern syntax (question below)
scripted-author repo: non-owner gives one VIOLATION, owner gives none
E
Three plugins
teammates
each plugin's snippet goldens; byte-identical on Linux and Windows
F
Model fixture L-pre to L7 and model-golden-outputs.json
E
contract §3 checklist done, version 2.3.0
G
Tester turns on T-24 to T-33
F
full suite against our system: T-24 to T-33 pass
A and B together give a working cross-team run with Team 16 for T-01 to T-23, which is the Phase 4 demonstration minus the drift tests.
Contract test map
Against our system, 21 of 33 tests depend only on steps A and B; the ten drift tests need E and F; two are Phase 5.
Tests
Needs
Against our system
Against Team 16
T-01 to T-16, T-20
A
pass
pass
T-17 (five runs, drift byte-identical)
A; C and E for drift
pass
pass
T-18, T-19, T-21 (prose findings)
none
fail by design (deviation 1)
pass
T-22, T-23
none
skip (Phase 5)
skip
T-24 to T-31 (L0 to L7)
C, E, F
skip until F, then pass
skip (no drift key)
T-32 (L-pre, MODELS_NOT_FOUND)
C and the L-pre commit only
could pass before E (see questions)
skip
T-33 (/generate at L0)
C, E, F
skip until F
skip (404)
The tester itself (B) runs every row on day one; until F it reports T-24 to T-33 as skip with "expected answers not yet published".
Design questions
Round 1 is open in the thread. Each question below says what is being decided, why it matters, the options with their costs, and the recommendation. Answer in the thread with the question number.
Q1 Who compares the models
The decision. A check regenerates a model from the code and diffs it against the committed one. Somebody must write that diff. Either the core diffs every model the same way, or each teammate writes the diff for their own model.
Why it matters. The diff output is fixed by the contract: each difference is {change, file, id, kind}, sorted by id, and T-24 to T-31 compare it byte for byte with the expected answer, order included. Three separate diffs mean three chances to sort differently or to call the same thing MODIFIED in one model and REMOVED plus ADDED in another.
Option
Teammate writes
Cost
Core diffs (recommended)
elements(model): turns their model into a flat map id -> (kind, file, attributes)
teammates must give every element a unique id and a file; the core decides MODIFIED as "same id, different attributes"
Each plugin diffs
compare(old, new) -> differences
three implementations of one rule; the tester's byte-for-byte comparison makes any drift between them a failing test
Recommendation: core diffs. It also means the spec's table (ADDED, REMOVED, MODIFIED) is coded once. Teammates keep full control of what an element is and what its id looks like.
Q2 Who parses the Python files
The decision. Structural and behavioral generators both read Python source. Either the core reads, checks and parses each file once and hands the plugins the result, or each plugin opens and parses files itself.
Why it matters. The spec fixes three failures that must happen before any model is built: a file over 1 MB gives FILE_TOO_LARGE, a binary or non-UTF-8 file gives PARSE_FAILED, and a syntax error gives PARSE_FAILED with the file and line (spec §5.2, one-check diagram). It also says no file may be skipped, because a skipped file would show up as fake REMOVED drift (spec §3.3). If each plugin parses, both must raise the same error, in the same order, with the same message, or T-17's repeatability and the CLI's exit code 2 become inconsistent.
Option
Plugin receives
Cost
Core parses once (recommended)
{path: (text, ast.Module)} for in-scope files
commits everyone to Python's built-in ast; a teammate who wants a different parser (for example LibCST) must ask for it
Core checks size and encoding only
{path: text}
the core still owns the first two errors; each plugin must turn its own syntax error into PARSE_FAILED the same way
Plugins do everything
paths only
all three errors duplicated
Recommendation: core parses once with ast. It is in the standard library, never imports or runs the code (REQ-06), and halves the parse time, which helps the 90 s limit. The middle option is a fine fallback if a teammate needs another parser.
Q3 Who owns scope.json and the path pattern rules
The decision. Three things match file paths against patterns: classification by mapping-v1.1.yaml (contract), scope.json (which files feed the generators) and ownership.json (who owns a path). Spec Q11 lists "path pattern rules for scope.json and ownership.json" as still open. The question is whether that belongs to the teammates with their formats, or to the core.
Why it matters. scope.json is not a model; it is input to all generators, and it is one of the four files /generate must reproduce byte for byte (T-33). Ownership rules are judged by the core's checker (step D), so the core must understand the pattern syntax. If patterns mean different things in different files, src/** could match in classification but not in ownership.
Option
Who decides
Cost
Core owns, reuses the mapping glob (recommended)
core: **/ is zero or more folders, ** anything, * one segment, as in mapping-v1.1.yaml
teammates live with that syntax; nothing new to invent
Core owns, uses gitignore / CODEOWNERS syntax
core
familiar to developers (spec compares ownership to CODEOWNERS), but a second matcher beside the contract's
Teammates own scope and ownership formats
the ownership teammate
core checker blocked until they decide; scope has no natural owner
Recommendation: core owns scope.json and one matcher shared with classification. The ownership teammate still owns the rest of ownership.json and what init proposes.
Q4 Where new code goes
The decision. Today Source/ holds GitHub_Connector (the v1 service) and Frontend_Archive. Phase 4 adds the core, the CLI, plugins, the tester and tests.
Why it matters. Spec §7.1 says one codebase runs as CLI, GitHub Action and hosted service, and §7.1 adoption says a repository installs drifter with pip from a release tag. So the core must be importable without FastAPI or the web app, and must not live inside the web service folder.
Option
Layout
Cost
New package (recommended)
Source/drifter/ (core, CLI, plugins/structural.py, behavioral.py, ownership.py), Source/Tester/, top-level tests/, one pyproject.toml with a drifter entry point
drifter must call git; it imports GitHub_Connector.fetch, or fetch.py moves into drifter later
Everything inside GitHub_Connector
one folder
the CLI would depend on the web service; harder to pip install
Separate repositories
core, service, tester apart
more setup, versions to keep in step
Recommendation: new Source/drifter/ package, plugins one file each so each teammate owns one file. Gives clean ownership of code too.
Q5 Fix GitHub_Connector in place, or rewrite it
The decision. The v1 service was built for an LLM prose check. It cannot start today (it imports LLM_Shell, which is not in the repo) and it differs from contract 2.2.0 in about ten places (see Inputs).
Why it matters. T-01 to T-21 grade exactly this service. It is the shortest path to a working run with Team 16.
Option
Work
Cost
Fix in place (recommended)
remove the LLM call; swap path_rules.json for mapping-v1.1.yaml; add unmapped; rename error codes; one skip reason; 90 s deadline; durable store
keeps tested code (fetch.py clone, short SHA, timeouts; runs.py write-once; course.py coverage); some v1 comments and settings become stale
Rewrite from the v1.1 SPEC
new service built from Team 16's §5 pipeline
cleaner, but repeats work that already handles git edge cases
Recommendation: fix in place, one change per contract item, each proven by the golden test for the 10 cases. AGENTS.md's "surgical changes" rule points the same way.
Q6 Where saved results live
The decision. Every /analyze result must be saved write-once and returned unchanged by GET /analysis/{id}, "also after the system restarts or is redeployed" (contract §1, REQ-04, T-14 to T-16). Today run files go to a folder that is wiped on every redeploy (settings.py says so).
Why it matters. A tester run against us after a redeploy would fail T-14 and T-16 for any result saved before it. Staff may also look up an old analysis_id.
Option
How
Cost
Railway volume (recommended)
mount a persistent volume at runs_dir; code unchanged
needs a volume on the Railway service (a setting, no code); data lives with one host
GitHub repository as store
commit each result as a file to a results repo; Health reports storage: github
survives anything, auditable, but needs a token, is slower and adds rate limits
Hosted database (Postgres, SQLite on volume)
store rows
more code and a new dependency for a write-once file store
Recommendation: Railway volume, since runs.py already writes one file per result atomically. Confirm we deploy on Railway (settings.py reads RAILWAY_GIT_COMMIT_SHA, so it looks like it).
Q7 Does the tester get its own deployment
The decision. The course registry lists a tester URL and a system URL per team. The tester calls the other team's system; the system is called by their tester.
Why it matters. The tester's run can take up to 600 s and makes many outbound calls; the system has a limit of 2 checks at once and its own coverage measurement (course.py counts lines run per session).
Option
How
Cost
Same app, /tester router (recommended)
one FastAPI app serving /system/* and /tester/*
one deploy; but the tester's own lines must be left out of /system/test/report coverage, and a long tester run shares the machine with incoming checks
Separate service
second Railway service from the same repo
clean coverage and resources; one more deploy and URL to keep alive
Recommendation: same app, as long as coverage counts only the system package (it already lists packages explicitly). Switch to a separate service if a 600 s tester run slows our own checks.
Q8 When to change the contract for the mismatches
The decision. The Alignment check found six mismatches. Two are in our spec only (AC-10 "three runs", AC meanings). Others touch docs/contract/, and contract §10 says any change there bumps the version and needs Team 16's agreement.
Why it matters. Each contract bump costs a round of agreement with Team 16. The model goldens will force a bump to 2.3.0 anyway (contract §3 checklist).
Option
When
Cost
Spec now, contract with goldens (recommended)
edit specifications.md today; queue contract items 2, 4, 5 for 2.3.0; tell Team 16 about item 1 and 4 now as a heads-up
one agreement round; the contract carries the small inaccuracies a bit longer
Bump now, again later
2.3.0 now, 2.4.0 with goldens
two rounds of agreement
Never
leave as is
the AC ambiguity can make coverage numbers differ between the two testers
Recommendation: spec now, contract once with the goldens.
Left to the teammates, not asked here: element kinds, id scheme, mining rules, the JSON Schemas and what init proposes for ownership.
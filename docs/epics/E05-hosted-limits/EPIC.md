# E05: Hosted limits and the tester's URL guard

Status: draft · Owner: Kaan

W-row: W1-7 (build order step 2.2) and W1-8 (build order step 2.3) in `docs/state/WORK-ITEMS.md` · Branch: `E05-hosted-limits`

## Goal

No route can swamp real checks or stall the health check, and on Railway the tester cannot be pointed at internal addresses. When this Epic closes: a check that waits for one of the 2 slots counts the wait against its own 80 s deadline and gets 500 `ANALYSIS_FAILED` when the deadline passes while it waits, as spec §7.3 already says (`docs/base/specifications.md:599-601`), for `/system/analyze`, `/system/generate` and `/models/view` alike; `GET /system/health` answers while 40 checks wait; one `/tester/unit/{group}` run at a time, a second gets 409 at once; the tester keeps at most 50 sessions; and `Tester.client.call` refuses every redirect and, on Railway, every target whose address is not globally routable. The `/system` contract and `docs/contract/pod-tester.openapi.yml` do not change. The team and every tester that calls our system need it: today a burst of checks can hold every thread, and the hosted tester can be aimed at Railway's private network.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/behavior.md` changes: its paragraph at line 89, its premises at lines 121 and 122, the state "Cloning, 80 s deadline starts" at line 28, the 500 row at line 84 and the `accDescr` at line 12 describe today's unlimited wait and late deadline. `docs/diagrams/data-flow.md` changes: its premises at line 110 (`analyze`) and line 135 (`/models/view`) cite lines the code steps move, and `/models/view` gains the slot. `docs/diagrams/dependency.md` reads: rule A4, `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`, so the guard reads `RAILWAY_PROJECT_ID` from the environment itself, as `Source/Tester/own_system.py:38` does. Two models change, so `DESIGN.md` sits beside this file.
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W1-7 and W1-8 rows (`docs/state/WORK-ITEMS.md:144-145`) carry the calls marked "Decided by the human, 2026-11-22": the lock, not an off switch, for `/tester/unit`; the session cap of 50 and its drop order; `health` as `async def`; "arrival"; one Epic for both steps; redirects refused on every host; the guard's rules; a refusal as a subclass of `NoReply`; and the live checks as work after the merge.
- Invariants: INV-3 (module boundaries) reads: no new import crosses a contract of `.importlinter`. INV-1 (determinism) and INV-2 (ownership) are not touched: no generator, model or answer changes.
- Other sources: spec §7.3 (`docs/base/specifications.md:595-601`); `docs/contract/pod-contract.md` §6 (one call per request, no retries, 90 s per call, `Source/Tester/client.py:1`, `:13`); `docs/contract/pod-tester.openapi.yml` (the `/test/setup` answers, unchanged); `Source/GitHub_Connector/analysis.py` (`slot`, `analyze`, `generate`); `Source/GitHub_Connector/api.py` (`health`, `models_view`, `STATUS_FOR`); `Source/GitHub_Connector/rules.py:30-40` (what `health` reads); `Source/GitHub_Connector/settings.py:39-43` (deadline 80 s, 2 slots); `Source/Tester/api.py` (`SESSIONS`, `LOCK`, `test_setup`, `test_run`, `unit`); `Source/Tester/client.py` (`call`, `NoReply`); `Source/Tester/pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419` (a `NoReply` in a run is a communication error); `Source/Tester/page.html:317-328`, `:605` (the page calls `/tester/unit` and shows a non-2xx message); anyio's default thread limiter, 40 (`anyio/_backends/_asyncio.py:2941` in anyio 4.12.1).

### Facts this Epic rests on, checked at `81c105a`

- Spec §7.3 says a third check waits for a free slot within its own deadline and gets 500 `ANALYSIS_FAILED` if the deadline passes while it waits (`docs/base/specifications.md:599-601`). The code does not: `with slot():` waits without limit and the deadline is taken after it (`Source/GitHub_Connector/analysis.py:63-67` for analyze, `:128-129` for generate).
- `/models/view` takes no slot and builds its own deadline (`Source/GitHub_Connector/api.py:169-206`, deadline at `:179`). No test calls it: `git grep -n "models/view" -- tests` prints nothing.
- `health` is a sync `def` (`Source/GitHub_Connector/api.py:146`), so it runs in the same 40-thread pool as waiting checks. It does no git, network or lock work: it reads two environment variables (`Source/GitHub_Connector/settings.py:16-19`, `:57-65`) and `rules.config_version()`, which stats the mapping file on each call and reads it only when the file changed (`Source/GitHub_Connector/rules.py:30-40`). That brief local file read is the only I/O it does on the event loop once it is `async def`.
- `/tester/unit/{group}` has no limit (`Source/Tester/api.py:138-143`); each call runs a `pytest` subprocess (`Source/Tester/unit_tests.py:26-38`). The page calls it (`Source/Tester/page.html:605`), so it gets a lock, not an off switch.
- `SESSIONS` is never trimmed: it is written at `Source/Tester/api.py:67` and only read elsewhere (`:29`, `:78`, `:101`, `:116`); nothing deletes from it. A session's states are `ready`, `running` and `done` (`:67`, `:83`, `:90`, `:92`).
- `client.call` uses `urllib.request.urlopen`, whose default opener follows redirects, and checks no address (`Source/Tester/client.py:29-49`).
- Setup answers a `NoReply` with 500, source `communication` (`Source/Tester/api.py:58-59`). A run turns a `NoReply` into a communication error (`Source/Tester/pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419`).
- CI and the image run Python 3.12 (`.github/workflows/ci.yml:20`, `Dockerfile:3`); this checkout runs 3.13.13. The guard unwraps an IPv4-mapped IPv6 address itself, and a test checks it, so it does not depend on what `ipaddress` does on either version.
- Baseline on `main` at `81c105a`: `python -m pytest -q` → `307 passed, 1 warning in 139.71s (0:02:19)`; `python -m pytest tests/tester --collect-only -q` → `53 tests collected`; `python -m pytest tests/connector --collect-only -q` → `73 tests collected`; `python -m pytest tests/docs -q` → `6 passed`; `ruff check` → `All checks passed!`; `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`
- No existing test name matches a `-k` pattern of this Epic: `python -m pytest tests --collect-only -q -k "test_slot_ or test_models_view_ or test_health_answers_while_40_checks_wait or test_unit_run_ or test_session_cap_ or test_guard_ or test_redirect_ or test_setup_guard_"` → `no tests collected (307 deselected)`. No module name matches either: `test_slot_` is not a substring of `test_slots.py`, nor `test_unit_run_` of `test_unit_tests.py`. So every count below can only come from the new tests.

## Steps

One commit per step, made after the step's check passes. 25 new tests in all. Each named test checks one behaviour, and each step's check selects its tests by name.

**Written first** means the test fails at the step's parent commit; **guard** means it passes once written. A written-first test must fail at the parent, not hang: where today's code would wait forever, the test runs the request in a thread, joins it with a timeout, asserts that it ended, and releases the slots it holds in a `finally`.

**No network.** None of the 25 new tests uses the network: the connector tests fake `fetch`, the tester tests use the `fake` target and local servers on `127.0.0.1`, and the guard tests patch `socket.getaddrinfo`. Every per-step Check runs without the network. Only the full suite (Done line 5) clones fixture repositories from GitHub; it takes about 3 minutes (139.71 s on the baseline run), and one earlier run took 14.7.

**Seams.** A: the HTTP routes of the real app with `fetch` faked, as `tests/connector/test_errors.py:24-45` does; the health test serves the app under uvicorn, as the `app_url` fixture does (`tests/tester/test_api.py:13-27`). B: the `/tester` routes on the real app with the `fake` target (`tests/tester/conftest.py:133-141`, `tests/tester/test_api.py`). C: `Tester.client.call`, plus one new public function, `Tester.client.check_target(url)`, tested with `socket.getaddrinfo` patched.

### Step 1/9: count the slot wait against the deadline, for analyze and generate

- Files: `Source/GitHub_Connector/analysis.py`, `tests/connector/test_slots.py` (new)
- What: `analyze` and `generate` take the deadline at arrival, the moment the route's function starts (each route calls them first, `Source/GitHub_Connector/api.py:107-115`), and wait for the slot only until that deadline. A wait that reaches the deadline raises `AnalysisError(ANALYSIS_FAILED)`, which the existing table answers with 500 (`Source/GitHub_Connector/api.py:33-40`, `:71-74`). The deadline handed to `fetch` is the same one, arrival plus `analysis_deadline`. The tests hold both slots themselves, shorten `analysis_deadline` through the settings, and fake `fetch` so that it records the deadline it is given. Tests, seam A:
  - `test_slot_wait_past_the_deadline_is_analysis_failed`: written first. Both slots held, `POST /system/analyze` in a thread, joined with a timeout; it must have ended with 500 `ANALYSIS_FAILED`. At the parent the thread is still waiting at the join, so the test fails; the `finally` releases the slots.
  - `test_slot_wait_counts_against_the_deadline`: written first. Both slots held, released after a short wait; the deadline handed to `fetch` is arrival plus the limit, within a tolerance smaller than the held wait. At the parent it is later by the held wait.
  - `test_slot_wait_past_the_deadline_fails_generate_too`: written first. As the first, for `POST /system/generate`.
  - `test_slot_is_free_again_after_a_check`: guard. After one analyze ends, both slots can be taken at once without waiting.
- Check: `python -m pytest tests/connector/test_slots.py -q -k "test_slot_"` → the summary line starts with `4 passed` and has no `failed`
- Trailer: `Step: 1/9`

### Step 2/9: `/models/view` takes the same slot under the same deadline

- Files: `Source/GitHub_Connector/api.py`, `tests/connector/test_slots.py`
- What: `models_view` waits for a slot until its own deadline, taken at arrival, through the same code in `analysis.py` that `analyze` and `generate` use, so the three routes cannot drift apart. Past the deadline it answers 500 `ANALYSIS_FAILED` and `fetch` is never called. Tests, seam A, `fetch` faked as `api.fetch`:
  - `test_models_view_waits_for_a_slot_and_fails_at_its_deadline`: written first. Both slots held; `GET /models/view` answers 500 `ANALYSIS_FAILED` and the faked `fetch` is never called. At the parent the view takes no slot and calls `fetch` at once, so the test fails without waiting.
  - `test_models_view_frees_its_slot`: guard. After one view ends, both slots can be taken at once without waiting.
- Check: `python -m pytest tests/connector/test_slots.py -q -k "test_models_view_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 2/9`

### Step 3/9: health answers while 40 checks wait

- Files: `Source/GitHub_Connector/api.py`, `tests/connector/test_slots.py`
- What: `health` becomes `async def` with the same body, so it runs on the event loop and not in the 40-thread pool. Test, seam A, the app served under uvicorn on `127.0.0.1` as the `app_url` fixture does:
  - `test_health_answers_while_40_checks_wait`: written first. The test holds both slots, sets a deadline longer than the test, starts 40 `POST /system/analyze` calls in threads and waits until all 40 have arrived; then `GET /system/health` must answer 200 within 1 s. At the parent the 40 waiting calls hold all 40 threads, so health does not answer in 1 s and the test fails. A `finally` releases the slots and joins the 40 threads.
- Check: `python -m pytest tests/connector/test_slots.py -q -k "test_health_answers_while_40_checks_wait"` → the summary line starts with `1 passed` and has no `failed`
- Trailer: `Step: 3/9`

### Step 4/9: one `/tester/unit` run at a time

- Files: `Source/Tester/api.py`, `tests/tester/test_api.py`
- What: the `unit` route takes a lock without waiting; while it is held, a second call answers 409 at once, in the test-route error body with source `tester`, which the page already shows (`Source/Tester/page.html:323-326`). The lock is in the route; `Source/Tester/unit_tests.py` is not changed. Tests, seam B, with `unit_tests.run_group` replaced by a stand-in that blocks on an event:
  - `test_unit_run_second_call_gets_409_at_once`: written first. One call blocks in the stand-in; a second call, run in a thread and joined with a timeout, has ended with 409. At the parent the second call also blocks, so the join times out and the test fails; the `finally` sets the event.
  - `test_unit_run_after_the_first_ended_runs`: guard. Once the first call has ended, the next one runs and answers 200.
- Check: `python -m pytest tests/tester/test_api.py -q -k "test_unit_run_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 4/9`

### Step 5/9: cap the tester's sessions at 50

- Files: `Source/Tester/api.py`, `tests/tester/test_api.py`, `tests/tester/conftest.py` (a setup-call counter on `FakeTarget`)
- What: setup reserves its seat in `SESSIONS` under `LOCK` before the outgoing call, and releases it if setup fails. When 50 seats are taken, it first drops the oldest `done` session; if none is done, the oldest `ready` session, which never ran; if every seat is `running` or reserved by a setup still in flight, it answers 500 with source `tester` and sends nothing to the target. "Oldest" is the order in which the seats were reserved. A reserved seat's id has not been returned to anyone yet, so no other route can reach it. The tests fill `SESSIONS` with 50 seeded sessions and restore it afterwards. Tests, seam B:
  - `test_session_cap_drops_the_oldest_finished_session`: written first. 50 sessions, some `done`; after one setup the oldest `done` one is gone and the new one is there.
  - `test_session_cap_drops_the_oldest_unrun_session_when_none_finished`: written first. 50 sessions, none `done`, some `ready`; the oldest `ready` one is gone.
  - `test_session_cap_refuses_setup_with_500_and_calls_no_target_when_all_are_running`: written first. 50 `running` sessions; setup answers 500 with source `tester`, and the fake target's setup counter has not moved.
- Check: `python -m pytest tests/tester/test_api.py -q -k "test_session_cap_"` → the summary line starts with `3 passed` and has no `failed`
- Trailer: `Step: 5/9`

### Step 6/9: the address guard

- Files: `Source/Tester/client.py`, `tests/tester/test_client.py`, `tests/tester/conftest.py` (a local server that counts its hits and can answer with a given status and headers, used again in steps 7 and 8)
- What: a new public function, `check_target(url)`, runs only when `RAILWAY_PROJECT_ID` is set. It refuses a host ending in `.internal` without a lookup. Otherwise it resolves the host with `socket.getaddrinfo` and refuses if any returned address is not globally routable, after unwrapping an IPv4-mapped IPv6 address to its IPv4 address. A refusal raises `Refused`, a new subclass of `NoReply` that names the host and the address. `call` runs `check_target` before it sends anything, so a refused target receives nothing and a run turns the refusal into a communication error through the existing `NoReply` handling. Tests, seam C, `socket.getaddrinfo` patched where the host is a name:
  - `test_guard_refuses_localhost_on_railway`: written first.
  - `test_guard_refuses_a_loopback_address_on_railway`: written first.
  - `test_guard_refuses_the_metadata_address_on_railway`: written first; the address is `169.254.169.254`.
  - `test_guard_refuses_an_internal_name_on_railway`: written first; the patched `getaddrinfo` is not called.
  - `test_guard_refuses_a_public_name_that_resolves_to_a_private_address_on_railway`: written first.
  - `test_guard_refuses_an_ipv4_mapped_loopback_address_on_railway`: written first; `::ffff:127.0.0.1`.
  - `test_guard_passes_a_public_address_on_railway`: written first. It fails at the parent only because `check_target` does not exist.
  - `test_guard_sends_nothing_to_a_refused_target`: written first. Through `call`, with `RAILWAY_PROJECT_ID` set, a local server on `127.0.0.1` counts zero hits and `call` raises `Refused`. At the parent `call` reaches the server.
  - `test_guard_lets_a_local_run_reach_localhost`: guard. Through `call`, with `RAILWAY_PROJECT_ID` unset, the local server answers.
  The six refusing tests fail at the parent because `check_target` does not exist.
- Check: `python -m pytest tests/tester/test_client.py -q -k "test_guard_"` → the summary line starts with `9 passed` and has no `failed`
- Trailer: `Step: 6/9`

### Step 7/9: refuse redirects

- Files: `Source/Tester/client.py`, `tests/tester/test_client.py`
- What: `call` follows no redirect, on every host. A 3xx answer with a `Location` raises `NoReply` whose message names the new URL; it is not `Refused`, so setup answers it as it answers any other `NoReply`, 500 with source `communication` (step 8's guard test). The three existing tests in `test_client.py` patch `client.urllib.request.urlopen` (`tests/tester/test_client.py:22`, `:35`, `:45`); if `call` stops calling that name, this step repoints their patch, and they stay three tests that pass. Tests, seam C, `RAILWAY_PROJECT_ID` unset, the local server from step 6 answering 302 to a second local server:
  - `test_redirect_is_refused_and_names_the_new_url`: written first.
  - `test_redirect_target_is_never_called`: written first; the second server counts zero hits.
- Check: `python -m pytest tests/tester/test_client.py -q -k "test_redirect_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 7/9`

### Step 8/9: setup answers a refusal with 400

- Files: `Source/Tester/api.py`, `tests/tester/test_api.py`
- What: `test_setup` answers `Refused` with 400, source `tester`, and a message that names the refused host; any other `NoReply` keeps its 500 `communication` answer. With `RAILWAY_PROJECT_ID` set, the test must not use `Tester.client` to reach the app on `127.0.0.1`, because the guard would refuse the test's own call: it calls the app with FastAPI's `TestClient`. Tests, seam B:
  - `test_setup_guard_answers_400_for_an_internal_target_on_railway`: written first. `RAILWAY_PROJECT_ID` set; setup with the `closed_url` fixture's loopback URL (`tests/tester/conftest.py:144-150`) answers 400 and no session is kept. At the parent (step 7) the refusal is a `NoReply`, so setup answers 500.
  - `test_setup_guard_reports_a_redirect_as_a_communication_error`: guard since step 7. `RAILWAY_PROJECT_ID` unset; a target that answers setup with a 302 gives 500, source `communication`, with the new URL in the message.
- Check: `python -m pytest tests/tester/test_api.py -q -k "test_setup_guard_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 8/9`

### Step 9/9: the models, the spec and the queue

- Files: `docs/diagrams/behavior.md`, `docs/diagrams/data-flow.md`, `docs/base/specifications.md`, `docs/state/WORK-ITEMS.md`, `docs/README.md` if a line there goes stale
- What:
  - `behavior.md`: the paragraph at line 89 says the wait counts against the deadline, which runs from arrival, and a wait past it ends in 500 `ANALYSIS_FAILED`; the premises at lines 121 and 122 say the same and cite the new lines; the state at line 28 no longer says the deadline starts at the clone; a transition from the waiting state to the 500 state is drawn, and the `accDescr` (line 12) and the 500 row (line 84) name it; a sentence or premise says `/models/view` takes the same slot and `health` runs on the event loop.
  - `data-flow.md`: the premises at lines 110 and 135 cite the moved lines, and the `/models/view` note (line 101) or its premise says it takes a slot.
  - Spec §7.3 gains the tester's limits (one `/tester/unit` run at a time, at most 50 sessions and the drop order) and the guard (redirects refused; on Railway, no internal address); its slot sentence (lines 599-601) stays true and is kept.
  - `WORK-ITEMS.md`: Next action names E05 as built and waiting for the audit, and W1-7 and W1-8 keep their after-the-merge work.
  - Every `file:line` that steps 1 to 8 moved is re-cited in the files above.
  The checker reads the changed paragraphs of `behavior.md`, `data-flow.md` and §7.3 and does not rely on the grep alone.
- Check: `grep -Pzo -e 'no\s+limit\s+on\s+the\s+wait|nothing\s+limits\s+the\s+wait|starts\s+when\s+the\s+slot\s+is\s+free|starts\s+once\s+the\s+slot\s+is\s+held|Cloning,\s+80\s+s\s+deadline\s+starts' docs/diagrams/behavior.md; python -m pytest tests/docs -q` → the grep prints nothing, then the summary line starts with `6 passed` and has no `failed`. The grep reads the file as one record (`-z`) and `\s+` matches a line break, so a phrase split across two lines is still found. Run on the file as it is today it prints all five old phrases (lines 28, 89, 121, 122), and on a test file holding "no limit" and "on the wait" on two lines it finds the phrase.
- Trailer: `Step: 9/9`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`. CI runs on the pushed HEAD of `E05-hosted-limits`. The branch is pushed once, after step 9, on the human's word; the pull request comes later.
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → every spec line this Epic made wrong is in the diff; empty when the Epic changes no behavior
3. No open row for this Epic: `git grep -n "E05" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The whole suite passes: `python -m pytest -q` → the summary line starts with `332 passed` and has no `failed` (307 at `81c105a`, plus 25). It clones fixture repositories from GitHub and takes about 3 minutes.
6. The connector's new tests pass: `python -m pytest tests/connector/test_slots.py -q` → the summary line starts with `7 passed` and has no `failed`
7. The tester's new tests pass: `python -m pytest tests/tester -q -k "test_unit_run_ or test_session_cap_ or test_guard_ or test_redirect_ or test_setup_guard_"` → the summary line starts with `18 passed` and has no `failed`
8. Lint: `ruff check` → `All checks passed!`
9. Imports still follow the map: `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.` (the line `main` gives at `81c105a`)
10. The old claims are gone from the behavior model: `grep -Pzo -e 'no\s+limit\s+on\s+the\s+wait|nothing\s+limits\s+the\s+wait|starts\s+when\s+the\s+slot\s+is\s+free|starts\s+once\s+the\s+slot\s+is\s+held|Cloning,\s+80\s+s\s+deadline\s+starts' docs/diagrams/behavior.md` → prints nothing

The live checks are not Done lines, because they need the deploy. They are work after the merge, listed in the W-rows (`docs/state/WORK-ITEMS.md:144-145`): the live page against our own system, a public URL and Team 16's system (one run, report read), and the timing run of step 2.2, which waits until contract 2.5.0 is sent.

## Out of scope

Each is a conscious choice, not an oversight.

- Pinning the checked address against a DNS answer that changes between the check and the connection. `check_target` resolves the host, then `urllib` resolves it again to connect; a name whose answer changes in between passes the guard.
- A limit on concurrent `/tester/test/run` calls. Each run holds a thread for its whole length (`Source/Tester/api.py:86`), so 40 runs at once still fill the thread pool.
- The other sync routes, such as `GET /system/analysis/{id}`, `/tester/test/report` and the console's files, which still wait for a thread while 40 checks wait. Only `health` moves to the event loop.
- The tester split (W3-6).
- Not covered by a named test, left to the builder and the auditor's reading: that setup releases its reserved seat when the target's setup fails or gives no answer, and that a refusal or a redirect in the middle of a run is reported as a communication error (the existing `NoReply` handling in `Source/Tester/pod_tests.py` does it, and no new code is added there).

## Open questions

None. The human decided every call this Epic needs on 2026-11-22, and the W1-7 and W1-8 rows record them (`docs/state/WORK-ITEMS.md:144-145`). Two readings follow from those calls and are stated in the steps, for the reviewer to check: a redirect raises a plain `NoReply`, not `Refused`, so setup answers it with 500 `communication` (step 8's second test) and only an address refusal gets 400; and a seat reserved by a setup still in flight is not dropped by the cap, like a running session.

## Review

Not reviewed yet. The design reviewer writes its verdict here.

# E05: Hosted limits and the tester's URL guard

Status: draft · Owner: Kaan

W-row: W1-7 (build order step 2.2) and W1-8 (build order step 2.3) in `docs/state/WORK-ITEMS.md` · Branch: `E05-hosted-limits`

## Goal

No route can swamp real checks or stall the health check, and on Railway the tester cannot be pointed at internal addresses. When this Epic closes: a check that waits for one of the 2 slots counts the wait against its own 80 s deadline and gets 500 `ANALYSIS_FAILED` when the deadline passes while it waits, as spec §7.3 already says (`docs/base/specifications.md:599-601`), for `/system/analyze`, `/system/generate` and `/models/view` alike; `GET /system/health` answers while 40 checks wait; one `/tester/unit/{group}` run at a time, a second gets 409 at once; the tester keeps at most 50 sessions; and `Tester.client.call` follows no redirect, returning the 3xx as the answer with the new URL, and, on Railway, refuses before sending anything every target whose address is not globally routable. Setup passes a 3xx through as the tester contract's `default` answer reads: the target's status, its body's message and source when it gives them, and otherwise source `system` and a message that names the new URL. It answers an address refusal with 400. The `/system` contract and `docs/contract/pod-tester.openapi.yml` do not change. The team and every tester that calls our system need it: today a burst of checks can hold every thread, and the hosted tester can be aimed at Railway's private network.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/behavior.md` changes: its paragraph at line 89, its premises at lines 121 and 122, the state "Cloning, 80 s deadline starts" at line 28, the 500 row at line 84 and the `accDescr` at line 12 describe today's unlimited wait and late deadline. `docs/diagrams/data-flow.md` changes: its premises at line 110 (`analyze`) and line 135 (`/models/view`) cite lines the code steps move, and `/models/view` gains the slot. `docs/diagrams/dependency.md` reads: rule A4, `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`, so the guard reads `RAILWAY_PROJECT_ID` from the environment itself, as `Source/Tester/own_system.py:38` does. Two models change, so `DESIGN.md` sits beside this file.
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W1-7 and W1-8 rows (`docs/state/WORK-ITEMS.md:144-145`) carry the calls marked "Decided by the human, 2026-11-22": the lock, not an off switch, for `/tester/unit`; the session cap of 50 and its drop order; `health` as `async def`; "arrival"; one Epic for both steps; a redirect never followed, on any host; the guard's rules; the ruling on URL-1, raised by the first review of this Epic (a 3xx returned as a `Reply` with its new URL and passed through at setup, an address refusal a `Refused` that setup answers with 400); and the live checks as work after the merge.
- Invariants: INV-3 (module boundaries) reads: no new import crosses a contract of `.importlinter`. INV-1 (determinism) and INV-2 (ownership) are not touched: no generator, model or answer changes.
- Other sources: spec §7.3 (`docs/base/specifications.md:595-601`); `docs/contract/pod-contract.md` §6 (one call per request, no retries, 90 s per call, `Source/Tester/client.py:1`, `:13`); `docs/contract/pod-tester.openapi.yml` (the `/test/setup` answers, unchanged: 400 at `:34-36`, and the `default` answer at `:37-42`, which passes the system's status, message and source through); `Source/GitHub_Connector/analysis.py` (`slot`, `analyze`, `generate`); `Source/GitHub_Connector/api.py` (`health`, `models_view`, `STATUS_FOR`); `Source/GitHub_Connector/rules.py:30-40` (what `health` reads); `Source/GitHub_Connector/settings.py:39-43` (deadline 80 s, 2 slots); `Source/Tester/api.py` (`SESSIONS`, `LOCK`, `test_setup`, `test_run`, `unit`); `Source/Tester/client.py` (`call`, `NoReply`); `Source/Tester/pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419` (a `NoReply` in a run is a communication error); `Source/Tester/page.html:317-328`, `:605` (the page calls `/tester/unit` and shows a non-2xx message); anyio's default thread limiter, 40 (`anyio/_backends/_asyncio.py:2941` in anyio 4.12.1).

### Facts this Epic rests on, checked at `81c105a`

- Spec §7.3 says a third check waits for a free slot within its own deadline and gets 500 `ANALYSIS_FAILED` if the deadline passes while it waits (`docs/base/specifications.md:599-601`). The code does not: `with slot():` waits without limit and the deadline is taken after it (`Source/GitHub_Connector/analysis.py:63-67` for analyze, `:128-129` for generate).
- `/models/view` takes no slot and builds its own deadline (`Source/GitHub_Connector/api.py:169-206`, deadline at `:179`). No test calls it: `git grep -n "models/view" -- tests` prints nothing.
- `health` is a sync `def` (`Source/GitHub_Connector/api.py:146`), so it runs in the same 40-thread pool as waiting checks. It does no git, network or lock work: it reads two environment variables (`Source/GitHub_Connector/settings.py:16-19`, `:57-65`) and `rules.config_version()`, which stats the mapping file on each call and reads it only when the file changed (`Source/GitHub_Connector/rules.py:30-40`). That brief local file read is the only I/O it does on the event loop once it is `async def`.
- `/tester/unit/{group}` has no limit (`Source/Tester/api.py:138-143`); each call runs a `pytest` subprocess (`Source/Tester/unit_tests.py:26-38`). The page calls it (`Source/Tester/page.html:605`), so it gets a lock, not an off switch.
- `SESSIONS` is never trimmed: it is written at `Source/Tester/api.py:67` and only read elsewhere (`:29`, `:78`, `:101`, `:116`); nothing deletes from it. A session's states are `ready`, `running` and `done` (`:67`, `:83`, `:90`, `:92`).
- `client.call` uses `urllib.request.urlopen`, whose default opener follows redirects, and checks no address (`Source/Tester/client.py:29-49`).
- Setup answers a `NoReply` with 500, source `communication` (`Source/Tester/api.py:58-59`). It already passes any non-2xx status through, with the body's `message` or "system setup answered N", and source `system` unless the body names another (`:60-65`). `Reply` is built only in `client.py` (`git grep -n "Reply(" -- Source tests` → `Source/Tester/client.py:49`, besides the `NoReply` lines). A run turns a `NoReply` into a communication error (`Source/Tester/pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419`).
- CI and the image run Python 3.12 (`.github/workflows/ci.yml:20`, `Dockerfile:3`); this checkout runs 3.13.13. The guard unwraps an IPv4-mapped IPv6 address itself, and a test checks it, so it does not depend on what `ipaddress` does on either version.
- Baseline on `main` at `81c105a`: `python -m pytest -q` → `307 passed, 1 warning in 139.71s (0:02:19)`; `python -m pytest tests/tester --collect-only -q` → `53 tests collected`; `python -m pytest tests/connector --collect-only -q` → `73 tests collected`; `python -m pytest tests/docs -q` → `6 passed`; `ruff check` → `All checks passed!`; `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.`
- No existing test name matches a `-k` pattern of this Epic: `python -m pytest tests --collect-only -q -k "test_slot_ or test_models_view_ or test_health_answers_while_40_checks_wait or test_unit_run_ or test_session_cap_ or test_guard_ or test_redirect_ or test_setup_guard_"` → `no tests collected (307 deselected)`. Re-run after the review's ruling, with the new names spelled out as well (`... or test_session_cap_frees_the_seat_of_a_setup_that_failed or test_setup_guard_passes_a_redirect_through_and_names_the_new_url`) → `no tests collected (307 deselected)`. No module name matches either: `test_slot_` is not a substring of `test_slots.py`, nor `test_unit_run_` of `test_unit_tests.py`. So every count below can only come from the new tests.

## Steps

One commit per step, made after the step's check passes. 26 new tests in all: 7 in the connector, 19 in the tester. Each named test checks one behaviour, and each step's check selects its tests by name.

**Written first** means the test fails at the step's parent commit; **guard** means it passes once written. A written-first test must fail at the parent, not hang: where today's code would wait forever, the test runs the request in a thread, joins it with a timeout, asserts that it ended, and releases the slots it holds in a `finally`.

**No network.** None of the 26 new tests uses the network: the connector tests fake `fetch`, the tester tests use the `fake` target and local servers on `127.0.0.1`, and the guard tests patch `socket.getaddrinfo`. Every per-step Check runs without the network. Only the full suite (Done line 5) clones fixture repositories from GitHub; it takes about 3 minutes (139.71 s on the baseline run), and one earlier run took 14.7.

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
- What: setup reserves its seat in `SESSIONS` under `LOCK` before the outgoing call, and releases it if setup fails. When 50 seats are taken, it first drops the oldest `done` session; if none is done, the oldest `ready` session, which never ran; if every seat is `running` or reserved by a setup still in flight, it answers 500 with source `tester` and sends nothing to the target. "Oldest" is the order in which the seats were reserved. A reserved seat's id has not been returned to anyone yet, so no other route can reach it. The cap is a module constant in `Tester/api.py`, so a test can lower it. The tests fill `SESSIONS` with seeded sessions and restore it afterwards. Tests, seam B:
  - `test_session_cap_drops_the_oldest_finished_session`: written first. 50 sessions, some `done`; after one setup the oldest `done` one is gone and the new one is there.
  - `test_session_cap_drops_the_oldest_unrun_session_when_none_finished`: written first. 50 sessions, none `done`, some `ready`; the oldest `ready` one is gone.
  - `test_session_cap_refuses_setup_with_500_and_calls_no_target_when_all_are_running`: written first. 50 `running` sessions; setup answers 500 with source `tester`, and the fake target's setup counter has not moved.
  - `test_session_cap_frees_the_seat_of_a_setup_that_failed`: written first. With the cap at 1 and `SESSIONS` empty, a setup the target refuses (the `fake` target's `setup_answer` set to a 409) and a setup the target does not answer (the `closed_url` fixture) each leave the seat free, so the next setup succeeds with 201. At the parent no session is kept after a failed setup either, so the test fails there only because the cap constant does not exist yet.
- Check: `python -m pytest tests/tester/test_api.py -q -k "test_session_cap_"` → the summary line starts with `4 passed` and has no `failed`
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

### Step 7/9: follow no redirect

- Files: `Source/Tester/client.py`, `tests/tester/test_client.py`
- What: `call` follows no redirect, on every host (the W1-8 ruling, `docs/state/WORK-ITEMS.md:145`). A 3xx answer comes back as a `Reply` with its 3xx status, and the `Reply` carries the new URL from the `Location` header in a new field that defaults to none, so every other `Reply` is built as before. It is not a `NoReply`. During a run a 3xx is a status like any other, judged by the test that received it; `Source/Tester/pod_tests.py` gets no new code. The three existing tests in `test_client.py` patch `client.urllib.request.urlopen` (`tests/tester/test_client.py:22`, `:35`, `:45`); if `call` stops calling that name, this step repoints their patch, and they stay three tests that pass. Tests, seam C, `RAILWAY_PROJECT_ID` unset, the local server from step 6 answering 302 to a second local server:
  - `test_redirect_is_refused_and_names_the_new_url`: written first. `call` returns a `Reply` whose status is the 302 and whose new URL is the second server's. At the parent `urllib` follows the redirect and returns the second server's 200, so the test fails.
  - `test_redirect_target_is_never_called`: written first; the second server counts zero hits.
- Check: `python -m pytest tests/tester/test_client.py -q -k "test_redirect_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 7/9`

### Step 8/9: setup answers a refusal with 400 and passes a redirect through

- Files: `Source/Tester/api.py`, `tests/tester/test_api.py`
- What: following the W1-8 ruling (`docs/state/WORK-ITEMS.md:145`), `test_setup` answers `Refused` with 400, source `tester`, and a message that names the refused host, read as a `target_url` the hosted tester will not accept; any other `NoReply` keeps its 500 `communication` answer. A 3xx from the target's setup is passed through as the contract's `default` answer reads (`docs/contract/pod-tester.openapi.yml:37-42`): the target's status always; the body's own `message` and a `source` it names in `SOURCES` pass through unchanged, as `Source/Tester/api.py:60-65` already does and as the contract and the course PDF (p. 3) require (Open questions, reading 3); when the body gives none, the source is `system` and the message names the new URL and says the tester does not follow redirects. The answer carries no `Location` header, so a browser on the page does not follow it either. With `RAILWAY_PROJECT_ID` set, the test must not use `Tester.client` to reach the app on `127.0.0.1`, because the guard would refuse the test's own call: it calls the app with FastAPI's `TestClient`. Use `TestClient` without `with`, or set `RAILWAY_VOLUME_MOUNT_PATH` to a temp folder: with `with`, the app's startup hook refuses to start on Railway without a volume (`Source/GitHub_Connector/settings.py:68-71`, `Source/GitHub_Connector/api.py:45-49`). Tests, seam B:
  - `test_setup_guard_answers_400_for_an_internal_target_on_railway`: written first. `RAILWAY_PROJECT_ID` set; setup with the `closed_url` fixture's loopback URL (`tests/tester/conftest.py:144-150`) answers 400 and no session is kept. At the parent (step 7) the refusal is a `NoReply`, so setup answers 500.
  - `test_setup_guard_passes_a_redirect_through_and_names_the_new_url`: written first. `RAILWAY_PROJECT_ID` unset; a target that answers setup with a 302, a `Location` and a body with no `message`, gives 302, source `system`, with the new URL in the message. At the parent (step 7) setup already passes the 302 through with source `system` (`Source/Tester/api.py:60-65`), but its message is "system setup answered 302", which does not name the new URL, so the test fails.
- Check: `python -m pytest tests/tester/test_api.py -q -k "test_setup_guard_"` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 8/9`

### Step 9/9: the models, the spec and the queue

- Files: `docs/diagrams/behavior.md`, `docs/diagrams/data-flow.md`, `docs/base/specifications.md`, `docs/state/WORK-ITEMS.md`, `docs/README.md` if a line there goes stale
- What:
  - `behavior.md`: the paragraph at line 89 says the wait counts against the deadline, which runs from arrival, and a wait past it ends in 500 `ANALYSIS_FAILED`; the premises at lines 121 and 122 say the same and cite the new lines; the state at line 28 no longer says the deadline starts at the clone; a transition from the waiting state to the 500 state is drawn, and the `accDescr` (line 12) and the 500 row (line 84) name it; a sentence or premise says `/models/view` takes the same slot and `health` runs on the event loop.
  - `data-flow.md`: the premises at lines 110 and 135 cite the moved lines, and the `/models/view` note (line 101) or its premise says it takes a slot.
  - Spec §7.3 gains the tester's limits (one `/tester/unit` run at a time, at most 50 sessions and the drop order) and the guard (no redirect followed: setup passes a 3xx through as the contract reads, with source `system` and the new URL when the body gives no message; on Railway, no internal address, answered 400 at setup); its slot sentence (lines 599-601) stays true and is kept.
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

5. The whole suite passes: `python -m pytest -q` → the summary line starts with `333 passed` and has no `failed` (307 at `81c105a`, plus 26). It clones fixture repositories from GitHub and takes about 3 minutes.
6. The connector's new tests pass: `python -m pytest tests/connector/test_slots.py -q` → the summary line starts with `7 passed` and has no `failed`
7. The tester's new tests pass: `python -m pytest tests/tester -q -k "test_unit_run_ or test_session_cap_ or test_guard_ or test_redirect_ or test_setup_guard_"` → the summary line starts with `19 passed` and has no `failed`
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

## Open questions

The human decided the calls in the W1-7 and W1-8 rows on 2026-11-22 (`docs/state/WORK-ITEMS.md:144-145`). Two questions came up in the first review, at `2f13155`; both are answered.

- Reading 1, how setup answers a target that redirects. The first review found the draft's answer, 500 `communication`, at odds with the tester contract's `default` answer, which passes a system response's status through and keeps 500 `communication` for "no system response at all" (`docs/contract/pod-tester.openapi.yml:37-42`), and raised row URL-1. Answered by the human's ruling on URL-1, recorded in the W1-8 row as "Decided by the human, 2026-11-22" (`docs/state/WORK-ITEMS.md:145`), and the row removed: `client.call` returns a 3xx as a `Reply` that carries the new URL, not a `NoReply`; setup passes the 3xx through with source `system` and a message that names the new URL and says the tester does not follow redirects; during a run a 3xx is judged by the test that received it, with no new code in `Source/Tester/pod_tests.py`; an address refusal stays `Refused`, a subclass of `NoReply`, which setup answers with 400, read as a `target_url` the hosted tester will not accept, and which a run reports as a communication error. Steps 7 and 8 follow it.
- Reading 2, a seat reserved by a setup in flight is not dropped: holds. The drop order names only "the oldest finished session" and "the oldest that is ready and never ran" (`docs/state/WORK-ITEMS.md:144`); a reserved seat is neither, since today a session exists only after the target's setup answered (`Source/Tester/api.py:56-67`).
- Reading 3, raised by the second review at `bb447ae`: what setup answers when the target's 3xx body carries its own `message` or `source`. Answered by the contract, which outranks the W1-8 row: the system's status, message and source are passed through unchanged (`docs/contract/pod-tester.openapi.yml:38-40`; the course PDF, `docs/base/student-facing-spec.docx.pdf` p. 3, "If system setup returns an error, return the same status, message, and source"), as `Source/Tester/api.py:60-65` already does. So a body's own `message` and a `source` in `SOURCES` win; the message that names the new URL and says the tester does not follow redirects replaces only the fallback "system setup answered N", and the source is `system` only when the body names none. The ruling invokes the same `default` answer (`docs/state/WORK-ITEMS.md:145`), so this follows it.

## Review

Revised after the verdict below, at the commit that follows `bb447ae`: the Goal, step 8, step 9's spec line, `DESIGN.md` (Intended structure and E05-5) and a note in the W1-8 row now say a 3xx body's own `message` and `source` pass through, and the new-URL message and source `system` apply only when the body gives none (reading 3). The step 7 test name is kept as the human asked; `RULED/` is not written, as the human asked. The next reviewer writes its verdict above this paragraph.

REVISE · design-reviewer at bb447ae · 2026-11-22

- Blocking: the Goal (line 9), step 8's What (line 120) and `DESIGN.md` (Intended structure, "The guard, in the client"; Must stay true, E05-5) say setup answers every 3xx with source `system` and a message that names the new URL. For a 3xx whose body carries its own `message` or `source`, that overrides what the tester contract (level 2) and the course PDF (level 1) say is passed through unchanged (`docs/contract/pod-tester.openapi.yml:38-40`; `docs/base/student-facing-spec.docx.pdf` p. 3; Open questions, reading 3). For RATIFY: those four places say the body's own `message` and named `source` pass through as `Source/Tester/api.py:60-65` does today, and the new-URL message and source `system` apply only when the body gives none. Step 8's two tests stay valid as written (the redirect test's body has no `message`); a third test for a 3xx body with its own message is optional and, if added, the totals (26, 19, 333) and the Done lines 5 and 7 move with it.
- Not blocking, for the builder: step 7's `test_redirect_is_refused_and_names_the_new_url` still says "refused", though after the URL-1 ruling a redirect is returned as a `Reply`, and `Refused` names the address guard's exception. A name such as `test_redirect_is_returned_with_the_new_url` keeps the `-k "test_redirect_"` selection and every count (`docs/state/WORK-ITEMS.md:145`).
- Not blocking, process: row URL-1 left `docs/decisions/OPEN-DECISIONS.md` in `bb447ae`, an agent commit, with the ruling written only into the W1-8 row, while `docs/decisions/RULED/README.md` says an answered row leaves in the same commit that files its ruling in `RULED/`, and `OPEN-DECISIONS.md` says the human moves it there. The ruling's 400 for an address refusal reads the contract's `400`, "Invalid request (missing or malformed target_url)" (`docs/contract/pod-tester.openapi.yml:34-35`), as covering a `target_url` the hosted tester will not accept; I judge that within "Invalid request" and so no contradiction, but a level-3 home for that reading would be the human filing `RULED/URL-1-...` from `docs/templates/RULED.md`.
- Every other claim holds on disk at `bb447ae` (no file under `Source/` or `tests/` changed since `81c105a`: `git diff --stat 81c105a bb447ae -- Source tests` prints nothing). Checked: every `file:line` in Relies on, Facts, Seams and steps 1 to 9 (`analysis.py:49-67`, `:124-129`; `api.py:20`, `:33-40`, `:45-49`, `:71-74`, `:106-115`, `:146`, `:169-206`, `:179`; `settings.py:16-19`, `:39-43`, `:57-71`; `rules.py:30-40`; `own_system.py:38`; `Tester/api.py:29-30`, `:56-67`, `:77-93`, `:101`, `:116`, `:138-143`; `client.py:1`, `:13`, `:16-49`; `pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419`; `page.html:317-328`, `:605`; `unit_tests.py:26-38`; `conftest.py:133-150`; `test_api.py:13-27`; `test_errors.py:24-45`; `test_client.py:22`, `:35`, `:45`; `ci.yml:20`; `Dockerfile:3`; `pod-contract.md` §6 lines 256-261; `pod-tester.openapi.yml:34-42`; spec `:595-601`; `behavior.md:12`, `:28`, `:84`, `:89`, `:121`, `:122`; `data-flow.md:101`, `:110`, `:135`; `WORK-ITEMS.md:144-145`; `dependency.md` A4 at `:79`); every DESIGN premise command (`git grep` for `with slot()|analysis_deadline` gives `:66,:67,:128,:129`; `api.py` gives only `:179`; `def health` at `:146`; `Reply(` only at `client.py:49` besides `NoReply`; `RAILWAY_PROJECT_ID` at `settings.py:70`, `own_system.py:38`, `test_storage.py`, `test_own_system.py`); anyio 4.12.1 `CapacityLimiter(40)` at `_asyncio.py:2941`; `git grep -n "models/view" -- tests` prints nothing; `tests/tester` 53 and `tests/connector` 73 collected; the full `-k` set, new names included, gives `no tests collected (307 deselected)`; `tests/docs` `6 passed`; `ruff check` `All checks passed!`; `PYTHONPATH=Source lint-imports` `Contracts: 5 kept, 0 broken.`; the step 9 grep prints all five old phrases today and finds a phrase split across two lines. No existing test sets `RAILWAY_PROJECT_ID` and then calls `Tester.client`, so the guard breaks none. Counts add up: 4+2+1+2+4+9+2+2 = 26; connector 7 (73+7 = 80, E05-1); tester 19; 307+26 = 333; `-k "test_guard_"` does not match `test_setup_guard_`.
- Readings 1 and 2 are answered with sources; reading 3 is answered from the contract. No question needs a row in `OPEN-DECISIONS.md`.
- Checks on form pass: the filled-copy grep (`docs/templates/README.md`) prints nothing for `EPIC.md` and `DESIGN.md`; each step names its files, one check with its output, and its trailer; each Done line but the human's is a command with its output; `DESIGN.md` exists for the changes to `behavior.md` and `data-flow.md`.

Revised after the verdict below: the human ruled on URL-1 (Open questions, reading 1), steps 5, 7 and 8 and the totals changed, and the next reviewer writes its verdict above this line.

REVISE · design-reviewer at 2f13155 · 2026-11-22

- Blocking: how `POST /tester/test/setup` answers a target that redirects is unsettled. Step 7 and step 8's `test_setup_guard_reports_a_redirect_as_a_communication_error` make it 500 `communication`, but W1-8 reads as 400 for any refusal, a refused redirect included, and the tester contract's `default` answer passes a system response's status through. For RATIFY: the human answers a row in `docs/decisions/OPEN-DECISIONS.md` (400 `tester`, 500 `communication`, or the 3xx passed through with source `system`), and steps 7 and 8, the Goal and Open questions follow it and cite the row or its `RULED/` id (`docs/state/WORK-ITEMS.md:145`; `docs/contract/pod-tester.openapi.yml:34-41`; this file, Open questions, reading 1).
- Every other claim holds on disk at `2f13155` (the code under `Source/` is unchanged since `81c105a`): every cited `file:line` in Relies on, Facts, Seams and steps; every DESIGN premise command (`git grep` outputs for `analysis.py:66,67,128,129`, `api.py:179`, `api.py:146`, `SESSIONS` at `Tester/api.py:29,67,78,101,116`, `RAILWAY_PROJECT_ID` at `settings.py:70`, `own_system.py:38`); anyio 4.12.1 `CapacityLimiter(40)` at `_asyncio.py:2941`; `tests/tester` 53 and `tests/connector` 73 collected; the `-k` set collects nothing (307 deselected); `tests/docs` 6 passed; `ruff check` "All checks passed!"; `lint-imports` "Contracts: 5 kept, 0 broken."; the step 9 grep prints all five old phrases today and finds a phrase split across two lines. Counts add up: 4+2+1+2+3+9+2+2 = 25, connector 7, tester 18, 307+25 = 332, connector 73+7 = 80 (E05-1).
- Reading 2 (in-flight seat not dropped) is settled from `docs/state/WORK-ITEMS.md:144` and `Source/Tester/api.py:56-67`; see Open questions.
- Not blocking, for the builder: step 8 sets `RAILWAY_PROJECT_ID` and calls the app through `TestClient`; with no volume, `require_volume_on_railway` raises in the lifespan (`Source/GitHub_Connector/settings.py:68-71`, `api.py:45-49`), so use `TestClient` without `with`, or set `RAILWAY_VOLUME_MOUNT_PATH` to a temp folder.
- Not blocking: the 400 for an address refusal sits under the tester contract's `400` response, described as "missing or malformed target_url" (`docs/contract/pod-tester.openapi.yml:34-35`); the same row could record the human's call on it in `RULED/`, since the W-row decisions rank below the contract.
- Checks on form pass: the filled-copy grep prints nothing for `EPIC.md` and `DESIGN.md`; each step names files, one check with its output, and its trailer; each Done line but the human's is a command with its output; `DESIGN.md` exists for the two model changes.

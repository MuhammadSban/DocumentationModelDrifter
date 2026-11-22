# Hosted limits and the tester's URL guard

Epic: `docs/epics/E05-hosted-limits/EPIC.md`

## Intended structure

Paths are under `Source/`.

- **The slot, one place.** `GitHub_Connector.analysis` keeps the one semaphore of 2 slots (`slot`, `analysis.py:49-60`) and gains the one way to wait for it: until a deadline taken at arrival, raising `AnalysisError(ANALYSIS_FAILED)` when the deadline passes first. `analyze`, `generate` and the `/models/view` route all wait through it, and hand the same deadline to `fetch`. `GitHub_Connector.api` already imports from `analysis` (`api.py:20`), so no new import crosses a layer.
- **Health on the event loop.** `GitHub_Connector.api.health` becomes `async def` with the same body. Every other route stays as it is.
- **The tester's own limits, in its route module.** `Tester.api` holds a second lock for `/tester/unit/{group}`, taken without waiting, and the session cap of 50 inside `test_setup`, under the existing `LOCK`. `Tester.unit_tests` does not change.
- **The guard, in the client.** `Tester.client` gains `check_target(url)` and `Refused(NoReply)`, and `call` runs `check_target` before it sends and follows no redirect. The guard reads `RAILWAY_PROJECT_ID` from the environment, as `Tester.own_system` does (`own_system.py:38`), because `Tester` may not import `GitHub_Connector.settings` (rule A4, `docs/diagrams/dependency.md`). `Tester.api.test_setup` answers `Refused` with 400; `Tester.pod_tests` is unchanged and keeps turning any `NoReply` into a communication error.
- **Models.** `docs/diagrams/behavior.md` changes: the waiting state gains a transition to 500, the clone state no longer starts the deadline, and the paragraph and premises on the three limits say the wait counts against the deadline. `docs/diagrams/data-flow.md` changes: its premises cite the moved lines and `/models/view` takes a slot. `docs/diagrams/dependency.md` does not change: no package, layer or allowed call is added.

## Premises, verified

Every fact the structure rests on, checked against the disk at `81c105a` before it is written here.

| Premise | How verified | Holds? |
|---|---|---|
| `analyze` and `generate` wait for the slot without limit and take the deadline after it. | `git grep -n -E "with slot\(\)|analysis_deadline" -- Source/GitHub_Connector/analysis.py` → `:66`, `:67`, `:128`, `:129` | yes |
| `/models/view` takes no slot and takes its own deadline. | `git grep -n -E "slot|analysis_deadline" -- Source/GitHub_Connector/api.py` → only `:179` | yes |
| `health` is a sync route. | `git grep -n "def health" -- Source/GitHub_Connector/api.py` → `146:def health() -> dict[str, object]:` | yes |
| `health` does no git, network or lock work: two environment reads and `rules.config_version()`, which stats the mapping file and reads it only when it changed. | `Source/GitHub_Connector/api.py:146-154`; `Source/GitHub_Connector/settings.py:16-19`, `:57-65`; `Source/GitHub_Connector/rules.py:30-40` | yes |
| A sync route runs in anyio's thread pool, which holds 40 threads by default. | `anyio/_backends/_asyncio.py:2941`, `CapacityLimiter(40)`, in anyio 4.12.1 | yes |
| The connector's error table maps `ANALYSIS_FAILED` to 500 and is not changed. | `Source/GitHub_Connector/api.py:33-40` | yes |
| `/tester/unit/{group}` has no limit, and the page calls it and shows a non-2xx message. | `Source/Tester/api.py:138-143`; `Source/Tester/page.html:317-328`, `:605` | yes |
| `SESSIONS` is written once per setup and never trimmed. | `git grep -n "SESSIONS" -- Source/Tester/` → `:29`, `:67`, `:78`, `:101`, `:116`, no delete | yes |
| `call` follows redirects and checks no address. | `Source/Tester/client.py:29-49`, `urllib.request.urlopen` with the default opener | yes |
| Setup answers a `NoReply` with 500 `communication`, and a run turns a `NoReply` into a communication error. | `Source/Tester/api.py:58-59`; `Source/Tester/pod_tests.py:106-108`, `:388-389`, `:398-399`, `:419` | yes |
| `RAILWAY_PROJECT_ID` is the repository's on-Railway signal, and tests set it per test. | `git grep -n "RAILWAY_PROJECT_ID" -- Source tests` → `settings.py:70`, `own_system.py:38`, `test_storage.py`, `test_own_system.py` | yes |
| `Tester` imports none of `GitHub_Connector`, `Frontend` and `drifter`. | `.importlinter`, contract `tester`; `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.` | yes |
| CI and the image run Python 3.12, so the IPv4-mapped unwrapping is tested on 3.12 in CI. | `.github/workflows/ci.yml:20`; `Dockerfile:3` | yes |

## Must stay true

| ID | What must stay true | Check |
|---|---|---|
| E05-1 | `/system` answers and error codes are unchanged: no schema, error code or contract file changes, and every existing connector test passes. | `git diff --exit-code main...HEAD -- Source/GitHub_Connector/schemas.py docs/contract` → prints nothing; `python -m pytest tests/connector -q` → the summary line starts with `80 passed` and has no `failed` |
| E05-2 | `docs/contract/pod-tester.openapi.yml` is unchanged. | `git diff --exit-code main...HEAD -- docs/contract/pod-tester.openapi.yml` → prints nothing |
| E05-3 | A local run still reaches localhost: with `RAILWAY_PROJECT_ID` unset the guard does nothing. | `python -m pytest tests/tester/test_client.py -q -k "test_guard_lets_a_local_run_reach_localhost"` → the summary line starts with `1 passed` and has no `failed`; the existing tester tests that run against the `fake` target on `127.0.0.1` pass in Done line 5 |
| E05-4 | Every public http(s) URL that answers without a redirect still works on Railway. A URL that answers with a redirect is refused, on every host, by the human's call (W1-8). | `python -m pytest tests/tester/test_client.py -q -k "test_guard_passes_a_public_address_on_railway"` → the summary line starts with `1 passed` and has no `failed` |
| INV-3 | Imports under `Source/` follow the module map, and the import contracts hold. | `PYTHONPATH=Source lint-imports` → `Contracts: 5 kept, 0 broken.` |

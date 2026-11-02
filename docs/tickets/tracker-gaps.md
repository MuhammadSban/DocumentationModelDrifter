# Open work: from one check to a working tracker

Written 2026-11-01, when `drift` and `drift_error` were first wired onto `POST /system/analyze`.
Open work only. Each row says what is missing, the fix, and the check that closes it. Nothing here
is a contradiction between documents: those live in `contract-contradictions.md`.

Order: the first table is what the drift check itself still owes, the second is what turns a check
into a tracker. `docs/base/phase4.md` owns the schedule; this file owns the detail behind its rows.

## 1. What the wired check still owes

| # | Missing | Fix | Check that closes it |
| --- | --- | --- | --- |
| 1 | The behavioral generator. No behavioral generator is registered in `GENERATORS`, so behavioral drift cannot be found and `models/behavioral.json` is read but never compared. | Barshan's `generate_behavioral(files)`, registered as `GENERATORS["behavioral"]` in `check.py`. | A behavioral difference appears in `drift.behavioral` for a changed state machine (T-24 to T-31). |
| 2 | Schema validation of the committed models. `INVALID_MODELS` fires on unreadable JSON, a break of the element rule and a malformed `scope.json` (#15), but no owner schema is checked, so a model whose attributes have the wrong shape reaches the comparison and shows up as drift instead of as no verdict. | Validate each file against its owner's `*.schema.json` (model-seam.md) before comparing. | A model file with a valid-JSON but wrong shape gives `INVALID_MODELS`, not a difference list. |
| 3 | Two blob downloads per check, not one. `/models` must be read before `scope.json` can say which files are in scope, so `read_sources` calls `read()` twice. D11 and `file-fetch.md` describe one batch. | Either accept two (the second is the large one, so the measured saving holds) or list `**/*.py` from the tree and fetch both sets at once, re-fetching only if `scope.json` is unusual. | The timing row in phase4.md v1.1: one full check of pytest and of Django on Railway. |
| 4 | The promisor-pack check on a real remote. D11's "the clone holds exactly 2 promisor packs" is verified per `read()` call on a local bare repo only (`tests/connector/test_fetch.py`, #18); a whole check still makes two downloads (row 3). | Count `.git/objects/pack/*.promisor` after one read of a GitHub repository. | That count is 2 on a real remote. |
| 5 | `GIT_NO_LAZY_FETCH` needs git 2.44+. On older git (2.39 ships with macOS) the flag is ignored, so a failed batch silently crawls file by file instead of failing at once. | The container already pins `python:3.12-slim-trixie` (git 2.47). Nothing to do but know it: a local run is not proof of the fail-fast behaviour. | `git --version` in the image is 2.44 or later. |
| 6 | `FILE_TOO_LARGE` covers in-scope files only. A `/models` file over 1 MB is downloaded and parsed. | Apply the same size test to the four model files, or state that it is deliberate. | A 2 MB `structural.json` gives a stated code, not a slow read. |
| 6b | Size is judged on what arrived, not before the download, so an oversized file is still paid for once. `ls-tree -l` cannot be used to avoid it: in a blobless clone it reports sizes only by fetching every blob, which is the file-by-file crawl D11 exists to prevent (measured here: it tripled the suite's time and made clones of Team 16's fixture fail intermittently). phase4.md already flags "detecting a file over 1 MB before downloading it" as left out. | Leave as is, or ask GitHub's API for sizes before cloning. | One check of a repository holding a 50 MB file still finishes inside the deadline. |
| 6c | `git log --name-status -M` can lazily fetch blobs: exact renames are free, but an inexact rename needs content to score similarity. Unmeasured, and it runs with lazy fetching on, so it would be slow rather than fail. | Measure on a repository with renames; if it costs, use `-M100%` or fold the log into the one batch. | The timing row of phase4.md v1.1 holds on a repository with renames in range. |
| 7 | The local CLI path and the hosted path may not check the same things. Both now go through `read_sources` (#14), so size, UTF-8 and parse are judged alike, but no test compares them. REQ-07 wants them identical. | The reader comparison test of #18. | The same commit gives the same `drift` from the CLI and from `/analyze`. |
| 8 | `POST /system/generate` does not exist, and nor does `drifter init`. Nothing writes a repository's first `/models`, so only a repository that already has all four files can be checked at all. | The route and the CLI of phase4.md v1.1, over `propose_ownership`, `generate_structural` and the scope defaults. | T-33 compares three file texts byte for byte at L0. |
| 9 | The commit-log parser splits on tabs and newlines, so a path containing either is misread. | `git log -z`, or quote the paths. | A repository with a tab in a filename is judged correctly. |
| 10 | Placement, per D5 and D10: the core belongs in `Source/drifter/`, not `Source/orchestration.py`; `CommitRecord` belongs in `models/common.py`; the ownership checker is the core's, not the ownership model's. | Move them when the CLI lands, since it needs the same imports. | Nothing imports `orchestration` by that name any more. |
| 11 | **Closed 2026-11-01.** The ownership model disagreed with spec 3.2 in six places: the rule key, the window, vendored folders, which `models/` is skipped, lowercase emails, and how a rename is judged. All six are now the spec's, agreed by Muhammad. | Done. | `tests/ownership/test_ownership_model.py`, one test per row. |

## 2. What turns one check into a tracker

Nothing in this section exists yet, and none of it is in `docs/base/specifications.md`: the spec
describes one check of one commit, and the GitHub Action of Phase 5. The watch list in
`Source/Frontend/index.html` is the only thing that currently polls, and it is a browser
page, so it tracks nothing once the tab is closed.

| # | Missing | Fix | Check that closes it |
| --- | --- | --- | --- |
| 13 | A tracked repository. There is no server-side record of `{repository, branch, last-seen commit}`: it lives in one browser's `localStorage`, so the tracker is per-device and ends with the tab. | A store beside `runs.py`, and routes to add, list and remove a tracked repository. | A repository added on one machine is still tracked when seen from another. |
| 14 | Anything that polls without a person present. No scheduler, no worker, no cron. | A background task that sweeps the tracked repositories, or Phase 5's Action, which inverts the problem: the push tells us. | A push made while no page is open produces a saved verdict. |
| 15 | A rate-limit budget. Unauthenticated GitHub REST is 60 requests per hour per IP, one per repository per sweep, so five repositories at a 60 s interval exhaust it in about twelve minutes. | `ETag`/`If-None-Match` on the commits call (a 304 is free), and a token for the rest. Both are already flagged in phase4.md's "left out". | 20 repositories tracked at a 60 s interval stay inside the limit. |
| 16 | Webhooks, which are what "continuous" actually wants: a push event instead of a poll. | A public endpoint with signature verification and a dedupe key on the delivery id. | A push produces one verdict, and a redelivery produces none. |
| 17 | Durable verdicts. `DRIFTER_RUNS_DIR` has no volume mounted, so a redeploy wipes every run and `GET /system/analysis/{id}` 404s afterwards. | D6: the Railway volume behind `runs.py`. | T-14 and T-16 pass across a redeploy. |
| 18 | A way to ask what a repository's state is. No list route and no history, so "is this repository drifted?" can only be answered by the browser that asked. | A route over the tracked-repository store that returns the latest verdict per repository. | The question is answerable after a restart. |
| 19 | Delivery. A verdict reaches nobody: no comment, no check run, no message. Drift found while nobody is looking is lost. | Phase 5's Action writes the job summary and fails the check; a tracker would need its own channel. | A drifted push is visible without opening the console. |
| 20 | Backoff, overlap and fairness in the sweep. A failing repository retries at the same interval, `setInterval` can start a sweep while the last one runs, and the sweep awaits each analysis in turn, so one 80 s check blocks every other repository behind it. | A sweep that runs one at a time, skips what is already in flight, and backs off per repository. | 20 repositories, one of them slow, all get polled within one interval. |

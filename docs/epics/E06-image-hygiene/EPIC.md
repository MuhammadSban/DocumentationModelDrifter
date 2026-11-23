# E06: Image hygiene

Status: ratified · Owner: Kaan

W-row: W1-2 and W1-3 (build order step 2.1) in `docs/state/WORK-ITEMS.md` · Branch: `E06-image-hygiene`

## Goal

The image is built from a small context, in an order that reuses its layers, from exact versions. When this Epic closes: a `.dockerignore` keeps `.git`, every `.env*` file and every cache out of the build context, which is under 2 MB, with the size before and after written in the W1-2 row; the `Dockerfile` runs from least to most often changed and copies `Source/` last, so a change under `Source/` rebuilds only that layer, and the app still runs as `drifter` (10001); `requirements.txt` and `requirements-dev.txt` are locks that `uv pip compile` writes from `requirements.in` and `requirements-dev.in`, every package with an exact version and its hashes, and the image installs with `pip install --require-hashes`; and the `Dockerfile` and `.github/workflows/ci.yml` name the same exact Python, 3.12.16. The team needs it: the folder a local build reads holds 60 MB today, a sum of file sizes (fact line 22) that step 1 checks against Docker's own `transferring context` figure and step 5 replaces with the measured one; a stray `.env` or cache under `Source/` or `tests/` would enter the image, and two builds of the same commit can install different package versions, which spec §2.2 rules out ("each release pins its parser and Python version", `docs/base/specifications.md:134-135`). No route, answer, model or test of the tool changes.

## Relies on

Everything this Epic reads or changes, found by looking before the steps are written.

- Models: `docs/diagrams/data-flow.md` reads: its premise at line 121 says "the image and CI use 3.12" and cites `Dockerfile:3` and `.github/workflows/ci.yml:21`. The sentence stays true with 3.12.16, the `FROM` line stays on line 3, and no line of `ci.yml` moves, so step 5 leaves the file as it is (decided by the human, W1-2 row). No part, flow or run state changes, so no model changes and there is no `DESIGN.md`.
- Rulings: none in `docs/decisions/RULED/`, which holds only its README. The W1-2 row (`docs/state/WORK-ITEMS.md:143`) carries the calls marked "Decided by the human": one Epic for both rows, uv as the lock tool, Python 3.12.16, the ignore list, and the Railway check as work after the merge.
- Invariants: INV-1 (determinism) reads: an exact Python and exact packages serve it, and its row and grade are not edited. INV-2 and INV-3 are not touched: no file under `Source/` changes.
- Other sources: `docs/proposals/docker/docker.md` (R1, R2, "How to verify"); spec §2.2 (`docs/base/specifications.md:134-135`) and its Priority 3 risk (`:685-688`); `Source/Tester/unit_tests.py:15-20` (`GROUPS`); `CLAUDE.md`, Commands; the uv reference for `uv pip compile` (https://docs.astral.sh/uv/reference/cli/, https://docs.astral.sh/uv/pip/compile/).

### Facts this Epic rests on, checked at `ff79932`

- There is no `.dockerignore`. The folder a local `docker build .` sends holds 59.77 MB in 4003 files, summed file by file: the root `.mypy_cache` 21.47 MB, `Source/` 20.59 MB (of which `Source/.mypy_cache` is 19 MB), `.git` 14.59 MB, `docs/` 2.11 MB, `tests/` 0.93 MB.
- The list on the build order page (`.git`, `.env*`, `__pycache__`, `.mypy_cache`), matched at any depth, leaves 2.64 MB: over the 2 MB bound, because `docs/` is 2.11 MB of it. Leaving out `docs/` except the two paths the image copies leaves about 0.6 MB. What the four `COPY` lines need is 0.54 MB in 74 files.
- R1 of `docker.md` as written (`docker.md:38-47`) leaves 21.79 MB: its `.mypy_cache` and `.env*` lines match at the root only, so `Source/.mypy_cache` stays in.
- These sums are file sizes, not Docker's own figure: Docker Desktop was not running when this was drafted, so no `transferring context` line has been read yet. Step 1 reads it.
- `Dockerfile:3` is `FROM python:3.12-slim-trixie`. After the pip install it has four `COPY` lines, in this order: `Source/` (`:14`), `tests/` (`:16`), `docs/contract/` (`:17`), `docs/base/requirements-to-tests.md` (`:18`). The user is created after them (`:21-22`) and the `ENV` block follows (`:25-28`). The R2 sketch (`docker.md:51-64`) has three `COPY` lines: it predates the fourth.
- `requirements.txt` holds eight names with no versions (`fastapi`, `uvicorn`, `pydantic-settings`, `pyyaml`, `coverage`, `pytest`, `jsonschema`, `httpx`). `requirements-dev.txt` holds `ruff==0.17.6` and `import-linter==2.17`, with no hashes.
- CI installs both files in one command, `pip install -r requirements.txt -r requirements-dev.txt` (`.github/workflows/ci.yml:21`), on `python-version: "3.12"` (`:20`). pip checks hashes for the whole install as soon as one requirement carries a hash, so both files need hashes, and line 21 can stay as it is.
- `python:3.12.16-slim-trixie` is on Docker Hub (last pushed 2026-11-08) and is the newest 3.12 patch there with a `slim-trixie` tag; the manifest that `actions/setup-python` reads (`actions/python-versions`, `versions-manifest.json`) lists 3.12.16 for Linux x64 on 22.04, 24.04 and 26.04, and nothing newer in 3.12. Both were read on 2026-11-22.
- This checkout runs Python 3.13.13 on Windows; the image and CI run 3.12 on Linux. `uv --version` gives `uv 0.11.19`; `pip-compile` is not installed. In uv's universal mode the Python that runs the command is the lower bound unless `--python-version` names one, so the commands below pass `--python-version 3.12`.
- The `/tester` page runs only `tests/structural`, `behavioral`, `ownership` and `common` (`Source/Tester/unit_tests.py:15-20`), so `tests/image/` never runs inside the image, where the `Dockerfile` and `.dockerignore` are absent.
- `docs/contract/` names no Python or package version: `grep -rniE "python|version" docs/contract/` finds `config_version`, `tool_version`, `schema_version`, the contract's own "Version 2.5.0" and the words "Python code", and no version of Python or of a package.
- CI is green on `ff79932`: run 45074364848, `358 passed, 1 warning in 49.74s`. There is no `tests/build/` folder, and pytest has no configuration file, so plain `pytest` collects a new folder under `tests/`, unless its name is in pytest's default `norecursedirs`, which holds `build`. Found on step 3's push: CI run 45090643620 on `09b07d3` gave `358 passed`, and `pytest --collect-only -q` found 0 tests under `tests/build/`. So step 4 moves the file to `tests/image/` (decided by the human, 2026-11-22).

## Steps

One commit per step, made after the step's check passes. Four new tests in all, in one new file: steps 1 to 3 wrote it as `tests/build/test_image.py`, and step 4 moves it to `tests/image/test_image.py`, because plain `pytest` never enters a folder named `build` (fact line 33). Each is **written first**: it fails at the step's parent commit.

**Seam.** Every test reads the text of a committed file from the repository root (`Path(__file__).resolve().parents[2]`, as `tests/docs/test_diagrams.py:10` does). No test builds an image, starts Docker or uses the network.

**The lock changes package versions**, so the whole suite's result comes from CI on the pushed branch (Done line 13), not from a local run.

### Step 1/5: add `.dockerignore`

- Files: `.dockerignore` (new), `tests/build/test_image.py` (new)
- What: before the file exists, build once from a fresh copy of the checkout and read the size on the `transferring context` line; add the file; build again from a second fresh copy and read it again. A fresh copy each time, because a repeat build from the same folder may send only what changed. Keep both sizes, each with its command and its `transferring context` line, in a log outside the repository, `/tmp/e06-context-sizes.log` in Git Bash; this step writes them into no file of the repository, and step 5 does (decided by the human, W1-2 row). The file leaves out, at any depth: `.git`, `.env*`, `__pycache__`, `*.pyc`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.import_linter_cache`; and `.claude` and `docs/`, with `docs/contract/` and `docs/base/requirements-to-tests.md` let back in, since the image copies them. A root-only pattern does not match `Source/.mypy_cache`, so the cache and `.env*` lines start with `**/`. Test:
  - `test_dockerignore_keeps_out_git_env_and_caches`: the file exists and its lines leave out `.git`, `.env*`, `__pycache__` and `.mypy_cache` at any depth. At the parent the file does not exist.
- Check: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `1 passed` and has no `failed`
- Trailer: `Step: 1/5`

### Step 2/5: order the Dockerfile from least to most often changed

- Files: `Dockerfile`, `tests/build/test_image.py`
- What: the order becomes `FROM`, the apt install, the user and `/app/runs`, `WORKDIR`, `ENV`, `COPY requirements.txt`, the pip install, `COPY docs/contract/`, `COPY docs/base/requirements-to-tests.md`, `COPY tests/`, `COPY Source/`, `EXPOSE`, `CMD`. Only the order changes: every instruction keeps its text, the user is still `drifter` with uid and gid 10001, and `FROM` stays on line 3. Test:
  - `test_source_is_the_last_copy_in_the_dockerfile`: the last `COPY` line of the `Dockerfile` copies `Source/`. At the parent it is the first of four.
- Check: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `2 passed` and has no `failed`
- Trailer: `Step: 2/5`

### Step 3/5: lock both requirement files with hashes

- Files: `requirements.in` (new), `requirements-dev.in` (new), `requirements.txt`, `requirements-dev.txt`, `Dockerfile` (the pip line), `tests/build/test_image.py`
- What: `requirements.in` holds the eight names. `requirements-dev.in` holds `-c requirements.txt`, `ruff==0.17.6` and `import-linter==2.17`: the constraint keeps a package that both locks name at one version, because CI installs both files in one command. Each `.in` file starts with a comment that gives its command. The two locks are written by:
  - `uv pip compile requirements.in --universal --python-version 3.12 --generate-hashes -o requirements.txt`
  - `uv pip compile requirements-dev.in --universal --python-version 3.12 --generate-hashes -o requirements-dev.txt`

  `--universal` gives one file for every operating system, with markers; `--python-version 3.12` makes 3.12 the lower bound, so the lock serves the image (Linux, 3.12) and this checkout (Windows, 3.13). The Dockerfile's line becomes `RUN pip install --no-cache-dir --require-hashes -r requirements.txt`. `ci.yml` is not touched in this step. Before the commit, install both locks into a fresh virtualenv outside the repository (Done line 9's command). Test:
  - `test_every_requirement_has_an_exact_version_and_a_hash`: in `requirements.txt` and in `requirements-dev.txt`, every requirement is `name==version` and carries at least one `--hash=sha256:` value. At the parent no line of `requirements.txt` has a version.
- Check: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `3 passed` and has no `failed`
- Trailer: `Step: 3/5`

### Step 4/5: name one exact Python in the Dockerfile and in CI

- Files: `Dockerfile` (line 3), `.github/workflows/ci.yml` (lines 17 and 20, a protected file: the edit stops for the human's approval), `tests/build/test_image.py` moved to `tests/image/test_image.py`
- What: `FROM python:3.12.16-slim-trixie`, and `python-version: "3.12.16"` with its comment naming the same version. No line is added or removed in either file. `git mv tests/build/test_image.py tests/image/test_image.py`, so CI collects the file. Test:
  - `test_dockerfile_and_ci_name_the_same_exact_python_patch`: the `FROM` line and the `python-version` value each name a three-part version, and the two are equal. At the parent both say `3.12`.
- Check: `python -m pytest tests/image/test_image.py -q` → the summary line starts with `4 passed` and has no `failed`
- Trailer: `Step: 4/5`

### Step 5/5: the docs

- Files: `docs/proposals/docker/docker.md`, `docs/state/WORK-ITEMS.md` (the W1-2 and W1-3 rows and Next action), and `docs/README.md` (lines 109 and 111), `CLAUDE.md` (Commands, a protected file) or the root `README.md` only where a line there went stale
- What: the two sizes of step 1's log go into the W1-2 row, after the words "Measured context:", written once in that row and nowhere else in the file, and into `docker.md`. If the log is gone, measure again as step 1 did, the size before from a fresh copy with `.dockerignore` deleted. `docker.md` says R1 and R2 are applied by this Epic, gives the measured sizes in place of "about 14 MB" and "about 15 MB", shows the ignore file and the order as built, with the fourth `COPY`, and its "Why" section names the paths the `Dockerfile` copies today. The W1-2 and W1-3 rows name this Epic, say what was built and keep the Railway check as work after the merge; Next action names E06 as built and waiting for the audit. `docs/README.md:109` says the proposals are "not built", which stops being true of `docker.md`'s R1 and R2, so it says those two are built; read `docs/README.md:111`, the Commands section of `CLAUDE.md` and the root `README.md` and change a line only if steps 1 to 4 made it untrue (R2); the two `pip install -r` commands of `CLAUDE.md` still work on a lock. `docs/diagrams/data-flow.md` is not edited. No new test, so the check reads the two docs (decided by the human, W1-2 row).
- Check: `LC_ALL=C.UTF-8 grep -Pzo -e 'not\s+yet\s+applied|about\s+14\s+MB|about\s+15\s+MB' docs/proposals/docker/docker.md; grep -c "Measured context:" docs/state/WORK-ITEMS.md` → the first grep prints nothing and exits 1, and the second prints `1`. Without a UTF-8 locale, `grep -P` exits 2 with an error on stderr and prints nothing on stdout, so the exit status is part of the result. At `ff79932`, and at this step's parent, the first prints all three phrases and the second prints `0`. That the second grep can count in this file: `grep -c "Decided by the human, 2026-11-22" docs/state/WORK-ITEMS.md` prints `7` at this draft's commit. The checker also reads the row: it gives a size before and a size after.
- Trailer: `Step: 5/5`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Lines 5, 7, 8, 10, 11 and 17 need Docker Desktop running, and lines 5 to 11 and 17 need Git Bash; lines 5, 9, 10 and 11 use the network to pull the base image and the packages. Each makes its own temporary folder outside the checkout and changes nothing in the repository. None was run when this Epic was drafted: Docker Desktop was not running.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`. CI runs on the pushed HEAD of `E06-image-hygiene`; each push is on the human's word.
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → prints nothing: this Epic changes no behavior, and spec §2.2 already asks for the pin
3. No open row for this Epic: `git grep -n "E06" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The build context is under 2 MB: `T=$(mktemp -d) && cp -r . "$T/c" && mkdir -p "$T/c/Source/drifter/__pycache__" "$T/c/Source/.mypy_cache" && touch "$T/c/Source/.env.e06" "$T/c/Source/drifter/__pycache__/e06.pyc" "$T/c/Source/.mypy_cache/e06"; docker image rm -f e06-image; docker build --progress=plain -t e06-image "$T/c" 2>&1 | grep "transferring context"; echo "exit=${PIPESTATUS[0]}"` → the last `transferring context` line names a size under 2 MB (a figure in kB, or in MB below 2), and the last line is `exit=0`, the build's own exit status. The copy carries `.git` and whatever caches the checkout has, and the command plants an env file, a `__pycache__` file and a `.mypy_cache` file under `Source/`, so the ignore file is what keeps them out. The old `e06-image` tag is removed first (an error from that removal on a machine with no such tag is expected), so lines 7 and 8 can only run on this build.
6. Both sizes are recorded: `git grep -c "Measured context:" -- docs/state/WORK-ITEMS.md` → `docs/state/WORK-ITEMS.md:1`, and that row gives a size before and a size after
7. The image holds no cache and no env file: after line 5, `MSYS_NO_PATHCONV=1 docker run --rm e06-image find /app \( -name __pycache__ -o -name ".env*" -o -name .mypy_cache \)` → prints nothing, though line 5 planted one file of each kind under `Source/`
8. The image still has its user and still answers: after line 5, `MSYS_NO_PATHCONV=1 docker run --rm e06-image id drifter` → `uid=10001(drifter) gid=10001(drifter) groups=10001(drifter)`; then `docker run -d --rm --name e06 -p 18000:8000 e06-image && sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:18000/system/health; docker stop e06` → the container id on the first line, then `200` followed by `e06` (`200e06`: `curl -w` prints no newline before `docker stop` prints the name). Port 18000 on the host, so a service already on port 8000 cannot fail the line
9. A fresh virtualenv on Windows installs both locks: `T=$(mktemp -d) && python -m venv "$T/v" && "$T/v/Scripts/python" -m pip install --disable-pip-version-check --require-hashes -r requirements.txt -r requirements-dev.txt` → the last line starts with `Successfully installed`
10. A change in `Source/` reuses every layer above it: `T=$(mktemp -d) && git archive HEAD | tar -x -C "$T" && docker build -q "$T" && echo "# e06" >> "$T/Source/drifter/__init__.py" && docker build --progress=plain "$T" 2>&1 | grep -E "^#[0-9]+ (\[|CACHED)"` → every step from the apt install to `COPY tests/ tests/` is followed by a `CACHED` line, and `COPY Source/ Source/` is not
11. A wrong hash fails the build: `T=$(mktemp -d) && git archive HEAD | tar -x -C "$T" && sed -i "s/sha256:[0-9a-f]\{8\}/sha256:00000000/g" "$T/requirements.txt" && docker build --progress=plain "$T" 2>&1 | grep -c "DO NOT MATCH THE HASHES"` → a number above 0. The change is made in the temporary copy; `git status --short` in the checkout prints nothing afterwards.
12. One exact Python in both files: `grep -n "3\.12\.[0-9]" Dockerfile .github/workflows/ci.yml` → the `FROM python:3.12.16-slim-trixie` line of the `Dockerfile` and the `python-version: "3.12.16"` line of `ci.yml`, with its comment; no line names another patch
13. The whole suite passes in CI: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --log | grep -E "[0-9]+ passed"` → the line holds `362 passed` and no `failed` (358 at `ff79932`, plus 4). `361 passed, 1 skipped` also counts: `tests/connector/test_golden.py` skips when the runner cannot reach the fixture repository (INV-1).
14. The new tests pass: `python -m pytest tests/image/test_image.py -q` → the summary line starts with `4 passed` and has no `failed`
15. The old claims are gone from the proposal: `LC_ALL=C.UTF-8 grep -Pzo -e 'not\s+yet\s+applied|about\s+14\s+MB|about\s+15\s+MB' docs/proposals/docker/docker.md` → prints nothing and exits 1. Without a UTF-8 locale, `grep -P` exits 2 with an error on stderr and prints nothing on stdout, so the exit status is part of the result. The grep reads the file as one record (`-z`) and `\s+` matches a line break. Run on the file at `ff79932` it prints all three phrases.
16. The image installs with hash checking on: `grep -c "^RUN .*--require-hashes" Dockerfile` → `1`. Only `RUN` lines count, so a comment that names the flag cannot change the figure.
17. The home folder is still the user's: after line 5, `MSYS_NO_PATHCONV=1 docker run --rm e06-image find /home/drifter ! -user drifter` → prints nothing: every file and folder under it, and the folder itself, belong to `drifter`. Step 2 moves `ENV HOME=/home/drifter` above the pip install, which runs as root.

"Railway still reports `storage: volume`" is not a Done line, because it needs the deploy. It is work after the merge, kept in the W1-3 row, as E05 did with its live checks.

## Out of scope

Each is a conscious choice, not an oversight.

- Pinning the base image by digest. The tag `3.12.16-slim-trixie` can be pushed again with new Debian packages; only a digest fixes them.
- Pinning the apt packages (`git`, `ca-certificates`).
- A job that re-locks on a schedule. A lock is refreshed by hand, with the two commands of step 3 and `--upgrade`.
- A CI step that builds the image. The build is checked by the Done lines, once, not on every push.
- Locking what `pip install -e .` installs for the CLI: `pyproject.toml` still names `jsonschema` with no version.
- A pip cache mount, a multi-stage build and leaving `tests/` out of the image (`docker.md`, "Left out, flagged").

## Open questions

The human decided the calls in the W1-2 row (`docs/state/WORK-ITEMS.md:143`). Three points rest on tools that were not run when this was drafted; each is checked by a step or a Done line, and none is the human's call.

- Does `docs/` followed by the two lines that let `docs/contract/` and `docs/base/requirements-to-tests.md` back in keep both paths in the context? Checked by the build of Done line 5: it fails at a `COPY` line if not. Review: no file, model or ruling answers it; it is Docker's behavior, not the human's call, and the build settles it, but only once Done line 5 shows whether the build succeeded, which today it does not (see Review, first finding; `Dockerfile:17-18`). Review at fd9dea1: settled by Done line 5 as revised, whose `exit=${PIPESTATUS[0]}` is the build's own status and must read `exit=0`; a build that cannot find `docs/contract/` or `docs/base/requirements-to-tests.md` stops at its `COPY` and prints a non-zero exit (`EPIC.md:101`; `Dockerfile:17-18`).
- Does pip accept two locks in one install when both name the same package at the same version? Checked in step 3 and by Done line 9, and by CI (Done line 1). Review: no file, model or ruling answers it; it is pip's behavior, not the human's call. Step 3's local install runs on Windows and 3.13 only, so the first Linux 3.12 answer is CI on step 3's push (`.github/workflows/ci.yml:20-21`).
- Does a first build from a fresh folder print the whole context's size on its `transferring context` line? Checked in step 1, where the size before must come out near the 59.77 MB summed from the files; if Docker sends only the paths the `COPY` lines name, the builder writes that in the log, and step 5 writes it beside the two sizes in the W1-2 row. Review: no file, model or ruling answers it; it is BuildKit's behavior, not the human's call. If BuildKit sends only the `COPY` paths, the size before is near 21 MB (`Source/` with its 19.86 MB `.mypy_cache`, `tests/`, `docs/contract/`), not 59.77 MB; the step already says what to write then.

## Review

Revised after the verdict below, after step 5, on the human's finding of 2026-11-22: without a UTF-8 locale `grep -P` exits 2, with an error on stderr and nothing on stdout, so step 5's check and Done line 15 could pass falsely. Both now prefix the `grep -Pzo` with `LC_ALL=C.UTF-8` and expect it to exit 1. The next reviewer writes its verdict above this paragraph.

RATIFY · design-reviewer at 069c1b8 · 2026-11-22 (reported, not written by the reviewer, as the human accepted for b6668ff)

- Every line that must name `tests/image/` does: step 4's Files, What and Check, Done line 14 and fact line 31. Keeping `tests/build/` in the checks of steps 1 to 3 is right, since a path named on pytest's command line is not filtered by `norecursedirs`.
- pytest 9.2.0's default `norecursedirs` is `*.egg`, `.*`, `_darcs`, `build`, `CVS`, `dist`, `node_modules`, `venv`, `{arch}`, and `image` matches none of them. No other `test_image*.py` exists, and `parents[2]` is still the root after the move. 358 + 4 = 362 is reachable.

Revised after the verdict below, between steps 3 and 4, on the human's call of 2026-11-22: pytest's default `norecursedirs` holds `build`, so CI never collected `tests/build/` (run 45090643620 on `09b07d3`: `358 passed`). Step 4 moves the test file to `tests/image/`; fact lines 31 and 33, the Steps intro, step 4's Files, What and Check, and Done line 14 say so. The checks of steps 1 to 3 keep `tests/build/`, the path at their commits. The next reviewer writes its verdict above this paragraph.

RATIFY · design-reviewer at b6668ff · 2026-11-22 (accepted by the human from the reviewer's report: the reviewer writes no verdict on an Epic whose Status is not `draft`, so it changed nothing and reported)

- The seven findings are closed. Done line 7 and line 8 pass `bash -n`. Line 8's port matches the container's default 8000 (`Dockerfile:32`). On a line with two hashes, line 11's `sed` changes both. Line 16 prints `0` today, and step 3 makes it `1`. Line 17's `find` covers the whole tree, and runs as root, since the `Dockerfile` has no `USER` line. Step 5 names `docs/README.md:109` and `:111`. The Goal's 60 MB cites fact line 22.
- Not blocking: the Goal says step 5 "replaces" the 60 MB, but step 5 writes the measured figure into the W1-2 row and `docker.md` and does not edit this file. Read "replaces" as "writes".
- The filled-copy check prints nothing. The commit touches only this file and carries `Step: plan`.

Revised after the verdict below, before any code, on the human's instruction of 2026-11-22: seven of its non-blocking findings are closed. Done line 7 writes the escaped parentheses into its command; Done line 8 publishes on port 18000 and names its whole output; Done line 11's `sed` has the `g` flag; Done line 16 counts only `RUN` lines; Done line 17 checks the whole tree under `/home/drifter`; step 5 also reads `docs/README.md:109`; the Goal says its 60 MB is a sum of file sizes that step 1 measures. Fact line 32 and the `data-flow.md` citation are left as noted. The next reviewer writes its verdict above this paragraph.

RATIFY · design-reviewer at fd9dea1 · 2026-11-22

The four blocking findings of the review at f85bdcc are resolved:

- Done line 5 removes the old tag, then echoes `${PIPESTATUS[0]}` right after the `docker build | grep` pipeline, so the echoed status is the build's own exit status. A failed build prints a non-zero exit, and lines 7, 8 and 17 then find no `e06-image`. (`EPIC.md:101`)
- Line 5 plants `Source/.env.e06`, `Source/drifter/__pycache__/e06.pyc` and `Source/.mypy_cache/e06` in the copy. `COPY Source/` would carry all three into the image if the ignore file failed, so line 7 now checks something real. Today `find . -name ".env*"` prints nothing in the checkout. (`EPIC.md:101`, `:103`; `Dockerfile:14`)
- Done line 9 passes `--disable-pip-version-check`, and step 3 runs the same command. pip's warning about scripts not on PATH prints before `Successfully installed`, and pip does not print it for a venv's own `Scripts`. (`EPIC.md:66`, `:105`)
- Step 1 no longer edits the W1-2 row, and step 5's check reads the two docs. It uses grep only, with no pytest, as the human decided. I proved that each grep can find its target. At fd9dea1 and at ff79932, `grep -Pzo` prints all three phrases of `docker.md`. `grep -c "Measured context:"` prints `0`, and `grep -c "Decided by the human, 2026-11-22"` prints `7`, so `-c` counts lines in this file. (`EPIC.md:46-48`, `:83`; `docs/state/WORK-ITEMS.md:143`)

Not blocking (worth fixing during the build or in step 5):

- The Goal says "a local build sends 60 MB today". Docker has not confirmed that figure. BuildKit's Dockerfile frontend usually sends only the paths that the `COPY` lines name. If it does, the size before is about 21 MB (`Source/` with its 19.86 MB `.mypy_cache`, plus `tests/`), and `.git` is never sent. Fact line 25 and open question 3 already allow for this. In step 5, write the measured figure in place of the "60 MB" wording, and do not keep it beside that wording. (`EPIC.md:9`, `:25`, `:134`)
- Done line 7 does not run as written: bash rejects the bare `(` with a syntax error. Write the escapes into the command, for example `find /app \( -name __pycache__ -o -name ".env*" -o -name .mypy_cache \)`. The error would show, so the line cannot pass falsely. (`EPIC.md:103`)
- Done line 8 prints the container id from `docker run -d` first. The rest reads `200e06`, because `curl -w` ends without a newline before `docker stop` prints the name. The expected output could say so. The line also assumes nothing else is listening on port 8000. (`EPIC.md:104`)
- Done line 17 checks only the owner of `/home/drifter` itself. If root's pip run made a folder under it, that folder would not show. `find /home/drifter ! -user drifter` → prints nothing would cover the whole tree. (`EPIC.md:113`)
- Done line 11's `sed` has no `g` flag, so it changes the first hash on each line only. It changes every hash because `uv pip compile --generate-hashes` writes one `--hash` per line. Adding `g` would keep the human's "every hash" call true whatever the layout. (`EPIC.md:107`; `docs/state/WORK-ITEMS.md:143`)
- Done line 16 expects `1`. A step 3 comment above the pip line that names `--require-hashes` would make it `2`. Keep the flag out of the comment, or count only `RUN` lines. (`EPIC.md:116`)
- Step 5 points at `docs/README.md:111`. Line 109, the heading text of that section, says the proposals there are "not agreed and not built", which stops being true of `docker.md`'s R1 and R2. (`docs/README.md:109`)
- Fact line 32 is still not exhaustive. The grep also finds "Python sources", "Python facts", "Python with ast" and "Version 1". The conclusion holds: `grep -rniE "python ?[0-9]|[a-z]==[0-9]|3\.1[0-9]" docs/contract/` prints nothing. (`docs/contract/spec-v1.1.md:217`)
- Next action still lists, as left over from E02, "the Python version on INV-1", a call of the human's. E06 pins 3.12.16 in the image and in CI and does not edit INV-1, so the two do not conflict. The human may want to settle that call alongside this Epic. (`docs/state/WORK-ITEMS.md:14`; `docs/invariants/INVARIANTS.md:16`)
- `data-flow.md:121` cites `ci.yml:21`, but the version is on `:20`. This predates E06, and the human chose to leave the file unedited (W1-2 row). I agree that its sentence stays true. (`docs/diagrams/data-flow.md:121`)

Claims checked and holding at fd9dea1:

- `git diff --stat ff79932 fd9dea1` touches only this file and `WORK-ITEMS.md`.
- Run 45074364848 is a push run on `ff79932`. It printed `Python 3.12.16` and `358 passed, 1 warning in 49.74s`. With four tests in one new file, the step checks expect 1, 2, 3, 4 and 4 passed, so the total is 358 + 4 = 362. Each test fails at its parent: there is no `.dockerignore`, the last `COPY` copies the requirements map, `requirements.txt` has no versions, and both files say `3.12`.
- No `tests/build/` exists, no other `test_image*` exists, there is no `__init__.py` under `tests/` and there is no pytest configuration. Plain `pytest` collects the new file in CI.
- `GROUPS` is at `unit_tests.py:15-20` and has no `build`. No test or tester code walks `tests/` for files.
- `Dockerfile:3`, `:14`, `:16-18`, `:21-22` and `:25-28` say what the Epic claims. So do `ci.yml:17`, `:20` and `:21`, both requirement files, and `docker.md:3`, `:15`, `:38-47`, `:51-64` and `:72`.
- `test_diagrams.py:10` uses `parents[2]`. Spec `:134-135` and `:685-688` say what the Epic quotes.
- Recomputed sizes: 60.1 MB in 4039 files. The root `.mypy_cache` is 21.47 MB, `Source/` 20.59 MB (its `.mypy_cache` 19.86 MB), `.git` 14.89 MB, `docs/` 2.14 MB and `tests/` 0.93 MB. Step 1's list leaves 0.56 MB.
- The only tracked dot-files that an ignore pattern could touch are `.github/workflows/ci.yml`, `.gitignore` and `tests/ownership/.gitkeep`. The ignore list matches none of them.
- Docker Hub shows `3.12.16-slim-trixie` pushed 2026-11-08, the newest 3.12 `slim-trixie`. The `actions/python-versions` manifest lists 3.12.16 as the newest 3.12, for Linux x64 on 22.04, 24.04 and 26.04.
- With uv 0.11.19, `uv help pip compile` lists `--universal`, `--generate-hashes`, `-c` and `-o`. It says universal mode treats `--python-version` as the lower bound.
- This machine runs Python 3.13.13, its ensurepip bundles pip 26.0.1, and `pip-compile` is not installed.
- `gh run list` has `--commit`, and Done lines 1 and 13 work on a known SHA. `.github/workflows/` holds only `ci.yml`.
- `ci.yml` and `CLAUDE.md` are on the ask list (`.claude/settings.json:9-11`). `RULED/` holds only its README. No row of `OPEN-DECISIONS.md` names E06. The hook accepts the `Step: i/N` trailers (`.claude/hooks/step-trailer.py:13`).
- The filled-copy check prints nothing for this file, and it does find 16 placeholder lines in `docs/templates/EPIC.md`.
- Authority order: nothing above level 7 conflicts. `pdftotext` of the course PDF finds "Team Tester Interface" but no Docker, Python version or lock. The contract names no Python or package version. Spec §2.2 asks for the pin. No model in `docs/diagrams/` changes, so no `DESIGN.md` is needed.

Open questions: each of the three ends with a sourced answer, and none needs a row in `docs/decisions/OPEN-DECISIONS.md`.

Revised after the verdict below, on the human's answers of 2026-11-22 (W1-2 row): Done line 5 shows the build's exit status, removes the old tag and plants an env file and two cache files; Done line 9 passes `--disable-pip-version-check`; Done line 13 accepts one skip; Done lines 16 and 17 are new; fact line 32 is exact; step 1 no longer edits the W1-2 row, and step 5 writes the sizes and has a grep-only check. The next reviewer writes its verdict above this paragraph.

REVISE · design-reviewer at f85bdcc · 2026-11-22

Must change for RATIFY:

- Done line 5 can pass while the build fails. Its output goes through `grep "transferring context"`, and the context is sent before any `COPY` runs, so a build that stops at `COPY docs/contract/` (open question 1) still prints a size under 2 MB. Lines 7 and 8 then run on whatever `e06-image` tag exists, which can be a stale one from an earlier run. Change line 5 so it removes the tag first (`docker image rm -f e06-image`) and its expected output also shows that the build succeeded, for example `echo "exit=${PIPESTATUS[0]}"` → `exit=0`. (Done line 5; open question 1; `Dockerfile:17-18`)
- Done line 7 can pass when the ignore file is broken. No `.env*` file exists anywhere in the checkout (`find . -name ".env*"` prints nothing), and a fresh clone holds no `__pycache__` or `.mypy_cache`. So "prints nothing" proves nothing about the `.env*` line, and proves nothing about the cache lines unless the copy holds the caches. In line 5, plant them in the temporary copy before the build, for example `Source/.env.e06`, `tests/.env`, `Source/drifter/__pycache__/x.pyc` and `Source/.mypy_cache/x`. Line 7 then checks something real. (Done lines 5 and 7; Goal)
- Done line 9's expected output, "the last line starts with `Successfully installed`", fails even when the install succeeds whenever pip prints its `[notice] A new release of pip is available` lines afterwards. A fresh venv on this checkout's Python 3.13.13 gets the pip that ensurepip bundles, 26.0.1 (`python -c "import ensurepip; print(ensurepip.version())"`), so the notice can follow. Add `--disable-pip-version-check` to the command, or expect "a line starts with `Successfully installed` and no line starts with `ERROR`". Step 3 runs the same command. (Done line 9; step 3)
- Step 5's check (`4 passed`) passes before step 5 is done: none of the four tests reads a doc. Make its check Done line 15's command (→ prints nothing), together with Done line 6's. In the same way, step 1's check does not show that its third file, the W1-2 row, gained "Measured context:" with both sizes; add Done line 6's command to step 1's check. (Steps 1 and 5; Done lines 6 and 15)

Not blocking:

- Done line 13 expects `362 passed`. INV-1 says `tests/connector/test_golden.py` skips when the runner cannot reach GitHub; the summary then reads `361 passed, 1 skipped`, and the line fails with nothing broken. Consider "passed plus skipped is 362, and no `failed`". The count itself holds: run 45074364848 on `ff79932` printed `358 passed, 1 warning in 49.74s`, `git diff --stat ff79932 f85bdcc` touches only this file and `WORK-ITEMS.md`, and the four tests make 1, 2, 3, 4, 4 across steps 1 to 5. (`docs/invariants/INVARIANTS.md`, INV-1)
- No line checks that the `Dockerfile`'s pip line carries `--require-hashes`, which the Goal promises. Done line 11 fails without the flag too, because one hash turns on pip's hash mode. A `grep -c -- "--require-hashes" Dockerfile` → `1` line would close the gap. (Goal; Done line 11)
- `docs/diagrams/data-flow.md:121` cites `.github/workflows/ci.yml:21`, which is the `pip install` line. The Python version is on `:20`. This was already wrong at `ff79932` and is not this Epic's doing; the human chose to leave the file as it is (`docs/state/WORK-ITEMS.md:143`). It is worth a later small change. (`data-flow.md:121`; `ci.yml:20-21`)
- Fact line 32 is inexact: `grep -rniE "python|version" docs/contract/` also finds `tool_version`, `schema_version`, "Version 2.5.0" and "Python code". The conclusion holds: the contract names no Python version and no package version. (`docs/contract/pod-contract.md:3`, `:109`)
- Step 2 moves `ENV HOME=/home/drifter` above the pip install, which runs as root. With `--no-cache-dir`, pip is not expected to write there, but no Done line checks that `/home/drifter` is still drifter's. The order is the one `docker.md:51-64` proposed. (Step 2; `Dockerfile:25-28`)

Claims checked and holding:

- `Dockerfile:3`, `:14`, `:16-18`, `:21-22` and `:25-28`; `ci.yml:17`, `:20` and `:21`; both requirement files as described.
- `docker.md:38-47` (R1, root-only `.mypy_cache` and `.env*`) and `:51-64` (R2, three `COPY` lines). The Done line 15 grep prints all three phrases on the file today.
- `unit_tests.py:15-20` (`GROUPS`, with no `build`) and `test_diagrams.py:10` (`parents[2]`).
- No `tests/build/`, no other `test_image.py`, no pytest configuration (`pyproject.toml` has none); `tests/conftest.py` only puts `Source/` on the import path. Nothing under `Source/`, `tests/` or `scripts/` reads `requirements*.txt` or the `Dockerfile`.
- Sizes recomputed at `f85bdcc`: 59.84 MB in 4012 files, with `.mypy_cache` 21.47, `Source/` 20.59 (its `.mypy_cache` 19.86), `.git` 14.64, `docs/` 2.13 and `tests/` 0.93; 0.56 MB after the step 1 list, and 0.54 MB for what the `COPY` lines need.
- Docker Hub has `3.12.16-slim-trixie`, pushed 2026-11-08, and it is the newest 3.12 `slim-trixie`. `versions-manifest.json` lists 3.12.16 as the newest 3.12, for Linux x64 on 22.04, 24.04 and 26.04.
- uv 0.11.19: `uv help pip compile` lists `--universal`, `--generate-hashes` and `-c`, and says `--python-version` "Defines the minimum Python version that must be supported".
- `ci.yml` and `CLAUDE.md` are on the ask list in `.claude/settings.json:9-11`. `RULED/` holds only its README. Spec `:134-135` and `:685-688` say what the Epic quotes. INV-1 to INV-3 are as described.
- The filled-copy check prints nothing, and it does find placeholders in `docs/templates/EPIC.md`.
- Authority order: nothing above level 7 conflicts. The course PDF's text names no Docker, Python version or lock; `pdftotext` was checked against "Team Tester Interface", which it does find. The contract names no versions. Spec §2.2 asks for the pin. No model changes, so no `DESIGN.md` is needed.
- Step order is safe for CI on each push: CI builds no image (`ci.yml:21-27`), so steps 1, 2 and 5 cannot turn it red, and step 3's lock is CI's first Linux install, caught by Done line 1. Railway deploys only green commits (R3).

Open questions: none needs a row in `docs/decisions/OPEN-DECISIONS.md`. All three ask how Docker, pip or BuildKit behave, and each is settled by a named check, not by the human. Question 1 is settled only once the first finding is fixed.

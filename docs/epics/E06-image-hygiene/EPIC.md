# E06: Image hygiene

Status: draft · Owner: Kaan

W-row: W1-2 and W1-3 (build order step 2.1) in `docs/state/WORK-ITEMS.md` · Branch: `E06-image-hygiene`

## Goal

The image is built from a small context, in an order that reuses its layers, from exact versions. When this Epic closes: a `.dockerignore` keeps `.git`, every `.env*` file and every cache out of the build context, which is under 2 MB, with the size before and after written in the W1-2 row; the `Dockerfile` runs from least to most often changed and copies `Source/` last, so a change under `Source/` rebuilds only that layer, and the app still runs as `drifter` (10001); `requirements.txt` and `requirements-dev.txt` are locks that `uv pip compile` writes from `requirements.in` and `requirements-dev.in`, every package with an exact version and its hashes, and the image installs with `pip install --require-hashes`; and the `Dockerfile` and `.github/workflows/ci.yml` name the same exact Python, 3.12.16. The team needs it: a local build sends 60 MB today, a stray `.env` or cache under `Source/` or `tests/` would enter the image, and two builds of the same commit can install different package versions, which spec §2.2 rules out ("each release pins its parser and Python version", `docs/base/specifications.md:134-135`). No route, answer, model or test of the tool changes.

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
- The `/tester` page runs only `tests/structural`, `behavioral`, `ownership` and `common` (`Source/Tester/unit_tests.py:15-20`), so `tests/build/` never runs inside the image, where the `Dockerfile` and `.dockerignore` are absent.
- `docs/contract/` names no Python or package version: `grep -rniE "python|version" docs/contract/` finds only `config_version`, the contract's and the model's own versions.
- CI is green on `ff79932`: run 45074364848, `358 passed, 1 warning in 49.74s`. There is no `tests/build/` folder, and pytest has no configuration file, so plain `pytest` collects a new folder under `tests/`.

## Steps

One commit per step, made after the step's check passes. Four new tests in all, in one new file, `tests/build/test_image.py`. Each is **written first**: it fails at the step's parent commit.

**Seam.** Every test reads the text of a committed file from the repository root (`Path(__file__).resolve().parents[2]`, as `tests/docs/test_diagrams.py:10` does). No test builds an image, starts Docker or uses the network.

**The lock changes package versions**, so the whole suite's result comes from CI on the pushed branch (Done line 13), not from a local run.

### Step 1/5: add `.dockerignore`

- Files: `.dockerignore` (new), `tests/build/test_image.py` (new), `docs/state/WORK-ITEMS.md` (the W1-2 row)
- What: before the file exists, build once from a fresh copy of the checkout and read the size on the `transferring context` line; add the file; build again from a second fresh copy and read it again. A fresh copy each time, because a repeat build from the same folder may send only what changed. Write both sizes in the W1-2 row after the words "Measured context:". The file leaves out, at any depth: `.git`, `.env*`, `__pycache__`, `*.pyc`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.import_linter_cache`; and `.claude` and `docs/`, with `docs/contract/` and `docs/base/requirements-to-tests.md` let back in, since the image copies them. A root-only pattern does not match `Source/.mypy_cache`, so the cache and `.env*` lines start with `**/`. Test:
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

- Files: `Dockerfile` (line 3), `.github/workflows/ci.yml` (lines 17 and 20, a protected file: the edit stops for the human's approval), `tests/build/test_image.py`
- What: `FROM python:3.12.16-slim-trixie`, and `python-version: "3.12.16"` with its comment naming the same version. No line is added or removed in either file. Test:
  - `test_dockerfile_and_ci_name_the_same_exact_python_patch`: the `FROM` line and the `python-version` value each name a three-part version, and the two are equal. At the parent both say `3.12`.
- Check: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `4 passed` and has no `failed`
- Trailer: `Step: 4/5`

### Step 5/5: the docs

- Files: `docs/proposals/docker/docker.md`, `docs/state/WORK-ITEMS.md`, and `docs/README.md` (line 111), `CLAUDE.md` (Commands, a protected file) or the root `README.md` only where a line there went stale
- What: `docker.md` says R1 and R2 are applied by this Epic, gives the measured sizes in place of "about 14 MB" and "about 15 MB", shows the ignore file and the order as built, with the fourth `COPY`, and its "Why" section names the paths the `Dockerfile` copies today. The W1-2 and W1-3 rows name this Epic, say what was built and keep the Railway check as work after the merge; Next action names E06 as built and waiting for the audit. Read `docs/README.md:111`, the Commands section of `CLAUDE.md` and the root `README.md` and change a line only if steps 1 to 4 made it untrue (R2); the two `pip install -r` commands of `CLAUDE.md` still work on a lock. `docs/diagrams/data-flow.md` is not edited. No new test.
- Check: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `4 passed` and has no `failed`
- Trailer: `Step: 5/5`

## Done criteria

Each line is a command and the output that means done. The auditor re-runs every line at HEAD.

Lines 5 to 10 need Docker Desktop running and Git Bash; lines 5 to 8 use the network to pull the base image and the packages. Each makes its own temporary folder outside the checkout and changes nothing in the repository. None was run when this Epic was drafted: Docker Desktop was not running.

Baseline, the same for every Epic:

1. CI green: `gh run list --commit $(git rev-parse HEAD) --limit 1 --json conclusion --jq ".[0].conclusion"` → `success`. CI runs on the pushed HEAD of `E06-image-hygiene`; each push is on the human's word.
2. Spec lines updated: `git diff --stat main...HEAD -- docs/base/specifications.md` → prints nothing: this Epic changes no behavior, and spec §2.2 already asks for the pin
3. No open row for this Epic: `git grep -n "E06" -- docs/decisions/OPEN-DECISIONS.md` → prints nothing
4. The human accepts. The one line that is the human's word and not a command: it comes after lines 1 to 3 and the Epic's own lines pass.

This Epic's own:

5. The build context is under 2 MB: `T=$(mktemp -d) && cp -r . "$T/c" && docker build --progress=plain -t e06-image "$T/c" 2>&1 | grep "transferring context"` → the last line printed names a size under 2 MB (a figure in kB, or in MB below 2). The copy carries the checkout's caches and `.git`, so the ignore file is what keeps them out.
6. Both sizes are recorded: `git grep -c "Measured context:" -- docs/state/WORK-ITEMS.md` → `docs/state/WORK-ITEMS.md:1`, and that row gives a size before and a size after
7. The image holds no cache and no env file: after line 5, `MSYS_NO_PATHCONV=1 docker run --rm e06-image find /app ( -name __pycache__ -o -name ".env*" -o -name .mypy_cache )`, with each parenthesis escaped by a backslash → prints nothing
8. The image still has its user and still answers: after line 5, `MSYS_NO_PATHCONV=1 docker run --rm e06-image id drifter` → `uid=10001(drifter) gid=10001(drifter) groups=10001(drifter)`; then `docker run -d --rm --name e06 -p 8000:8000 e06-image && sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/system/health; docker stop e06` → `200` before the container's name
9. A fresh virtualenv on Windows installs both locks: `T=$(mktemp -d) && python -m venv "$T/v" && "$T/v/Scripts/python" -m pip install --require-hashes -r requirements.txt -r requirements-dev.txt` → the last line starts with `Successfully installed`
10. A change in `Source/` reuses every layer above it: `T=$(mktemp -d) && git archive HEAD | tar -x -C "$T" && docker build -q "$T" && echo "# e06" >> "$T/Source/drifter/__init__.py" && docker build --progress=plain "$T" 2>&1 | grep -E "^#[0-9]+ (\[|CACHED)"` → every step from the apt install to `COPY tests/ tests/` is followed by a `CACHED` line, and `COPY Source/ Source/` is not
11. A wrong hash fails the build: `T=$(mktemp -d) && git archive HEAD | tar -x -C "$T" && sed -i "s/sha256:[0-9a-f]\{8\}/sha256:00000000/" "$T/requirements.txt" && docker build --progress=plain "$T" 2>&1 | grep -c "DO NOT MATCH THE HASHES"` → a number above 0. The change is made in the temporary copy; `git status --short` in the checkout prints nothing afterwards.
12. One exact Python in both files: `grep -n "3\.12\.[0-9]" Dockerfile .github/workflows/ci.yml` → the `FROM python:3.12.16-slim-trixie` line of the `Dockerfile` and the `python-version: "3.12.16"` line of `ci.yml`, with its comment; no line names another patch
13. The whole suite passes in CI: `gh run view $(gh run list --commit $(git rev-parse HEAD) --limit 1 --json databaseId --jq ".[0].databaseId") --log | grep -E "[0-9]+ passed"` → the line holds `362 passed` and no `failed` (358 at `ff79932`, plus 4)
14. The new tests pass: `python -m pytest tests/build/test_image.py -q` → the summary line starts with `4 passed` and has no `failed`
15. The old claims are gone from the proposal: `grep -Pzo -e 'not\s+yet\s+applied|about\s+14\s+MB|about\s+15\s+MB' docs/proposals/docker/docker.md` → prints nothing. The grep reads the file as one record (`-z`) and `\s+` matches a line break. Run on the file at `ff79932` it prints all three phrases.

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

- Does `docs/` followed by the two lines that let `docs/contract/` and `docs/base/requirements-to-tests.md` back in keep both paths in the context? Checked by the build of Done line 5: it fails at a `COPY` line if not.
- Does pip accept two locks in one install when both name the same package at the same version? Checked in step 3 and by Done line 9, and by CI (Done line 1).
- Does a first build from a fresh folder print the whole context's size on its `transferring context` line? Checked in step 1, where the size before must come out near the 59.77 MB summed from the files; if Docker sends only the paths the `COPY` lines name, the builder writes that beside the two sizes in the W1-2 row.

## Review

Not reviewed yet. The design reviewer writes RATIFY or REVISE here, with the reviewer, the date and the findings, each citing its source.

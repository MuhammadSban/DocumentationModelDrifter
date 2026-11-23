# Docker build: a .dockerignore and better layer caching

Questions: should the repo add a `.dockerignore` and reorder the `Dockerfile` so builds reuse more cached layers? And should the backend, frontend and database run in separate containers, now or in Phase 5? Written 2026-11-04. R1 and R2 are applied by Epic E06 (2026-11-22), which also locks the packages with hashes and names Python 3.12.16; the container split below is still a proposal.

## Short answer

Yes, both. They are small, standard practice, and change nothing about how the app runs. They still matter in Phase 5, but only for the hosted service: the Phase 5 gate installs drifter with pip inside each repository's GitHub Actions run (spec §6.2) and never uses this image.

## Why the change is needed

### 1. There was no `.dockerignore`

The `Dockerfile` copies only named paths (`requirements.txt`, `docs/contract/`, `docs/base/requirements-to-tests.md`, `tests/`, `Source/`), so most of the repo never reaches the image. Railway builds from a git checkout, so files ignored by git never reach its build either. The gaps were:

- **Local builds sent caches.** BuildKit sends only the paths the `COPY` lines name, so `.git` and the root `.mypy_cache` stayed out, but `Source/.mypy_cache` (about 19 MB) went in. Measured on 2026-11-22, each from a fresh copy of the checkout: the `transferring context` line read 21.64 MB before the ignore file and 541.74 kB after.
- **Stray files could enter the image on a local build.** `__pycache__` and `.pytest_cache` inside `Source/` or `tests/` were copied in. A `.env` or key file dropped into `Source/` would have been too.
- **A future `COPY . .` would copy secrets and `.git`.** The ignore file guards against that change.

### 2. One layer was rebuilt on every code change

Docker reuses a cached layer only while every step above it is unchanged. Before E06, the user-creation step came after the code was copied:

```
COPY Source/ ...        <- changes on almost every commit
COPY tests/ ...
COPY docs/contract/ ...
RUN groupadd ... useradd ... mkdir /app/runs   <- never changes, but rebuilt every time
```

So every commit reran `groupadd`, `useradd` and `mkdir`. The cost is small (a second or two), but the order is wrong, and the image gets a new layer it did not need.

What is already right: `requirements.txt` is copied and installed before the code, so the slow `pip install` layer is reused unless dependencies change.

## Recommendations

### R1. Add `.dockerignore` at the repo root

As built by E06. Patterns match at any depth (`**/`), since a root-only `.mypy_cache` line misses `Source/.mypy_cache`; `docs` is left out except the two paths the image copies.

```
# keeps git, env files and caches out of the build context, at any depth
**/.git
**/.env*
**/__pycache__
**/*.pyc
**/.mypy_cache
**/.pytest_cache
**/.ruff_cache
**/.import_linter_cache

# keeps agent files and the docs out, except the two paths the image copies
.claude
docs
!docs/contract
!docs/base/requirements-to-tests.md
```

### R2. Order the `Dockerfile` from least to most often changed

As built by E06:

```
FROM python:3.12.16-slim-trixie
RUN apt-get ... git ca-certificates ...            # changes almost never
RUN groupadd ... useradd ... mkdir -p /app/runs    # moved up: never changes
WORKDIR /app
ENV DRIFTER_RUNS_DIR=/app/runs ...                 # moved up with it
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt # changes when dependencies change
COPY docs/contract/ docs/contract/                 # changes on a contract version bump
COPY docs/base/requirements-to-tests.md docs/base/requirements-to-tests.md
COPY tests/ tests/
COPY Source/ Source/                               # changes most often, so last
EXPOSE 8000
CMD [...]                                          # unchanged
```

Only the order changes. The steps and the final image contents stay the same, and the app still runs as user `drifter` (10001).

### How to verify

1. `docker build -t drifter .` twice. The second build shows every step as `CACHED`.
2. Change one line in `Source/` and rebuild. Every step above `COPY Source/` shows `CACHED`, including `useradd` and `pip install`.
3. The `transferring context` line in the build output is under 2 MB. E06 measured it from a fresh copy: 21.64 MB before the ignore file, 541.74 kB after.
4. `docker run -p 8000:8000 drifter`, then `GET /system/health` answers, and `docker run drifter ls -a /app` shows no `__pycache__` or `.env`.
5. Deploy to Railway and confirm `/system/health` still reports `storage: volume`.

## Separate containers for backend, frontend and database?

Splitting a system into containers is good practice when its parts scale differently, deploy on different schedules or need different runtimes. The split alone does not make a system scalable. A part scales only when it holds no state of its own, so copies of it can run side by side. So the useful question for each part is: would it gain anything on its own?

### What the project has today

One container, one Railway service, one FastAPI app (`Source/GitHub_Connector/api.py`):

| Part | What it really is | Where it runs |
| --- | --- | --- |
| Backend | `/system/*` routes, the check, the generators | the app |
| Frontend | `index.html` and `app.css`, served as files (`api.py:63`, `api.py:163`), plus the model viewer, which Python renders (`Frontend/model_viewer.py`) | the app |
| Tester | `/tester` routes (`Source/Tester/`) | the app, same process |
| "Database" | none; one JSON file per result, written atomically by `runs.py` to the Railway volume at `/data` | the volume |

### Part by part

| Split | Verdict now | Why |
| --- | --- | --- |
| **Frontend into its own container** | **No** | It is two static files. A second container (for example nginx) would add a second URL, CORS settings and one more deploy to serve two files (about 930 lines of HTML and CSS). The model viewer needs the Python model code, so it would stay in the backend anyway. |
| **A database container** (for example Postgres) | **No** | Results are written once and read back by id, which is what files do well. A database container on Railway also keeps its data on one volume, so it removes no limit; it only adds a service, a schema and backups. |
| **Tester into its own service** | **Not yet, the first to split** | Its load is different: a run can take 600 s and makes many outbound calls, while it shares the machine with incoming checks. `phase4.md` Q7 already says to split it if a tester run slows our own checks. |
| **Several backend copies** | **No** | Blocked by state, not by packaging: results live on one volume, the check limit (2) and the single test session live in one process's memory. |

### What would make the backend scale

If the hosted service ever needs more than one copy, the order is:

1. **Move results to a storage bucket**, not a database container. `runs.py` is the only file that changes (`phase4.md:110`).
2. **Move the shared limits out of the process** (the 2-check cap and the one active test session), so all copies see the same counts.
3. **Then** run more copies of the same image.

A frontend or database container does none of these.

### Docker Compose

Compose describes several containers in one `compose.yaml` and starts them together with `docker compose up`. It is the usual companion to a split, but it plays a narrower role here:

- **It is for running locally, not for deploying.** Railway deploys each service from its own settings (the dashboard), not from a Compose file. So Compose would not replace any Railway setup; it would sit beside it.
- **With one container it adds nothing.** `docker build` and `docker run` already do the whole job.
- **It earns its place at the first split.** Once the tester is a second service, a Compose file would start both locally with one command, share one network so the tester can call the system by name, mount a local folder as the runs volume, and set each service's env vars. That makes "point our tester at our system" reproducible on any laptop and in CI.

A sketch for that moment (same image, two services):

```yaml
services:
  system:
    build: .
    ports: ["8000:8000"]
    volumes: ["runs:/app/runs"]
  tester:
    build: .
    command: ["uvicorn", "--app-dir", "Source", "Tester.app:app", "--host", "0.0.0.0", "--port", "8001"]
    ports: ["8001:8001"]
    environment:
      SYSTEM_URL: http://system:8000
volumes:
  runs:
```

**Why a named volume (`runs`) and not a folder on the laptop (`./.runs`).** The app runs as user `drifter` (10001). A new named volume copies the ownership of `/app/runs` from the image, so `drifter` can write to it at once. A bind-mounted folder keeps the host's owner, so on Linux `drifter` cannot write to it without a `chown`. The named volume also survives `docker compose down` (only `down -v` deletes it), just as the Railway volume survives a redeploy. To read the saved results, use `docker compose exec system ls /app/runs`.

**No `VOLUME` line in the `Dockerfile`.** Keep the volume in Compose and in Railway, where it is named and managed. A `VOLUME` instruction in the image creates an unnamed volume on every plain `docker run`, which piles up and hides where results went. Check Railway's docs before adding one, since Railway mounts its own volume instead.

`Tester.app` and `SYSTEM_URL` do not exist yet; the tester is a router inside the system app today, so the split itself would create them.

**Recommendation:** add Compose together with the tester split, not before. If a storage bucket replaces the volume later, an S3-compatible container such as MinIO can stand in for it locally in the same file.

### Phase 5

Phase 5 adds no hosted load. The gate is `drifter check` inside each repository's own GitHub Actions run, installed with pip, and its answers are saved as workflow artifacts (spec §6.2). Every repository brings its own machine, so this plan scales with users without any container change. The hosted service stays what it is today: the course tester's target and the console.

### Recommendation

Keep one container for Phase 4 and Phase 5. Revisit only on one of these signals:

- **The tester slows our checks** (shown by the Django timing, #22): split the tester into a second service from the same image, and add the Compose file above at the same time.
- **The hosted service needs zero-downtime deploys or more than 2 checks at once:** follow the three steps above.
- **The frontend grows into its own app** (a build step, a framework, its own release cycle): then give it its own service or a static host.

## Left out, flagged (each needs a conscious decision)

- **A pip cache mount** (`RUN --mount=type=cache,...`). It speeds up rebuilds after a dependency change. Railway needs a service-specific cache id, so check Railway's docs before adding it.
- **A multi-stage build.** It gives a smaller image only if build tools are needed at install time. None are needed today.
- **Leaving `tests/` out of the image.** The `/tester` page runs them, so they must stay.

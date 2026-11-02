# serves the /system app, the console at / and the tester at /tester, with git installed and no credentials baked in

FROM python:3.12-slim-trixie

# installs git, the connector's only tool, and nothing else
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Source/ Source/
# ships the tests the /tester page runs and the golden answers the pod tests compare with
COPY tests/ tests/
COPY docs/contract/ docs/contract/

# creates the unprivileged user the app runs as; the container starts as root only to hand it the
# Railway volume, which mounts root-owned, then drops to it before serving (D6)
RUN useradd --create-home --uid 10001 drifter && mkdir -p /app/runs && chown drifter /app/runs

# keeps run files where the drifter user can write (a volume replaces it on Railway), points HOME at
# drifter's for git after setpriv, tool_version comes from RAILWAY_GIT_COMMIT_SHA at runtime
ENV DRIFTER_RUNS_DIR=/app/runs \
    HOME=/home/drifter \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# listens on the PORT the host sets (Railway does), 8000 when run locally
EXPOSE 8000
CMD ["sh", "-c", "if [ -n \"$RAILWAY_VOLUME_MOUNT_PATH\" ]; then chown drifter \"$RAILWAY_VOLUME_MOUNT_PATH\"; fi && exec setpriv --reuid=10001 --regid=10001 --init-groups uvicorn --app-dir Source GitHub_Connector.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

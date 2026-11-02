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

# creates the unprivileged user and group the app runs as, both 10001
RUN groupadd --gid 10001 drifter && useradd --create-home --uid 10001 --gid 10001 drifter \
    && mkdir -p /app/runs && chown drifter:drifter /app/runs

# keeps run files where drifter can write (a Railway volume replaces it), HOME is drifter's for git
ENV DRIFTER_RUNS_DIR=/app/runs \
    HOME=/home/drifter \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# starts as root to hand drifter the root-mounted volume, then drops to drifter (D6); listens on PORT
EXPOSE 8000
CMD ["sh", "-c", "if [ -n \"$RAILWAY_VOLUME_MOUNT_PATH\" ]; then chown drifter:drifter \"$RAILWAY_VOLUME_MOUNT_PATH\"; fi && exec setpriv --reuid=drifter --regid=drifter --init-groups uvicorn --app-dir Source GitHub_Connector.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

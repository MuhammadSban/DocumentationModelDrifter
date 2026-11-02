# builds the model fixture repository (spec §4.2) from nothing, reproducibly: fixed authors, committers and
# dates, LF only and no git config from the machine, so every build gives the same commit SHAs; tags each
# commit by its case label. Usage: python scripts/model_fixture.py FOLDER

import os
import subprocess
import sys
from pathlib import Path

OWNER = ("Fixture Owner", "owner@fixture.example")

STORE = '''"""Keeps orders in memory."""


class Store:
    def __init__(self):
        self.items = {}

    def get(self, key):
        return self.items.get(key)


class OrderStore(Store):
    def put(self, order):
        self.items[order.order_id] = order
'''

AUDIT = '''"""Records what happened to an order."""


def record(event):
    return event
'''

ORDERS = '''"""An order and its lifecycle."""

import audit
from store import OrderStore


class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.status = "open"

    def advance(self):
        if self.status == "open":
            self.status = "paid"
'''

# lists the commits oldest first: tag, message, author, date and the files it writes
COMMITS = [
    ("L-pre", "Python code, no /models yet", OWNER, "2026-01-01T00:00:00+00:00",
     {"src/audit.py": AUDIT, "src/orders.py": ORDERS, "src/store.py": STORE}),
]


def _git(folder: Path, *args: str, env: dict | None = None) -> None:
    # runs git with no system or global config, so nothing on the machine changes the SHAs
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True,
                   env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, **(env or {})})


def build(folder: Path) -> None:
    # creates the repository in an empty or missing folder and makes every commit with its tag
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise SystemExit(f"{folder} is not empty")
    _git(folder, "init", "-q", "-b", "main")
    _git(folder, "config", "core.autocrlf", "false")
    for tag, message, (name, email), date, files in COMMITS:
        for path, text in files.items():
            (folder / path).parent.mkdir(parents=True, exist_ok=True)
            (folder / path).write_bytes(text.encode("utf-8"))
        _git(folder, "add", "-A")
        _git(folder, "commit", "-q", "-m", message, env={
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": date})
        _git(folder, "tag", tag)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/model_fixture.py FOLDER")
    build(Path(sys.argv[1]))

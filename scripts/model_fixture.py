# builds the model fixture repository (spec §4.2) from nothing, reproducibly: fixed authors, committers and
# dates, LF only and no git config from the machine, so every build gives the same commit SHAs; tags each
# case's commit by its label. /models is written by this repository's drifter init and drifter update.
# Usage: python scripts/model_fixture.py FOLDER

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

SOURCE = Path(__file__).resolve().parents[1] / "Source"

OWNER = ("Fixture Owner", "owner@fixture.example")
VISITOR = ("Fixture Visitor", "visitor@fixture.example")

# keeps git, and drifter's own git calls, from reading any config on the machine
CLEAN = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}

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


def _replace(old: str, new: str) -> Callable[[str], str]:
    # edits a file's current text, stopping the build unless old is there exactly once
    def edit(text: str) -> str:
        if text.count(old) != 1:
            raise SystemExit(f"fixture edit expected {old!r} exactly once")
        return text.replace(old, new)
    return edit


def _drop_inherits(text: str) -> str:
    # removes the one inherits edge from structural.json by hand, keeping drifter's layout (spec §3.2)
    model = json.loads(text)
    model["edges"] = [e for e in model["edges"] if e["id"] != "inherits:store:OrderStore->store:Store"]
    return json.dumps(model, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


# lists the commits oldest first: tag (None for a commit that only accepts the last case's drift), message,
# author, the files it writes (a text, or an edit of the current text) and the drifter command it runs:
# init before the commit, or update on the commit, folded into it
COMMITS = [
    ("L-pre", "Python code, no /models yet", OWNER,
     {"src/audit.py": AUDIT, "src/orders.py": ORDERS, "src/store.py": STORE}, None),
    ("L0", "Commit /models as drifter init writes it", OWNER, {}, "init"),
    ("L1", "Edit comments and whitespace only", OWNER,
     {"src/audit.py": _replace("def record(event):\n", "\ndef record(event):  # keeps the event as given\n"),
      "src/orders.py": _replace("    def advance(self):\n",
                                "    # moves the order one step on\n    def advance(self):\n")},
     None),
    ("L2", "Add one function", OWNER,
     {"src/audit.py": _replace("    return event\n", "    return event\n\n\ndef forget(event):\n    return None\n")},
     None),
    (None, "Accept L2's drift with drifter update", OWNER, {}, "update"),
    ("L3", "Remove one import", OWNER, {"src/orders.py": _replace("import audit\n", "")}, None),
    (None, "Accept L3's drift with drifter update", OWNER, {}, "update"),
    ("L4", "Add a state and a transition into it", OWNER,
     {"src/orders.py": _replace('            self.status = "paid"\n',
                                '            self.status = "paid"\n'
                                '        elif self.status == "paid":\n'
                                '            self.status = "shipped"\n')},
     None),
    ("L5", "Add a function and update /models in the same commit", OWNER,
     {"src/store.py": _replace("        self.items[order.order_id] = order\n",
                               "        self.items[order.order_id] = order\n\n\n"
                               "def new_store():\n"
                               "    return OrderStore()\n")},
     "update"),
    ("L6", "Edit a comment in a file another author owns", VISITOR,
     {"src/orders.py": _replace("    # moves the order one step on\n", "    # moves the order one step on, never back\n")},
     None),
    ("L7", "Remove an inherits edge from structural.json by hand", OWNER,
     {"models/structural.json": _drop_inherits}, None),
]


def _git(folder: Path, *args: str, env: dict | None = None) -> None:
    # runs git with no system or global config, so nothing on the machine changes the SHAs
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True,
                   env={**os.environ, **CLEAN, **(env or {})})


def _drifter(folder: Path, command: str) -> None:
    # runs this repository's drifter on the fixture's HEAD, which writes the fixture's /models
    subprocess.run([sys.executable, "-m", "drifter.cli", command, "--repo", str(folder)], check=True,
                   capture_output=True, env={**os.environ, **CLEAN, "PYTHONPATH": str(SOURCE)})


def build(folder: Path) -> None:
    # creates the repository in an empty or missing folder and makes every commit, one day apart
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise SystemExit(f"{folder} is not empty")
    _git(folder, "init", "-q", "-b", "main")
    _git(folder, "config", "core.autocrlf", "false")
    for day, (tag, message, (name, email), files, command) in enumerate(COMMITS, start=1):
        date = f"2026-01-{day:02d}T00:00:00+00:00"
        env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date,
               "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": date}
        for path, content in files.items():
            target = folder / path
            text = content if isinstance(content, str) else content(target.read_bytes().decode("utf-8"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        if command == "init":
            _drifter(folder, "init")
        _git(folder, "add", "-A")
        _git(folder, "commit", "-q", "--allow-empty", "-m", message, env=env)
        if command == "update":
            # folds drifter update into the commit it regenerates, since update reads a commit, not the folder
            _drifter(folder, "update")
            _git(folder, "add", "-A")
            _git(folder, "commit", "-q", "--amend", "-m", message, env=env)
        if tag:
            _git(folder, "tag", tag)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/model_fixture.py FOLDER")
    build(Path(sys.argv[1]))

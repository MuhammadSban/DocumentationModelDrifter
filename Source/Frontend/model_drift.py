# the website's rudimentary drift check: regenerates the structural model at two commits and says
# whether the newer one is exactly the older one. One question, one boolean.
#
# This is NOT the contract checker. Source/drifter/check.py compares a regenerated model with the
# committed /models element by element, reports ADDED / REMOVED / MODIFIED, judges ownership and
# raises the spec's four no-verdict codes. Nothing here does any of that: it compares two
# generated models whole, so any change anywhere reads as drift.

from __future__ import annotations

import json
from dataclasses import dataclass

from drifter.check import DEFAULT_SCOPE, MODEL_FILES, in_scope
from models.common import ParseFailed
from models.structural_model import generate_structural

# names the committed model a snapshot reads for its scope; absent, DEFAULT_SCOPE applies
SCOPE_FILE = "models/scope.json"


class SnapshotFailed(Exception):
    # reports a commit whose model could not be generated, naming the commit and the reason
    pass


@dataclass(frozen=True)
class Verdict:
    # what the page shows beside a model: which commits were compared, and for each model whether
    # the newer generated one differs. A model absent from changed was not checked at all, which
    # the page says rather than drawing it as being in step.
    head: str
    base: str | None
    changed: dict[str, bool]
    note: str | None = None


def snapshot(reader, commit: str) -> dict:
    # regenerates the structural model from the in-scope files at one commit, as the generator
    # would have written it into /models at that commit
    tree = reader.tree_at(commit)
    paths = in_scope(sorted(tree), _scope(reader, tree, commit))
    if not paths:
        raise SnapshotFailed(f"{commit[:7]} has no files in scope")
    raw = reader.read(paths, commit)
    try:
        return generate_structural({path: raw[path].decode("utf-8") for path in paths})
    except (ParseFailed, UnicodeDecodeError) as exc:
        raise SnapshotFailed(f"{commit[:7]} could not be parsed: {exc}") from None


def drifted(previous: dict, current: dict) -> bool:
    # the naive check the website shows: drift is the generated model not being exactly the one
    # the commit before it generated. No element diff, so a reordered field counts as drift.
    return previous != current


def committed(reader, commit: str) -> dict[str, dict]:
    # reads whichever of the four model files the commit carries, so the page can show a
    # committed ownership model beside the generated structural one; an unparseable file is left out
    tree = reader.tree_at(commit)
    present = [f"models/{name}" for name in MODEL_FILES if f"models/{name}" in tree]
    if not present:
        return {}
    raw = reader.read(present, commit)
    found = {}
    for path in present:
        try:
            found[path.removeprefix("models/")] = json.loads(raw[path].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return found


def _scope(reader, tree: dict[str, str], commit: str) -> dict:
    # takes the commit's own scope.json where it has one, so a repository that declares its scope
    # is read the way its own generator reads it
    if SCOPE_FILE not in tree:
        return DEFAULT_SCOPE
    try:
        scope = json.loads(reader.read([SCOPE_FILE], commit)[SCOPE_FILE].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return DEFAULT_SCOPE
    return scope if isinstance(scope, dict) else DEFAULT_SCOPE

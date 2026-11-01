# runs one drifter check at a commit and returns the spec's four-field answer (REQ-02):
# regenerate the structural and behavioral models from the code and compare them with the
# committed /models by element id, and judge every non-merge commit between base and head
# against the ownership rules. Read-only: nothing here writes to the repository.
#
#   drifter check               # check HEAD of the checkout in the current folder
#   drifter check SHA --base X  # check a commit against a given base
#
# Ownership is checked, never regenerated and diffed: history grows with the push being checked
# (spec 3.2). `drifter init` proposes the first ownership.json, a person corrects it, and from
# then on each push is judged against it.
#
# The behavioral generator is not built: until it registers in GENERATORS (v1.2), behavioral
# reports no differences.

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from models.common import ParseFailed, glob, parse_files
from models.ownership_model import CommitRecord, PathTouch, check_ownership
from models.structural_model import generate_structural

# names the four files /models must hold, as the contract's ModelsFixture requires
MODEL_FILES = ("behavioral.json", "ownership.json", "scope.json", "structural.json")

# defaults drifter init writes into scope.json (spec 3.2)
DEFAULT_SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}

# caps one in-scope file, over this there is no verdict (spec 5.2)
MAX_FILE_BYTES = 1024 * 1024

# reads history for the ownership check, NUL-separated so no path comes back quoted
LOG_ARGS = ("log", "-z", "--topo-order", "--name-status", "-M", "--format=%x01%H%x1f%ae%x1f%P")

# names the regular file modes a check reads; symlinks and submodules are left out
REGULAR = {"100644", "100755"}

# maps git's status letters to the ownership model's change types
LETTERS = {"A": "ADDED", "M": "MODIFIED", "D": "DELETED", "R": "RENAMED", "C": "COPIED", "T": "TYPE_CHANGED"}


class DriftError(Exception):
    # carries one drift_error code from the contract, which the route reports without a verdict
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def body(self) -> dict:
        # renders the contract's DriftError object
        return {"code": self.code, "message": self.message}


class Reader(Protocol):
    # reads one commit of a repository; LocalReader reads a checkout, the connector's Comparison a
    # fresh blobless clone, so every entry point gathers its Sources the same way
    head: str

    def tree(self) -> dict[str, str]:
        # maps every regular file at the commit to its blob
        ...

    def read(self, paths: list[str]) -> dict[str, bytes]:
        # returns each path's bytes at the commit
        ...

    def log(self) -> str:
        # returns the commits base..head as one LOG_ARGS log, newest first
        ...


@dataclass(frozen=True)
class Sources:
    # everything one check reads at one commit, gathered before any model is built
    files: dict[str, str]  # in-scope path -> text at the commit
    models: dict[str, dict]  # the committed /models, parsed
    commits: list[CommitRecord]  # the commits between base and head, newest first


# ------------------------------------------------------------------------------- the pure check


def answer(sources: Sources) -> dict:
    # returns the contract's DriftAnswer: aligned is true only when all three lists are empty
    structural = model_differences("structural", sources)
    behavioral = model_differences("behavioral", sources)
    ownership = check_ownership(sources.models["ownership.json"], sources.commits)
    return {
        "aligned": not (structural or behavioral or ownership),
        "behavioral": behavioral,
        "ownership": ownership,
        "structural": structural,
    }


# maps each regenerated model to its generator; behavioral joins at v1.2 (model-seam.md)
GENERATORS: dict[str, Callable[[dict[str, str]], dict]] = {"structural": generate_structural}


def model_differences(name: str, sources: Sources) -> list[dict]:
    # regenerates one model and sets it against the committed one by element id; a model with no
    # registered generator reports no differences
    generate = GENERATORS.get(name)
    if generate is None:
        return []
    try:
        fresh = generate(sources.files)
    except ParseFailed as exc:
        raise DriftError(exc.code, str(exc)) from None
    return differences(fresh, sources.models[f"{name}.json"])


def differences(fresh: dict, committed: dict) -> list[dict]:
    # reports from the code's side: ADDED is in the code but not the model, REMOVED is in the
    # model but not the code, MODIFIED is one id in both with different attributes
    fresh_by_id = _elements(fresh)
    committed_by_id = _elements(committed)
    found = []
    for element_id in sorted(set(fresh_by_id) | set(committed_by_id)):
        in_code, in_model = fresh_by_id.get(element_id), committed_by_id.get(element_id)
        if in_model is None:
            found.append(_difference("ADDED", in_code))
        elif in_code is None:
            found.append(_difference("REMOVED", in_model))
        elif in_code != in_model:
            found.append(_difference("MODIFIED", in_code))
    return found


def _elements(model: dict) -> dict[str, dict]:
    # indexes every element of every top-level list by id; a value that is not a list, such as
    # schema_version, is not an element (model-seam.md)
    return {e["id"]: e for value in model.values() if isinstance(value, list) for e in value}


def _difference(change: str, element: dict) -> dict:
    # renders the contract's ModelDifference, whose keys are fixed
    return {"change": change, "file": element["file"], "id": element["id"], "kind": element["kind"]}


def in_scope(paths: list[str], scope: dict) -> list[str]:
    # keeps the paths scope.json includes and does not exclude, matched with the one glob that
    # mapping-v1.1.yaml also uses, so a pattern means the same everywhere (phase4.md Q3)
    include = scope.get("include", DEFAULT_SCOPE["include"])
    exclude = scope.get("exclude", DEFAULT_SCOPE["exclude"])
    kept = [p for p in paths if any(_matches(p, pattern) for pattern in include)]
    return sorted(p for p in kept if not any(_matches(p, pattern) for pattern in exclude))


def _matches(path: str, pattern: str) -> bool:
    # matches one scope pattern against a repo-relative path
    return glob(pattern).match(path) is not None


# ------------------------------------------------------------- reading one commit, locally or not


def local_sources(repo: Path, head: str = "HEAD", base: str | None = None) -> Sources:
    # reads one commit of a local checkout
    return read_sources(LocalReader(repo, head, base))


def read_sources(reader: Reader) -> Sources:
    # reads the three things one check needs: the committed /models at the commit, the in-scope
    # files, and the commits the ownership check judges. The three no-verdict codes are raised
    # here, before any generator runs (phase4.md Q2).
    tree = reader.tree()
    missing = [name for name in MODEL_FILES if f"models/{name}" not in tree]
    if missing:
        raise DriftError("MODELS_NOT_FOUND", f"models/{missing[0]} is missing at {reader.head}")
    committed = reader.read([f"models/{name}" for name in MODEL_FILES])
    models = {name: _model(f"models/{name}", committed[f"models/{name}"]) for name in MODEL_FILES}
    paths = in_scope(sorted(tree), models["scope.json"])
    raw = reader.read(paths)
    # judges size, then encoding, then syntax, each before any generator runs (phase4.md Q2).
    # Size is judged on what arrived: a blobless clone cannot report it any earlier.
    big = [path for path in sorted(raw) if len(raw[path]) > MAX_FILE_BYTES]
    if big:
        raise DriftError("FILE_TOO_LARGE", f"{big[0]} is {len(raw[big[0]])} bytes, over 1 MB")
    files = _decode(raw)
    # parses every in-scope file once before any generator runs, so a generator may assume each
    # one parses and one bad file fails the whole check (spec 3.2)
    try:
        parse_files(files)
    except ParseFailed as exc:
        raise DriftError(exc.code, str(exc)) from None
    return Sources(files=files, models=models, commits=_parse_history(reader.log()))


class LocalReader:
    # reads one commit of a local checkout with git. The base defaults to the head's first parent
    # and is excluded; for a root commit only the head itself is judged (spec 3.1).
    def __init__(self, repo: Path, head: str = "HEAD", base: str | None = None) -> None:
        self.repo = repo
        self.head = _git(repo, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
        if base is None:
            parents = _git(repo, "rev-parse", f"{self.head}^@").split()
            base = parents[0] if parents else None
        self.base = base
        self._tree: dict[str, str] | None = None

    def tree(self) -> dict[str, str]:
        # lists the whole tree once, whichever folder of the checkout the command runs in
        if self._tree is None:
            self._tree = {}
            for entry in _git(self.repo, "ls-tree", "-r", "-z", "--full-tree", self.head).split("\0"):
                meta, _, path = entry.partition("\t")
                if meta:
                    mode, _, sha = meta.split()
                    if mode in REGULAR:
                        self._tree[path] = sha
        return self._tree

    def read(self, paths: list[str]) -> dict[str, bytes]:
        # reads each path's blob at the head, one git call per file
        tree = self.tree()
        return {path: _run(self.repo, "cat-file", "blob", tree[path]) for path in paths}

    def log(self) -> str:
        # reads the commits base..head, or the head alone for a root commit
        span = f"{self.base}..{self.head}" if self.base else self.head
        return _git(self.repo, *LOG_ARGS, span)


def _decode(raw: dict[str, bytes]) -> dict[str, str]:
    # turns each in-scope file's bytes into text; one that is not UTF-8 ends the check (spec 5.2)
    files = {}
    for path, data in raw.items():
        try:
            files[path] = data.decode("utf-8")
        except UnicodeDecodeError:
            raise DriftError("PARSE_FAILED", f"{path} is not UTF-8 text") from None
    return files


def _model(path: str, raw: bytes | str) -> dict:
    # parses one committed model file, a file that is not readable JSON ending the check
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DriftError("INVALID_MODELS", f"{path} is not valid JSON: {exc}") from None


def _parse_history(raw: str) -> list[CommitRecord]:
    # reads the commit records out of one LOG_ARGS log: \x01 opens a header, then each change
    # is a status and one path, or two for a rename or copy
    tokens = raw.split("\x00")
    records, header, touches, i = [], None, [], 0
    while i < len(tokens):
        token = tokens[i].lstrip("\n")
        i += 1
        if token.startswith("\x01"):
            if header:
                records.append(_record(header, touches))
            header, touches = token[1:], []
        elif token[:1] in ("R", "C"):
            old, new = tokens[i], tokens[i + 1]
            i += 2
            touches.append(PathTouch(new, "RENAMED", old) if token[0] == "R" else PathTouch(new, "COPIED"))
        elif token:
            touches.append(PathTouch(tokens[i], LETTERS[token[0]]))
            i += 1
    if header:
        records.append(_record(header, touches))
    return records


def _record(header: str, touches: list[PathTouch]) -> CommitRecord:
    # builds one commit record from its sha, author email and parents
    sha, email, parent_list = header.split("\x1f")
    return CommitRecord(sha, email.lower(), tuple(parent_list.split()), tuple(touches))


def _git(repo: Path, *args: str) -> str:
    # runs one git command in repo and returns its text, decoded as git hands paths over
    return _run(repo, *args).decode("utf-8", "surrogateescape")


def _run(repo: Path, *args: str) -> bytes:
    # runs one git command in repo and returns its bytes
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout

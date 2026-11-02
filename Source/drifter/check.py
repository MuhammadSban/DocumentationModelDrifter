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

from models.common import ParseFailed, glob, parse_files, write_model
from models.ownership_model import CommitRecord, PathTouch, check_ownership, propose_ownership
from models.structural_model import generate_structural

# names the four files /models must hold, as the contract's ModelsFixture requires
MODEL_FILES = ("behavioral.json", "ownership.json", "scope.json", "structural.json")

# defaults drifter init writes into scope.json (spec 3.2)
DEFAULT_SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}

# stands in for behavioral.json until its generator registers (spec #12, Further Notes)
BEHAVIORAL_PLACEHOLDER = {"schema_version": 1}

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
            found.append(_difference("ADDED", fresh_by_id[element_id]))
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
    # files, and the commits the ownership check judges. All four no-verdict codes are raised
    # here, before any generator runs (phase4.md Q2).
    tree = reader.tree()
    missing = [name for name in MODEL_FILES if f"models/{name}" not in tree]
    if missing:
        raise DriftError("MODELS_NOT_FOUND", f"models/{missing[0]} is missing at {reader.head}")
    committed = reader.read([f"models/{name}" for name in MODEL_FILES])
    models = {name: _model(f"models/{name}", committed[f"models/{name}"]) for name in MODEL_FILES}
    for name in ("behavioral.json", "structural.json"):
        _element_rule(f"models/{name}", models[name])
    _scope_rule(models["scope.json"])
    _ownership_rule(models["ownership.json"])
    files = _read_files(reader, in_scope(sorted(tree), models["scope.json"]))
    return Sources(files=files, models=models, commits=_parse_history(reader.log()))


def _read_files(reader: Reader, paths: list[str]) -> dict[str, str]:
    # judges each file in path order by size, then encoding, then syntax, so the first bad file
    # is the one reported (phase4.md Q2). Size is judged on what arrived: a blobless clone cannot
    # report it any earlier. Parsing every file here lets a generator assume each one parses (spec 3.2).
    raw = reader.read(paths)
    files = {}
    for path in sorted(raw):
        if len(raw[path]) > MAX_FILE_BYTES:
            raise DriftError("FILE_TOO_LARGE", f"{path} is {len(raw[path])} bytes, over 1 MB")
        files[path] = _decode(path, raw[path])
        try:
            parse_files({path: files[path]})
        except ParseFailed as exc:
            raise DriftError(exc.code, str(exc)) from None
    return files


# ------------------------------------------------------------ the first models, for drifter init


class HistoryReader(Reader, Protocol):
    # adds every commit reachable from head to a Reader, for proposing ownership
    def history(self) -> str:
        # returns every commit reachable from head as one LOG_ARGS log, newest first
        ...


def generate_models(reader: HistoryReader) -> dict[str, str]:
    # returns the four /models files' text at the commit, as drifter init writes them: the
    # default scope, the regenerated models and ownership proposed from all history (spec 3.2)
    files = _read_files(reader, in_scope(sorted(reader.tree()), DEFAULT_SCOPE))
    models = _regenerate(files)
    models["ownership.json"] = proposed_ownership(reader)
    models["scope.json"] = DEFAULT_SCOPE
    return {name: write_model(models[name]) for name in MODEL_FILES}


def proposed_ownership(reader: HistoryReader) -> dict:
    # proposes ownership from all of history, for a caller that wants that one model: drifter init
    # writing the first /models, or a page showing a repository that has committed none
    return propose_ownership(reader.head, _parse_history(reader.history()))


def regenerate_models(reader: Reader) -> dict[str, str]:
    # returns structural.json and behavioral.json's text at the commit, as drifter update writes
    # them. Only the committed scope.json is read, so a broken model being replaced cannot block it.
    if "models/scope.json" not in reader.tree():
        raise DriftError("MODELS_NOT_FOUND", f"models/scope.json is missing at {reader.head}")
    scope = _model("models/scope.json", reader.read(["models/scope.json"])["models/scope.json"])
    _scope_rule(scope)
    files = _read_files(reader, in_scope(sorted(reader.tree()), scope))
    return {name: write_model(model) for name, model in _regenerate(files).items()}


def _regenerate(files: dict[str, str]) -> dict[str, dict]:
    # regenerates structural.json and behavioral.json from in-scope files; behavioral is a
    # placeholder until its generator registers
    return {
        f"{name}.json": GENERATORS[name](files) if name in GENERATORS else BEHAVIORAL_PLACEHOLDER
        for name in ("behavioral", "structural")
    }


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
        # reads each path's blob at the head in one git call, so a large checkout starts one
        # process, not one per file
        tree = self.tree()
        shas = sorted({tree[path] for path in paths})
        raw = _run(self.repo, "cat-file", "--batch", input="".join(f"{sha}\n" for sha in shas).encode())
        blobs, at = {}, 0
        while at < len(raw):
            # reads "<sha> blob <size>", then that many bytes and the newline after them
            end = raw.index(b"\n", at)
            sha, _, size = raw[at:end].decode().split(" ")
            blobs[sha] = raw[end + 1:end + 1 + int(size)]
            at = end + 1 + int(size) + 1
        return {path: blobs[tree[path]] for path in paths}

    def log(self) -> str:
        # reads the commits base..head, or the head alone for a root commit
        span = f"{self.base}..{self.head}" if self.base else self.head
        return _git(self.repo, *LOG_ARGS, span)

    def history(self) -> str:
        # reads every commit reachable from the head
        return _git(self.repo, *LOG_ARGS, self.head)


def _decode(path: str, data: bytes) -> str:
    # turns one in-scope file's bytes into text; one that is not UTF-8 ends the check (spec 5.2)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise DriftError("PARSE_FAILED", f"{path} is not UTF-8 text") from None


def _element_rule(path: str, model: object) -> None:
    # rejects a model that breaks the element rule (model-seam.md): an object whose top-level
    # lists hold objects with a string id, kind and file, no id repeated, since the diff by id
    # would silently collapse a repeat
    if not isinstance(model, dict):
        raise DriftError("INVALID_MODELS", f"{path} is not a JSON object")
    seen: set[str] = set()
    for value in model.values():
        for element in value if isinstance(value, list) else ():
            if not (isinstance(element, dict) and all(isinstance(element.get(k), str) for k in ("id", "kind", "file"))):
                raise DriftError("INVALID_MODELS", f"{path} has an element without a string id, kind and file")
            if element["id"] in seen:
                raise DriftError("INVALID_MODELS", f"{path} repeats the id {element['id']}")
            seen.add(element["id"])


def _scope_rule(scope: object) -> None:
    # rejects a scope.json that is not an object whose include and exclude, when given, are
    # lists of patterns
    if not isinstance(scope, dict):
        raise DriftError("INVALID_MODELS", "models/scope.json is not a JSON object")
    for key in ("include", "exclude"):
        patterns = scope.get(key, [])
        if not (isinstance(patterns, list) and all(isinstance(p, str) for p in patterns)):
            raise DriftError("INVALID_MODELS", f"models/scope.json: {key} is not a list of patterns")


def _ownership_rule(model: object) -> None:
    # rejects an ownership.json the checker cannot read: an object whose rules, when given, are
    # objects with a string pattern and a list of string owners
    if not isinstance(model, dict):
        raise DriftError("INVALID_MODELS", "models/ownership.json is not a JSON object")
    rules = model.get("rules", [])
    if not isinstance(rules, list):
        raise DriftError("INVALID_MODELS", "models/ownership.json: rules is not a list")
    for rule in rules:
        owners = rule.get("owners") if isinstance(rule, dict) else None
        if not (isinstance(owners, list) and all(isinstance(o, str) for o in owners) and isinstance(rule.get("pattern"), str)):
            raise DriftError("INVALID_MODELS", "models/ownership.json has a rule without a string pattern and a list of owners")


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
    records: list[CommitRecord] = []
    touches: list[PathTouch] = []
    header: str | None = None
    i = 0
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


def _run(repo: Path, *args: str, input: bytes | None = None) -> bytes:
    # runs one git command in repo, feeding it input, and returns its bytes
    return subprocess.run(["git", "-C", str(repo), *args], input=input, capture_output=True, check=True).stdout

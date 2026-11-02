# loads a repository's committed models into dataclasses, so a page or a frontend reads one shape
# instead of raw JSON; reads only, never generates, and never repairs a file it does not recognise

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# names the files the generators write into a repository's /models folder
STRUCTURAL_FILE = "structural.json"
BEHAVIORAL_FILE = "behavioral.json"
OWNERSHIP_FILE = "ownership.json"
SCOPE_FILE = "scope.json"


class ModelLoadError(Exception):
    # reports a model file that is not the shape its generator writes, naming the file and the
    # field, so a changed generator fails loudly rather than rendering a half-empty page
    pass


@dataclass(frozen=True)
class Node:
    # one part of the code: a module, class, function or method (base/structure.md).
    # The signature fields stay empty for a module or class, which carry none.
    id: str
    kind: str
    file: str
    is_async: bool = False
    decorators: tuple[str, ...] = ()
    params: tuple[str, ...] = ()


@dataclass(frozen=True)
class Edge:
    # one relation between nodes: a module importing a module, or a class inheriting a class
    id: str
    kind: str
    source: str
    target: str
    file: str


@dataclass(frozen=True)
class StructuralModel:
    # one structural model, nodes and edges kept in the file's order (sorted by id)
    schema_version: int
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class State:
    # one value a variable takes inside one machine (base/behavioral.md). A machine groups states
    # by the class or function they live in, so one machine may hold several variables.
    id: str
    kind: str
    file: str
    machine: str
    variable: str
    value: str


@dataclass(frozen=True)
class Transition:
    # one function or method moving a variable from one value to another. The guard is always
    # the source state restated, so the trigger is what an arrow carries that its ends do not.
    id: str
    kind: str
    file: str
    source: str
    target: str
    trigger: str
    guard: str


@dataclass(frozen=True)
class BehavioralModel:
    # one behavioral model, states and transitions kept in the file's order (sorted by id)
    schema_version: int
    states: tuple[State, ...]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class OwnershipRule:
    # one path pattern's owners by git author email; a path no rule matches is open to anyone,
    # and the rules are tried in order, so the first match wins (spec 3.2)
    pattern: str
    owners: tuple[str, ...]


@dataclass(frozen=True)
class OwnershipModel:
    # one ownership model, rules kept in the file's order (sorted by path)
    schema_version: int
    rules: tuple[OwnershipRule, ...]


@dataclass(frozen=True)
class Scope:
    # which paths count as the code the models describe, as include and exclude patterns (spec 3.2)
    include: tuple[str, ...]
    exclude: tuple[str, ...]


@dataclass(frozen=True)
class Models:
    # one repository's models, a field being None where that model is absent. The source names
    # where they came from, a folder for a checkout or owner/name@sha for a clone, and is shown
    # to the reader rather than read back.
    source: str
    structural: StructuralModel | None
    behavioral: BehavioralModel | None
    ownership: OwnershipModel | None
    scope: Scope | None


def load_models(models_dir: str | Path) -> Models:
    # loads every model a folder holds and skips the ones it does not; a model that is present
    # but malformed raises ModelLoadError rather than loading as empty
    folder = Path(models_dir)
    structural_file = folder / STRUCTURAL_FILE
    behavioral_file = folder / BEHAVIORAL_FILE
    ownership_file = folder / OWNERSHIP_FILE
    scope_file = folder / SCOPE_FILE
    return Models(
        source=str(folder),
        structural=load_structural(structural_file) if structural_file.is_file() else None,
        behavioral=load_behavioral(behavioral_file) if behavioral_file.is_file() else None,
        ownership=load_ownership(ownership_file) if ownership_file.is_file() else None,
        scope=load_scope(scope_file) if scope_file.is_file() else None,
    )


def models_from_dicts(parsed: dict[str, dict], source: str) -> Models:
    # builds the same Models from models another module already parsed, keyed by file name, so a
    # server holding a repository's models in memory does not write them to disk to show them
    return Models(
        source=source,
        structural=structural_from_dict(parsed[STRUCTURAL_FILE], STRUCTURAL_FILE)
        if STRUCTURAL_FILE in parsed else None,
        behavioral=behavioral_from_dict(parsed[BEHAVIORAL_FILE], BEHAVIORAL_FILE)
        if BEHAVIORAL_FILE in parsed else None,
        ownership=ownership_from_dict(parsed[OWNERSHIP_FILE], OWNERSHIP_FILE)
        if OWNERSHIP_FILE in parsed else None,
        scope=scope_from_dict(parsed[SCOPE_FILE], SCOPE_FILE) if SCOPE_FILE in parsed else None,
    )


def load_structural(path: str | Path) -> StructuralModel:
    # reads one structural.json, as base/structure.md defines it
    return structural_from_dict(_read(path), path)


def load_behavioral(path: str | Path) -> BehavioralModel:
    # reads one behavioral.json, as base/behavioral.md defines it
    return behavioral_from_dict(_read(path), path)


def load_ownership(path: str | Path) -> OwnershipModel:
    # reads one ownership.json, as propose_ownership writes it
    return ownership_from_dict(_read(path), path)


def load_scope(path: str | Path) -> Scope:
    # reads one scope.json, which decides which files the code models describe
    return scope_from_dict(_read(path), path)


def structural_from_dict(data: dict, label: str | Path) -> StructuralModel:
    # builds one structural model, label naming the source in any error
    return StructuralModel(
        schema_version=_field(data, "schema_version", label),
        nodes=tuple(_node(entry, label) for entry in _field(data, "nodes", label)),
        edges=tuple(_edge(entry, label) for entry in _field(data, "edges", label)),
    )


def behavioral_from_dict(data: dict, label: str | Path) -> BehavioralModel:
    # builds one behavioral model, label naming the source in any error
    return BehavioralModel(
        schema_version=_field(data, "schema_version", label),
        states=tuple(_state(entry, label) for entry in _field(data, "states", label)),
        transitions=tuple(_transition(entry, label) for entry in _field(data, "transitions", label)),
    )


def ownership_from_dict(data: dict, label: str | Path) -> OwnershipModel:
    # builds one ownership model, label naming the source in any error
    return OwnershipModel(
        schema_version=_field(data, "schema_version", label),
        rules=tuple(_rule(entry, label) for entry in _field(data, "rules", label)),
    )


def scope_from_dict(data: dict, label: str | Path) -> Scope:
    # builds one scope, label naming the source in any error
    return Scope(
        include=tuple(_field(data, "include", label)),
        exclude=tuple(_field(data, "exclude", label)),
    )


def _read(path: str | Path) -> dict:
    # parses one model file, reporting unreadable JSON and anything that is not an object
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelLoadError(f"{path}: {exc}") from None
    if not isinstance(data, dict):
        raise ModelLoadError(f"{path}: expected a JSON object, found {type(data).__name__}")
    return data


def _field(entry: dict, key: str, path: str | Path):
    # takes one required field, naming the file and the key where it is absent
    if key not in entry:
        raise ModelLoadError(f"{path}: an entry is missing {key!r}")
    return entry[key]


def _node(entry: dict, path: str | Path) -> Node:
    # builds one node, reading the signature fields only a function or method carries
    return Node(
        id=_field(entry, "id", path),
        kind=_field(entry, "kind", path),
        file=_field(entry, "file", path),
        is_async=entry.get("async", False),
        decorators=tuple(entry.get("decorators", ())),
        params=tuple(entry.get("params", ())),
    )


def _edge(entry: dict, path: str | Path) -> Edge:
    # builds one edge
    return Edge(
        id=_field(entry, "id", path),
        kind=_field(entry, "kind", path),
        source=_field(entry, "source", path),
        target=_field(entry, "target", path),
        file=_field(entry, "file", path),
    )


def _state(entry: dict, path: str | Path) -> State:
    # builds one state
    return State(
        id=_field(entry, "id", path),
        kind=_field(entry, "kind", path),
        file=_field(entry, "file", path),
        machine=_field(entry, "machine", path),
        variable=_field(entry, "variable", path),
        value=_field(entry, "value", path),
    )


def _transition(entry: dict, path: str | Path) -> Transition:
    # builds one transition
    return Transition(
        id=_field(entry, "id", path),
        kind=_field(entry, "kind", path),
        file=_field(entry, "file", path),
        source=_field(entry, "source", path),
        target=_field(entry, "target", path),
        trigger=_field(entry, "trigger", path),
        guard=_field(entry, "guard", path),
    )


def _rule(entry: dict, path: str | Path) -> OwnershipRule:
    # builds one ownership rule, its owners kept in the file's order (sorted by the generator)
    return OwnershipRule(
        pattern=_field(entry, "pattern", path),
        owners=tuple(_field(entry, "owners", path)),
    )

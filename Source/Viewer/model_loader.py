# loads a repository's committed models into dataclasses, so a page or a frontend reads one shape
# instead of raw JSON; reads only, never generates, and never repairs a file it does not recognise

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# names the files the generators write into a repository's /models folder
STRUCTURAL_FILE = "structural.json"
OWNERSHIP_FILE = "ownership.json"


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
class OwnershipRule:
    # one file's owners by git author email; a file no rule names is open to anyone (spec 3.2)
    path: str
    owners: tuple[str, ...]


@dataclass(frozen=True)
class OwnershipModel:
    # one ownership model, rules kept in the file's order (sorted by path)
    schema_version: int
    rules: tuple[OwnershipRule, ...]


@dataclass(frozen=True)
class Models:
    # one repository's models, a field being None where that file is not in the folder
    models_dir: Path
    structural: StructuralModel | None
    ownership: OwnershipModel | None


def load_models(models_dir: str | Path) -> Models:
    # loads every model a folder holds and skips the ones it does not; a model that is present
    # but malformed raises ModelLoadError rather than loading as empty
    folder = Path(models_dir)
    structural_file = folder / STRUCTURAL_FILE
    ownership_file = folder / OWNERSHIP_FILE
    return Models(
        models_dir=folder,
        structural=load_structural(structural_file) if structural_file.is_file() else None,
        ownership=load_ownership(ownership_file) if ownership_file.is_file() else None,
    )


def load_structural(path: str | Path) -> StructuralModel:
    # reads one structural.json, as base/structure.md defines it
    data = _read(path)
    return StructuralModel(
        schema_version=_field(data, "schema_version", path),
        nodes=tuple(_node(entry, path) for entry in _field(data, "nodes", path)),
        edges=tuple(_edge(entry, path) for entry in _field(data, "edges", path)),
    )


def load_ownership(path: str | Path) -> OwnershipModel:
    # reads one ownership.json, as propose_ownership writes it
    data = _read(path)
    return OwnershipModel(
        schema_version=_field(data, "schema_version", path),
        rules=tuple(_rule(entry, path) for entry in _field(data, "rules", path)),
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


def _rule(entry: dict, path: str | Path) -> OwnershipRule:
    # builds one ownership rule, its owners kept in the file's order (sorted by the generator)
    return OwnershipRule(
        path=_field(entry, "path", path),
        owners=tuple(_field(entry, "owners", path)),
    )

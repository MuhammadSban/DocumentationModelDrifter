# gives each changed path a category from the pod's mapping-v1.1.yaml, first match wins (v1.1 SPEC section 5.1),
# and says which paths are skipped and which implementation paths have no mapping

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from GitHub_Connector.schemas import Category
from GitHub_Connector.settings import get_settings
from models.common import glob


@dataclass(frozen=True)
class _Mapping:
    # holds one version of the mapping file
    config_version: str
    categories: list[tuple[re.Pattern, Category]]
    default: Category
    extensions: frozenset[str]
    filenames: frozenset[str]
    sources: frozenset[str]
    max_changed_files: int


def _mapping() -> _Mapping:
    # rereads the mapping whenever the file changes on disk
    path = get_settings().mapping_file
    st = path.stat()
    return _load(path, st.st_mtime_ns, st.st_size)


@lru_cache(maxsize=8)
def _load(path: Path, _mtime: int, _size: int) -> _Mapping:
    # reads one version of the mapping, patterns compiled in file order
    data = yaml.safe_load(path.read_text("utf-8"))
    categories = [
        (glob(pattern), Category(entry["category"]))
        for entry in data["categories"]
        for pattern in entry["patterns"]
    ]
    return _Mapping(
        config_version=data["config_version"],
        categories=categories,
        default=Category(data["default_category"]),
        extensions=frozenset(ext.lower() for ext in data["supported_extensions"]),
        filenames=frozenset(data["supported_filenames"]),
        sources=frozenset(m["source"] for m in data.get("mappings") or []),
        max_changed_files=data["max_changed_files"],
    )


def config_version() -> str:
    # names the mapping version every result carries, mapping-v1.1
    return _mapping().config_version


def classify(path: str) -> Category:
    # returns the category of the first pattern that matches, else the default, OTHER
    loaded = _mapping()
    for pattern, category in loaded.categories:
        if pattern.match(path):
            return category
    return loaded.default


def is_unsupported(path: str) -> bool:
    # says whether a path is off the allowlist: neither its extension (any case) nor its file name is listed
    loaded = _mapping()
    name = path.rsplit("/", 1)[-1]
    ext = name[name.rfind("."):].lower() if "." in name else ""
    return ext not in loaded.extensions and name not in loaded.filenames


def is_mapped(path: str) -> bool:
    # says whether a path is the source of an entry in mappings
    return path in _mapping().sources


def max_changed_files() -> int:
    # caps how many changed paths one analysis takes, more is CHANGE_LIMIT_EXCEEDED
    return _mapping().max_changed_files

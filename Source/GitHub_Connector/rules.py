# gives each changed path a category from the ordered rules file, first match wins,
# and says which file types are skipped unread

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path

from GitHub_Connector.schemas import Category
from GitHub_Connector.settings import get_settings


@dataclass(frozen=True)
class _Rules:
    # holds one version of the rules file
    raw: bytes
    rules: list[tuple[str, Category]]
    fallback: Category
    unsupported_exts: tuple[str, ...]


def _rules(rules_file: Path) -> _Rules:
    # rereads the rules whenever the file changes on disk
    st = rules_file.stat()
    return _load(rules_file, st.st_mtime_ns, st.st_size)


@lru_cache(maxsize=8)
def _load(rules_file: Path, _mtime: int, _size: int) -> _Rules:
    # reads one version of the rules, line endings normalised so a Windows checkout hashes the same
    raw = rules_file.read_bytes().replace(b"\r\n", b"\n")
    data = json.loads(raw)
    rules = [(r["pattern"], Category(r["category"])) for r in data.get("rules", [])]
    exts = tuple(ext.lower() for ext in data.get("unsupported", []))
    return _Rules(raw, rules, Category(data["fallback"]), exts)


def config_version() -> str:
    # hashes the rules file, so any rule change shows up in every run file
    return hashlib.sha256(_rules(get_settings().rules_file).raw).hexdigest()[:12]


def classify(path: str) -> Category:
    # returns the category of the first rule that matches, else the fallback
    loaded = _rules(get_settings().rules_file)
    for pattern, category in loaded.rules:
        if matches(pattern, path):
            return category
    return loaded.fallback


def is_unsupported(path: str) -> bool:
    # says whether a path's file type is on the denylist, so it is skipped without being read
    name = path.rsplit("/", 1)[-1].lower()
    return name.endswith(_rules(get_settings().rules_file).unsupported_exts)


def matches(pattern: str, path: str) -> bool:
    # matches one rule against a repo-relative path, gitignore style
    if "/" not in pattern:
        # matches a bare name pattern such as *.md against the file name, in any folder
        return fnmatchcase(path.rsplit("/", 1)[-1], pattern)
    if pattern.endswith("/**"):
        # matches a folder pattern such as docs/** against everything under it, from the root
        return path.startswith(pattern[:-2])
    return fnmatchcase(path, pattern)

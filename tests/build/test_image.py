# checks the image's build files as committed text; no test builds an image or starts Docker

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _lines(name: str) -> list[str]:
    # reads a root file's lines, without blanks and comments
    text = (ROOT / name).read_text(encoding="utf-8")
    return [s for s in (line.strip() for line in text.splitlines()) if s and not s.startswith("#")]


def test_dockerignore_keeps_out_git_env_and_caches() -> None:
    # checks .git, every .env* file and the caches are left out at any depth
    assert (ROOT / ".dockerignore").is_file(), ".dockerignore is missing"
    lines = _lines(".dockerignore")
    for pattern in ("**/.git", "**/.env*", "**/__pycache__", "**/.mypy_cache"):
        assert pattern in lines, f".dockerignore lacks {pattern}"

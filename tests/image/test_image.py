# checks the image's build files as committed text; no test builds an image or starts Docker

from __future__ import annotations

import re
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


def test_source_is_the_last_copy_in_the_dockerfile() -> None:
    # checks Source/ is copied last, so a change there reuses every layer above it
    copies = [line for line in _lines("Dockerfile") if line.startswith("COPY ")]
    assert copies[-1] == "COPY Source/ Source/", f"the last COPY is {copies[-1]!r}"


PINNED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[^\]]*\])?==[A-Za-z0-9.+!_-]+(\s*;.*)?$")


def _requirements(name: str) -> list[str]:
    # joins a lock's continued lines into one requirement each, its markers and hashes included
    joined = "\n".join(_lines(name)).replace("\\\n", " ")
    return [line for line in joined.splitlines() if line.strip()]


def test_every_requirement_has_an_exact_version_and_a_hash() -> None:
    # checks both locks pin every package to one version and carry its hashes
    for name in ("requirements.txt", "requirements-dev.txt"):
        reqs = _requirements(name)
        assert reqs, f"{name} names no package"
        for req in reqs:
            spec, _, hashes = req.partition("--hash=")
            assert PINNED.match(spec.strip()), f"{name}: no exact version in {spec.strip()!r}"
            assert hashes.startswith("sha256:"), f"{name}: no sha256 hash for {spec.strip()!r}"


def test_dockerfile_and_ci_name_the_same_exact_python_patch() -> None:
    # checks the image and CI run one three-part Python version
    image = re.search(r"^FROM python:([^-\s]+)", "\n".join(_lines("Dockerfile")), re.M)
    ci = re.search(r'^python-version:\s*"([^"]+)"', "\n".join(_lines(".github/workflows/ci.yml")), re.M)
    assert image and ci, "the FROM line or the python-version is missing"
    assert re.fullmatch(r"\d+\.\d+\.\d+", image[1]), f"the Dockerfile names {image[1]}, not a patch"
    assert image[1] == ci[1], f"the Dockerfile names {image[1]}, CI names {ci[1]}"

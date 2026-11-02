# runs the drifter command line on a local checkout, the current folder by default. check prints the
# four-field answer as canonical JSON and exits 0 when aligned, 1 on drift, 2 with no verdict.
# init writes the four /models files from a commit and refuses (exit 1) to overwrite one unless
# --force; update rewrites only structural.json and behavioral.json, from the scope committed at
# the commit, leaving ownership.json and scope.json as the person left them. A no-verdict code
# prints its drift_error and exits 2 for every command.

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from drifter.check import (
    MODEL_FILES,
    DriftError,
    LocalReader,
    answer,
    generate_models,
    local_sources,
    regenerate_models,
)
from models.common import write_model


def main(argv: list[str] | None = None) -> int:
    # parses one command, runs it and returns its exit code
    parser = argparse.ArgumentParser(prog="drifter")
    commands = parser.add_subparsers(dest="command", required=True)
    check_cmd = commands.add_parser("check", help="check the code at a commit against the committed /models")
    check_cmd.add_argument("commit", nargs="?", default="HEAD")
    check_cmd.add_argument("--base", help="the commit to judge ownership from; defaults to the commit's first parent")
    check_cmd.add_argument("--repo", default=".", help="the checkout to check; defaults to the current folder")
    init_cmd = commands.add_parser("init", help="write the first /models from the code at a commit")
    init_cmd.add_argument("commit", nargs="?", default="HEAD")
    init_cmd.add_argument("--force", action="store_true", help="overwrite existing /models files")
    init_cmd.add_argument("--repo", default=".", help="the checkout to write into; defaults to the current folder")
    update_cmd = commands.add_parser("update", help="regenerate structural.json and behavioral.json, accepting drift")
    update_cmd.add_argument("commit", nargs="?", default="HEAD")
    update_cmd.add_argument("--repo", default=".", help="the checkout to write into; defaults to the current folder")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            return _init(Path(args.repo), args.commit, args.force)
        if args.command == "update":
            _write(_models_folder(Path(args.repo)), regenerate_models(LocalReader(Path(args.repo), args.commit)))
            return 0
        verdict = answer(local_sources(Path(args.repo), args.commit, args.base))
    except DriftError as exc:
        _print({"drift": None, "drift_error": exc.body()})
        return 2
    _print(verdict)
    return 0 if verdict["aligned"] else 1


def _init(repo: Path, commit: str, force: bool) -> int:
    # writes the four files into the checkout's top-level /models, refusing to replace one unless forced
    models = _models_folder(repo)
    existing = [name for name in MODEL_FILES if (models / name).exists()]
    if existing and not force:
        print(f"drifter: models/{existing[0]} exists; use --force to overwrite", file=sys.stderr)
        return 1
    _write(models, generate_models(LocalReader(repo, commit)))
    return 0


def _models_folder(repo: Path) -> Path:
    # finds the checkout's top-level /models, whichever folder the command runs in
    top = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, check=True)
    return Path(top.stdout.decode("utf-8").strip()) / "models"


def _write(models: Path, texts: dict[str, str]) -> None:
    # writes each file's text as UTF-8 bytes, so Windows adds no carriage returns
    models.mkdir(exist_ok=True)
    for name, text in texts.items():
        (models / name).write_bytes(text.encode("utf-8"))


def _print(body: dict) -> None:
    # writes canonical JSON as UTF-8 bytes, so Windows adds no carriage returns
    sys.stdout.buffer.write(write_model(body).encode("utf-8"))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    sys.exit(main())

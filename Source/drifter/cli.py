# runs the drifter command line on a local checkout, the current folder by default. check prints the
# four-field answer as canonical JSON and exits 0 when aligned, 1 on drift, 2 with no verdict.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from drifter.check import DriftError, answer, local_sources
from models.common import write_model


def main(argv: list[str] | None = None) -> int:
    # parses one command, runs it and returns its exit code
    parser = argparse.ArgumentParser(prog="drifter")
    commands = parser.add_subparsers(dest="command", required=True)
    check_cmd = commands.add_parser("check", help="check the code at a commit against the committed /models")
    check_cmd.add_argument("commit", nargs="?", default="HEAD")
    check_cmd.add_argument("--base", help="the commit to judge ownership from; defaults to the commit's first parent")
    check_cmd.add_argument("--repo", default=".", help="the checkout to check; defaults to the current folder")
    args = parser.parse_args(argv)
    try:
        verdict = answer(local_sources(Path(args.repo), args.commit, args.base))
    except DriftError as exc:
        _print({"drift": None, "drift_error": exc.body()})
        return 2
    _print(verdict)
    return 0 if verdict["aligned"] else 1


def _print(body: dict) -> None:
    # writes canonical JSON as UTF-8 bytes, so Windows adds no carriage returns
    sys.stdout.buffer.write(write_model(body).encode("utf-8"))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    sys.exit(main())

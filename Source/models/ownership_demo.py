# shows both halves of the ownership model: what drifter init proposes from history, and what a
# push is then judged against
#
#   python3 Source/models/ownership_demo.py              # the sample history below
#   python3 Source/models/ownership_demo.py --repo .     # a real repository

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drifter.check import check_ownership
from models.common import write_model
from models.ownership_model import (
    BOT_MARK,
    MAX_FILES,
    SKIP,
    WINDOW,
    CommitRecord,
    PathTouch,
    propose_ownership,
)

LINE = "=" * 94

# maps git's status letters to change types, for --repo
LETTERS = {"A": "ADDED", "M": "MODIFIED", "D": "DELETED", "R": "RENAMED", "C": "COPIED", "T": "TYPE_CHANGED"}


def sample() -> tuple[str, list[CommitRecord]]:
    # builds a history that trips every proposal rule once, newest commit first
    def c(sha, email, parents, paths):
        return CommitRecord(sha, email, parents, tuple(paths))

    def M(p): return PathTouch(p, "MODIFIED")
    def A(p): return PathTouch(p, "ADDED")
    def D(p): return PathTouch(p, "DELETED")
    def R(new, old): return PathTouch(new, "RENAMED", old)

    return "h0", [
        c("h0", "ana@x.com", ("h1",), [M("src/core.py"), M("models/ownership.json")]),
        c("h1", "mika@x.com", ("h2", "s1"), [M("src/core.py")]),
        c("s1", "bob@x.com", ("h3",), [M("docs/guide.md")]),
        c("h2", "dependabot[bot]@users.noreply.github.com", ("h3",), [M("requirements.txt")]),
        c("h3", "bob@x.com", ("h4",), [R("src/core.py", "src/main.py")]),
        c("h4", "ana@x.com", ("h5",), [M("src/main.py"), D("src/legacy.py")]),
        c("h5", "cho@x.com", ("h6",), [M("src/main.py"), A("docs/guide.md")]),
        c("h6", "sweeper@x.com", ("h7",), [M(f"gen/f{i}.py") for i in range(60)]),
        c("h7", "ana@x.com", (), [A("src/main.py"), A("src/legacy.py"), A("requirements.txt")]),
    ]


def from_repo(repo: Path) -> tuple[str, list[CommitRecord]]:
    # reads a real repository's whole history, as drifter init does
    head = _git(repo, "rev-parse", "HEAD").strip()
    raw = _git(repo, "log", "--topo-order", "--name-status", "-M", "--format=%x00%H%x1f%ae%x1f%P", head)
    records = []
    for block in raw.split("\x00"):
        if not block.strip():
            continue
        lines = block.strip("\n").split("\n")
        sha, email, parents = lines[0].split("\x1f")
        touches = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split("\t")
            if parts[0][0] == "R":
                touches.append(PathTouch(parts[2], "RENAMED", parts[1]))
            else:
                touches.append(PathTouch(parts[1], LETTERS[parts[0][0]]))
        records.append(CommitRecord(sha, email.lower(), tuple(parents.split()), tuple(touches)))
    return head, records


def _git(repo: Path, *args: str) -> str:
    # runs one git command and returns its text
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          check=True).stdout.decode("utf-8", "surrogateescape")


def why_ignored(record: CommitRecord) -> str:
    # names the rule that stops a commit naming an owner, empty where it names one
    if len(record.parents) > 1:
        return f"merge, {len(record.parents)} parents"
    if BOT_MARK in record.author_email:
        return "bot author"
    if len(record.paths) > MAX_FILES:
        return f"sweep, {len(record.paths)} files over {MAX_FILES}"
    return ""


def show_history(head: str, records: list[CommitRecord], limit: int) -> None:
    # prints the history exactly as propose_ownership receives it, newest first
    print(LINE)
    print("IN   git history, newest first")
    print(LINE)
    print(f"head {head}")
    print(f"commits {len(records)}   window {WINDOW} commits per file   skip {', '.join(SKIP)}")
    print()
    print(f"{'#':>3}  {'sha':<10} {'author':<40} {'par':>3} {'files':>5}  names an owner?")
    for i, record in enumerate(records[:limit]):
        ignored = why_ignored(record)
        print(f"{i:>3}  {record.sha[:10]:<10} {record.author_email[:40]:<40} "
              f"{len(record.parents):>3} {len(record.paths):>5}  {'no: ' + ignored if ignored else 'yes'}")
    if len(records) > limit:
        print(f"     ... {len(records) - limit} more commits")
    print()


def show_proposal(proposed: dict, limit: int) -> None:
    # prints the file drifter init would write, and what it left out
    text = write_model(proposed)
    print(LINE)
    print("OUT  models/ownership.json, for a person to correct by hand")
    print(LINE)
    print(f"rules {len(proposed['rules'])}   schema_version {proposed['schema_version']}   "
          f"{len(text)} bytes")
    print()
    for rule in proposed["rules"][:limit]:
        print(f"  {rule['pattern']:<40} {', '.join(rule['owners'])}")
    if len(proposed["rules"]) > limit:
        print(f"  ... {len(proposed['rules']) - limit} more rules")
    print()
    print("first 300 bytes as written:")
    print(text[:300] + ("..." if len(text) > 300 else ""))
    print()


def show_check(proposed: dict, candidates: list[CommitRecord]) -> None:
    # prints the other half: commits judged against the rules
    print(LINE)
    print("IN   commits a push asks about, judged against those rules")
    print(LINE)
    for record in candidates:
        paths = ", ".join(t.path for t in record.paths)
        print(f"  {record.sha[:8]}  {record.author_email:<24} {len(record.parents)} parent(s)  {paths}")
    print()
    violations = check_ownership(proposed, candidates)
    print(LINE)
    print("OUT  ownership violations, the drift answer's ownership field")
    print(LINE)
    if not violations:
        print("  none, every change was made by an owner or touched a path no rule covers")
    for v in violations:
        print(f"  {v['change']}  {v['path']}")
        print(f"            author {v['author']} is not among {', '.join(v['owners'])}")
        print(f"            commit {v['commit']}")
    print()


def main() -> None:
    # runs the sample history, or a real repository given --repo
    args = sys.argv[1:]
    if "--repo" in args:
        repo = Path(args[args.index("--repo") + 1]).resolve()
        print(f"\nreading {repo}")
        head, records = from_repo(repo)
        limit = 12
    else:
        head, records = sample()
        limit = 100

    show_history(head, records, limit)
    proposed = propose_ownership(head, records)
    show_proposal(proposed, limit)

    # judges the head commit, then the same change made by someone with no claim to the file
    owned = [rule for rule in proposed["rules"] if rule["owners"]]
    candidates = [records[0]]
    if owned:
        candidates.append(CommitRecord("f" * 40, "stranger@x.com", ("x" * 40,),
                                       (PathTouch(owned[0]["pattern"], "MODIFIED"),)))
    show_check(proposed, candidates)
    print("same history proposed twice gives identical bytes:",
          write_model(propose_ownership(head, records)) == write_model(proposed))


if __name__ == "__main__":
    main()

# runs one drifter check at a commit and returns the spec's four-field answer (REQ-02):
# regenerate the structural and behavioral models from the code and compare them with the
# committed /models by element id, and judge every non-merge commit between base and head
# against the ownership rules. Read-only: nothing here writes to the repository.
#
#   python3 Source/orchestration.py --repo . HEAD          # check a local clone
#   python3 Source/orchestration.py --repo . HEAD --base X  # against a given base
#
# Ownership is checked, never regenerated and diffed: history grows with the push being checked
# (spec 3.2). `drifter init` proposes the first ownership.json, a person corrects it, and from
# then on each push is judged against it.
#
# What the lower layers still owe, each marked FILLER, so `grep -n FILLER` is the to-do list:
#
#   behavioral_differences   the behavioral generator is not built
#   remote_sources           the connector cannot read a remote repo's history or /models yet
#   scope matching           must use the mapping-v1.1.yaml glob, one matcher shared (spec 3.2)

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from models.common import ParseFailed, parse_files
from models.ownership_model import CommitRecord, PathTouch, check_ownership
from models.structural_model import generate_structural

# names the four files /models must hold, as the contract's ModelsFixture requires
MODEL_FILES = ("behavioral.json", "ownership.json", "scope.json", "structural.json")

# defaults drifter init writes into scope.json (spec 3.2)
DEFAULT_SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}

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


@dataclass(frozen=True)
class Sources:
    # everything one check reads at one commit, gathered before any model is built
    files: dict[str, str]  # in-scope path -> text at the commit
    models: dict[str, dict]  # the committed /models, parsed
    commits: list[CommitRecord]  # the commits between base and head, newest first


# ------------------------------------------------------------------------------- the pure check


def answer(sources: Sources) -> dict:
    # returns the contract's DriftAnswer: aligned is true only when all three lists are empty
    structural = structural_differences(sources.files, sources.models["structural.json"])
    behavioral = behavioral_differences(sources.files, sources.models["behavioral.json"])
    ownership = check_ownership(sources.models["ownership.json"], sources.commits)
    return {
        "aligned": not (structural or behavioral or ownership),
        "behavioral": behavioral,
        "ownership": ownership,
        "structural": structural,
    }


def structural_differences(files: dict[str, str], committed: dict) -> list[dict]:
    # regenerates the structural model and sets it against the committed one by element id
    try:
        fresh = generate_structural(files)
    except ParseFailed as exc:
        raise DriftError(exc.code, str(exc)) from None
    return differences(fresh, committed)


def behavioral_differences(files: dict[str, str], committed: dict) -> list[dict]:
    # FILLER. returns no differences, so a check runs end to end before the generator exists.
    # The behavioral model holds at least states and transitions; its kind names, id scheme and
    # mining rules are open (spec 3.2, Q11). Once generate_behavioral(files) lands it reads the
    # same files dict and this becomes `return differences(generate_behavioral(files), committed)`,
    # since differences() is already keyed by element id and needs no change.
    return []


def differences(fresh: dict, committed: dict) -> list[dict]:
    # reports from the code's side: ADDED is in the code but not the model, REMOVED is in the
    # model but not the code, MODIFIED is one id in both with different attributes
    fresh_by_id = _elements(fresh)
    committed_by_id = _elements(committed)
    found = []
    for element_id in sorted(set(fresh_by_id) | set(committed_by_id)):
        in_code, in_model = fresh_by_id.get(element_id), committed_by_id.get(element_id)
        if in_model is None:
            found.append(_difference("ADDED", in_code))
        elif in_code is None:
            found.append(_difference("REMOVED", in_model))
        elif in_code != in_model:
            found.append(_difference("MODIFIED", in_code))
    return found


def _elements(model: dict) -> dict[str, dict]:
    # indexes a model's nodes and edges by id, the one key every comparison uses
    return {e["id"]: e for e in [*model.get("nodes", ()), *model.get("edges", ())]}


def _difference(change: str, element: dict) -> dict:
    # renders the contract's ModelDifference, whose keys are fixed
    return {"change": change, "file": element["file"], "id": element["id"], "kind": element["kind"]}


def in_scope(paths: list[str], scope: dict) -> list[str]:
    # keeps the paths scope.json includes and does not exclude.
    # FILLER as a pattern language: only `**/*.ext` and `dir/**` are understood, which covers the
    # defaults; spec 3.2 asks for the full mapping-v1.1.yaml glob, anything else is an exact path.
    include = scope.get("include", DEFAULT_SCOPE["include"])
    exclude = scope.get("exclude", DEFAULT_SCOPE["exclude"])
    kept = [p for p in paths if any(_matches(p, pattern) for pattern in include)]
    return sorted(p for p in kept if not any(_matches(p, pattern) for pattern in exclude))


def _matches(path: str, pattern: str) -> bool:
    # matches one scope pattern against a repo-relative path
    if pattern.startswith("**/"):
        return path.endswith(pattern[3:].lstrip("*"))
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return path == pattern


# ------------------------------------------------------------- reading one commit, locally or not


def local_sources(repo: Path, head: str, base: str | None = None) -> Sources:
    # reads a local clone with git, the stand-in for the connector's blobless clone
    head_sha = _git(repo, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
    models = _read_models(repo, head_sha)
    paths = _git(repo, "ls-tree", "-r", "--name-only", head_sha).splitlines()
    wanted = in_scope(paths, models["scope.json"])
    files = {path: _git(repo, "show", f"{head_sha}:{path}") for path in wanted}
    # parses every in-scope file once before any generator runs, so a generator may assume
    # each one parses and one bad file fails the whole check (spec 3.2)
    try:
        parse_files(files)
    except ParseFailed as exc:
        raise DriftError(exc.code, str(exc)) from None
    return Sources(files=files, models=models, commits=_history(repo, head_sha, base))


def remote_sources(repository: str, head: str, base: str | None = None) -> Sources:
    # FILLER. the same three reads against a repository the connector clones.
    # fetch() yields a Comparison, which is one diff, so two calls are missing: the history the
    # ownership check judges (`git log --topo-order --name-status -M` over the same clone, parsed
    # as _history() below does) and /models at the commit (cmp.read_many(MODEL_FILES, "head")).
    # The in-scope files are already reachable through cmp.tree("head") and cmp.read_many().
    raise NotImplementedError(
        f"cannot read {repository} at {head}: the connector has no history or /models call yet"
    )


def _read_models(repo: Path, commit: str) -> dict[str, dict]:
    # reads and parses the committed /models, failing with the contract's codes
    models = {}
    for name in MODEL_FILES:
        try:
            raw = _git(repo, "show", f"{commit}:models/{name}")
        except subprocess.CalledProcessError:
            raise DriftError("MODELS_NOT_FOUND", f"models/{name} is missing at {commit}") from None
        try:
            models[name] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DriftError("INVALID_MODELS", f"models/{name} is not valid JSON: {exc}") from None
    return models


def _history(repo: Path, head: str, base: str | None) -> list[CommitRecord]:
    # lists the commits the ownership check judges, newest first. The base defaults to the head's
    # first parent and is excluded; for a root commit only the head itself is judged (spec 3.1).
    if base is None:
        parents = _git(repo, "rev-parse", f"{head}^@").split()
        base = parents[0] if parents else None
    span = [f"{base}..{head}"] if base else [head]
    raw = _git(repo, "log", "--topo-order", "--name-status", "-M",
               "--format=%x00%H%x1f%ae%x1f%P", *span)
    records = []
    for block in raw.split("\x00"):
        if not block.strip():
            continue
        lines = block.strip("\n").split("\n")
        sha, email, parent_list = lines[0].split("\x1f")
        touches = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split("\t")
            if parts[0][0] == "R":
                touches.append(PathTouch(parts[2], "RENAMED", parts[1]))
            else:
                touches.append(PathTouch(parts[1], LETTERS[parts[0][0]]))
        records.append(CommitRecord(sha, email.lower(), tuple(parent_list.split()), tuple(touches)))
    return records


def _git(repo: Path, *args: str) -> str:
    # runs one git command in repo and returns its text, decoded as git hands paths over
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)
    return proc.stdout.decode("utf-8", "surrogateescape")


# ---------------------------------------------------------------------------------- command line


def report(verdict: dict, sources: Sources) -> None:
    # prints one check, what went in and what came out
    print(f"in   {len(sources.files)} in-scope files, {len(sources.commits)} commits judged, "
          f"{len(sources.models['ownership.json'].get('rules', ()))} ownership rules")
    print(f"out  aligned={verdict['aligned']}")
    for model in ("structural", "behavioral", "ownership"):
        rows = verdict[model]
        print(f"     {model:<12} {len(rows)} difference(s)")
        for row in rows[:5]:
            detail = row.get("id") or f"{row['path']} by {row['author']}"
            print(f"       {row['change']:<10} {detail}")
        if len(rows) > 5:
            print(f"       ... {len(rows) - 5} more")


def main() -> None:
    # checks a local clone at a commit
    args = sys.argv[1:]
    if "--repo" not in args:
        print(__doc__ or "usage: orchestration.py --repo PATH [COMMIT] [--base SHA]")
        return
    repo = Path(args[args.index("--repo") + 1]).resolve()
    base = args[args.index("--base") + 1] if "--base" in args else None
    positional = [a for i, a in enumerate(args) if not a.startswith("--") and args[i - 1] not in ("--repo", "--base")]
    head = positional[0] if positional else "HEAD"
    try:
        sources = local_sources(repo, head, base)
    except DriftError as exc:
        print(f"no verdict: {exc.code}  {exc.message}")
        return
    try:
        report(answer(sources), sources)
    except DriftError as exc:
        print(f"no verdict: {exc.code}  {exc.message}")


if __name__ == "__main__":
    main()

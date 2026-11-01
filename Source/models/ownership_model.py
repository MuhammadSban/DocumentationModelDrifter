# proposes the first models/ownership.json from git history, and judges commits against its rules.
# Ownership is not regenerated per push (spec 3.2): history grows with the push being checked, so
# comparing a fresh mining against the committed file would flag anyone new touching a file.

from __future__ import annotations

from dataclasses import dataclass

from models.common import glob, literal

SCHEMA_VERSION = 1

# lists the change types a commit may report, an unknown one is a contract break
CHANGE_TYPES = frozenset({"ADDED", "MODIFIED", "DELETED", "RENAMED", "COPIED", "TYPE_CHANGED"})

# names a bot in an author email, as GitHub writes dependabot[bot]@users.noreply.github.com
BOT_MARK = "[bot]"

# proposal defaults, which a person then corrects by hand like a CODEOWNERS file
WINDOW = 10  # commits per path that name its owners, so a departed author does not own it forever (spec 3.2)
MAX_FILES = 50  # a commit touching more is a sweep and names no owner
SKIP = ("vendor/", "third_party/", "node_modules/")  # vendored folders at any depth get no rule (spec 3.2)
MODELS = "models/"  # the root /models folder, which init writes, gets no rule (spec 3.2)


class OwnershipInputError(Exception):
    # signals commits that break the contract, naming the field rather than failing deeper
    pass


@dataclass(frozen=True)
class PathTouch:
    # names one path a commit changed, old_path is set only for RENAMED
    path: str
    change_type: str
    old_path: str | None = None


@dataclass(frozen=True)
class CommitRecord:
    # one commit as git reports it, newest first across a history; parents both marks a merge
    # and proves the ordering, and the author email is the identity the spec and contract use
    sha: str
    author_email: str
    parents: tuple[str, ...]
    paths: tuple[PathTouch, ...]


def validate(head_sha: str, records: list[CommitRecord]) -> None:
    # rejects records that break the contract, so a changed connector fails loudly, never quietly
    if not records:
        raise OwnershipInputError("records is empty, expected at least the head commit")
    seen: set[str] = set()
    # holds the commits the walk may name next: head, then every parent already announced
    frontier = {head_sha}
    for record in records:
        if record.sha in seen:
            raise OwnershipInputError(f"commit {record.sha} appears twice in records")
        if record.sha not in frontier:
            raise OwnershipInputError(
                f"commit {record.sha} is not head and is no parent of an earlier record; "
                "records must arrive newest first, starting at head (git log --topo-order)"
            )
        seen.add(record.sha)
        frontier.update(record.parents)
        if not record.author_email:
            raise OwnershipInputError(f"commit {record.sha} has no author_email")
        for touch in record.paths:
            if touch.change_type not in CHANGE_TYPES:
                raise OwnershipInputError(
                    f"commit {record.sha} reports unknown change_type {touch.change_type!r} "
                    f"for {touch.path}"
                )
            if touch.change_type == "RENAMED" and not touch.old_path:
                raise OwnershipInputError(
                    f"commit {record.sha} renames {touch.path} with no old_path"
                )


# ------------------------------------------------------------------ what drifter init proposes


def propose_ownership(
    head_sha: str,
    records: list[CommitRecord],
    *,
    window: int = WINDOW,
    max_files: int = MAX_FILES,
    bots: tuple[str, ...] = (),
    skip: tuple[str, ...] = SKIP,
) -> dict:
    # mines history into one rule per file: the path, and every author who changed it recently.
    # A file no author owns gets no rule, which leaves it open to anyone (spec 3.2).
    if window < 1:
        raise OwnershipInputError(f"window must be at least 1, got {window}")
    if max_files < 1:
        raise OwnershipInputError(f"max_files must be at least 1, got {max_files}")
    validate(head_sha, records)
    walked, newest = _walk(records)
    live = {
        path
        for path, change_type in newest.items()
        if change_type != "DELETED" and not _under(path, skip) and not path.startswith(MODELS)
    }
    owners = _owners(walked, live, window, max_files, bots)
    return {
        "rules": [
            # escapes the path, since rules are read as globs and "src/*.py" would claim its neighbours
            {"owners": sorted(owners[path]), "pattern": literal(path)}
            for path in sorted(live)
            if owners[path]
        ],
        "schema_version": SCHEMA_VERSION,
    }


def _under(path: str, folders: tuple[str, ...]) -> bool:
    # tells a path inside one of folders, matched at the root or any folder below it
    return any("/" + f.strip("/") + "/" in "/" + path for f in folders if f.strip("/"))


def _walk(records: list[CommitRecord]) -> tuple[list[tuple[CommitRecord, tuple[str, ...]]], dict[str, str]]:
    # resolves every changed path to the name it carries at head, walking newest first, and notes
    # each head name's newest change type; a rename moves the file's history onto its new name
    canonical: dict[str, str] = {}  # maps a path's older name to the name it has at head
    newest: dict[str, str] = {}  # maps a head name to the change type of its newest entry
    walked: list[tuple[CommitRecord, tuple[str, ...]]] = []
    for record in records:
        touched: list[str] = []
        for touch in record.paths:
            head_name = canonical.get(touch.path, touch.path)
            if touch.change_type == "RENAMED":
                # credits the file's older history to the name it carries at head
                canonical[touch.old_path] = head_name
            if head_name not in newest:
                newest[head_name] = touch.change_type
            if head_name not in touched:
                # counts a commit once per file, even where a rename names both its sides
                touched.append(head_name)
        walked.append((record, tuple(touched)))
    return walked, newest


def _owners(
    walked: list[tuple[CommitRecord, tuple[str, ...]]],
    live: set[str],
    window: int,
    max_files: int,
    bots: tuple[str, ...],
) -> dict[str, set[str]]:
    # names every author of each file's newest commits, up to the window; merges, bots and sweeps
    # name nobody, as none of the three says who looks after a file
    owners: dict[str, set[str]] = {path: set() for path in live}
    counted: dict[str, int] = {path: 0 for path in live}
    for record, touched in walked:
        if len(record.parents) > 1 or len(record.paths) > max_files or _is_bot(record.author_email, bots):
            continue
        for path in touched:
            if path in owners and counted[path] < window:
                counted[path] += 1
                owners[path].add(record.author_email.lower())
    return owners


def _is_bot(email: str, bots: tuple[str, ...]) -> bool:
    # tells a bot author, by GitHub's marker anywhere in the email or by the caller's list
    return BOT_MARK in email or email in bots


# ------------------------------------------------------------------------- what each push checks


def check_ownership(rules: dict, commits: list[CommitRecord]) -> list[dict]:
    # judges every non-merge commit: each file it changes must have its git author among the
    # owners of the first rule matching that path. A path no rule matches is open to anyone.
    # Returns the contract's OwnershipViolation objects, sorted by commit then path.
    patterns = [
        (rule["pattern"], tuple(owner.lower() for owner in rule["owners"])) for rule in rules.get("rules", ())
    ]
    violations: list[dict] = []
    for commit in commits:
        if len(commit.parents) > 1:
            # a merge is never judged, it carries no change of its own (spec 3.2)
            continue
        for path in _changed(commit):
            owners = _match(path, patterns)
            author = commit.author_email.lower()
            if owners is not None and author not in owners:
                violations.append({
                    "author": author,
                    "change": "VIOLATION",
                    "commit": commit.sha,
                    "owners": sorted(owners),
                    "path": path,
                })
    return sorted(violations, key=lambda v: (v["commit"], v["path"]))


def _changed(commit: CommitRecord) -> list[str]:
    # lists the paths one commit changes, each once and in path order; a rename counts under its
    # old path, so the owners travel with the file (spec 3.2)
    return sorted({touch.old_path if touch.change_type == "RENAMED" else touch.path for touch in commit.paths})


def _match(path: str, patterns: list[tuple[str, tuple[str, ...]]]) -> tuple[str, ...] | None:
    # returns the owners of the first rule matching path, None where no rule does; patterns use
    # the mapping-v1.1.yaml glob (spec 3.2)
    for pattern, owners in patterns:
        if glob(pattern).match(path):
            return owners
    return None

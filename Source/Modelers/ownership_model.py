# derives who owns each file of a repository from commit records, with no git, network or LLM

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

# names a scoring change, so a run says which derivation produced it even if the rules held still
MODEL_VERSION = "1.0.0"

# lists the change types the connector may report, an unknown one is a contract break
CHANGE_TYPES = frozenset({"ADDED", "MODIFIED", "DELETED", "RENAMED", "COPIED", "TYPE_CHANGED"})

# marks an author with no linked GitHub account, so their commits still count under a stable key
EMAIL_PREFIX = "email:"

# names a bot by convention, GitHub appends it to every app's login
BOT_SUFFIX = "[bot]"


class OwnershipInputError(Exception):
    # signals records that break the contract, naming the field and commit rather than failing deeper
    pass


@dataclass(frozen=True)
class PathTouch:
    # names one path a commit touched, old_path is set only for RENAMED
    path: str
    change_type: str
    old_path: str | None = None


@dataclass(frozen=True)
class CommitRecord:
    # describes one commit as the connector reports it, newest first across a run
    sha: str
    author_login: str | None
    author_email: str
    author_date: str
    parent_count: int
    paths: tuple[PathTouch, ...]


@dataclass(frozen=True)
class Rules:
    # holds one version of the rules file, config_version is its hash
    window: int
    max_files: int
    bots: frozenset[str]
    vendored: tuple[str, ...]
    config_version: str


def load_rules(rules_file: Path) -> Rules:
    # reads the rules, line endings normalised so a Windows checkout hashes the same
    raw = Path(rules_file).read_bytes().replace(b"\r\n", b"\n")
    data = json.loads(raw)
    return Rules(
        window=int(data["window"]),
        max_files=int(data["max_files"]),
        bots=frozenset(data.get("bots", [])),
        vendored=tuple(data.get("vendored", [])),
        config_version=hashlib.sha256(raw).hexdigest()[:12],
    )


def validate(head_sha: str, records: list[CommitRecord]) -> None:
    # rejects records that break the contract, so a changed connector fails loudly, never quietly
    if not records:
        raise OwnershipInputError("records is empty, expected at least the head commit")
    if records[0].sha != head_sha:
        raise OwnershipInputError(
            f"records[0].sha is {records[0].sha}, expected head {head_sha}; "
            "records must arrive newest first"
        )
    seen: set[str] = set()
    for record in records:
        if record.sha in seen:
            raise OwnershipInputError(f"commit {record.sha} appears twice in records")
        seen.add(record.sha)
        if record.parent_count < 0:
            raise OwnershipInputError(f"commit {record.sha} has parent_count {record.parent_count}")
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


def _vendored(path: str, vendored: tuple[str, ...]) -> bool:
    # tells a vendored path, each rule is a folder prefix matched at the root or any folder below
    return any("/" + rule in "/" + path for rule in vendored)


def _walk(records: list[CommitRecord]) -> tuple[list[tuple[CommitRecord, tuple[str, ...]]], dict[str, str]]:
    # resolves every touched path to the name it carries at head, walking newest first, and
    # notes each head name's most recent change type; renames are followed, nothing is filtered yet
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


def _rows(newest: dict[str, str], rules: Rules) -> set[str]:
    # keeps the paths that exist at head and are worth owning: no deletions, no vendored code
    return {
        path
        for path, change_type in newest.items()
        if change_type != "DELETED" and not _vendored(path, rules.vendored)
    }


@dataclass(frozen=True)
class Owner:
    # names one owner of a path and how many of its windowed commits they wrote
    key: str
    commits: int


@dataclass(frozen=True)
class PathOwnership:
    # reports one file's owners, ranked, empty where no commit survived the filters
    path: str
    window_total: int
    unresolved_commits: int
    owners: tuple[Owner, ...]


@dataclass(frozen=True)
class OwnershipModel:
    # holds one derivation, reproducible from the same head, records and rules
    model_version: str
    config_version: str
    head_commit: str
    paths: tuple[PathOwnership, ...]


def _author(record: CommitRecord) -> str:
    # names the author, falling back to their email where no GitHub account is linked
    return record.author_login or EMAIL_PREFIX + record.author_email.lower()


def _bot(key: str, rules: Rules) -> bool:
    # tells a bot, by GitHub's login convention or by the rules file's denylist
    if key.endswith(BOT_SUFFIX) or key in rules.bots:
        return True
    return key.startswith(EMAIL_PREFIX) and key[len(EMAIL_PREFIX):] in rules.bots


def _windows(
    walked: list[tuple[CommitRecord, tuple[str, ...]]], keep: set[str], rules: Rules
) -> dict[str, list[tuple[str, bool]]]:
    # collects each kept path's newest surviving commits, as (author key, author was resolved)
    windows: dict[str, list[tuple[str, bool]]] = {path: [] for path in keep}
    for record, touched in walked:
        key = _author(record)
        if record.parent_count > 1 or len(record.paths) > rules.max_files or _bot(key, rules):
            # a merge, a sweep or a bot confers no ownership, though its paths were still discovered
            continue
        for path in touched:
            window = windows.get(path)
            if window is not None and len(window) < rules.window:
                window.append((key, record.author_login is not None))
    return windows


def _rank(window: list[tuple[str, bool]]) -> tuple[Owner, ...]:
    # ranks a path's owners: most commits first, then whoever touched it most recently, then by key;
    # the three together are a total order, so the same window always ranks the same way
    commits: dict[str, int] = {}
    newest: dict[str, int] = {}
    for index, (key, _) in enumerate(window):
        commits[key] = commits.get(key, 0) + 1
        newest.setdefault(key, index)
    ordered = sorted(commits, key=lambda key: (-commits[key], newest[key], key))
    return tuple(Owner(key=key, commits=commits[key]) for key in ordered)


def derive(head_sha: str, records: list[CommitRecord], rules: Rules) -> OwnershipModel:
    # derives who owns each file at head from commit records given newest first; no clock,
    # random value or network reading enters, so the same inputs always give the same model
    validate(head_sha, records)
    walked, newest = _walk(records)
    keep = _rows(newest, rules)
    windows = _windows(walked, keep, rules)
    return OwnershipModel(
        model_version=MODEL_VERSION,
        config_version=rules.config_version,
        head_commit=head_sha,
        paths=tuple(
            PathOwnership(
                path=path,
                window_total=len(windows[path]),
                unresolved_commits=sum(1 for _, resolved in windows[path] if not resolved),
                owners=_rank(windows[path]),
            )
            for path in sorted(keep)
        ),
    )


def owners_of(model: OwnershipModel, path: str) -> tuple[Owner, ...]:
    # returns one path's ranked owners, empty for a path the model does not cover;
    # a documentation-to-code pair is two of these lookups
    for row in model.paths:
        if row.path == path:
            return row.owners
    return ()


def dump(model: OwnershipModel) -> bytes:
    # serialises a model the one way, so the same derivation always writes the same bytes;
    # escapes non-ASCII, as git reports an undecodable path with surrogates that UTF-8 refuses
    return json.dumps(
        asdict(model), ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")

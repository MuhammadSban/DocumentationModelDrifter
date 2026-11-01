# checks the ownership model against spec 3.2: the window, the folders that get no rule, the
# lowercase comparison and how a rename is judged

from models.ownership_model import (
    SKIP,
    VENDORED,
    WINDOW,
    CommitRecord,
    PathTouch,
    check_ownership,
    propose_ownership,
)


def _commit(sha, author, *paths, parents=("p",)):
    # one commit touching paths, each MODIFIED unless given as a (path, type, old) tuple
    touches = tuple(
        PathTouch(*p) if isinstance(p, tuple) else PathTouch(p, "MODIFIED") for p in paths
    )
    return CommitRecord(sha=sha, author_email=author, parents=parents, paths=touches)


def _history(author, path, count):
    # count commits by author over one path, newest first, head named "c0"
    return [_commit(f"c{i}", author, path, parents=(f"c{i + 1}",)) for i in range(count)]


def test_the_window_is_the_last_10_commits():
    assert WINDOW == 10
    # the 11th commit back names an owner who is outside the window
    records = _history("ana@x.com", "src/app.py", 10) + [_commit("c10", "old@x.com", "src/app.py")]

    rules = propose_ownership("c0", records)["rules"]

    assert rules == [{"owners": ["ana@x.com"], "pattern": "src/app.py"}]


def test_vendored_folders_get_no_rule_at_any_depth():
    assert VENDORED == ("vendor/", "third_party/", "node_modules/")
    paths = ["vendor/a.py", "src/vendor/b.py", "deep/third_party/c.py", "ui/node_modules/d.js"]
    records = [_commit("c0", "ana@x.com", *paths, "src/app.py")]

    rules = propose_ownership("c0", records)["rules"]

    assert [rule["pattern"] for rule in rules] == ["src/app.py"]


def test_only_the_root_models_folder_is_skipped():
    assert SKIP == ("models/",)
    records = [_commit("c0", "ana@x.com", "models/structural.json", "src/models/order.py")]

    rules = propose_ownership("c0", records)["rules"]

    # the repository's own src/models/ keeps its owners; only the folder init writes is skipped
    assert [rule["pattern"] for rule in rules] == ["src/models/order.py"]


def test_proposed_owners_are_lowercase():
    records = [_commit("c0", "Ana@X.com", "src/app.py")]

    rules = propose_ownership("c0", records)["rules"]

    assert rules == [{"owners": ["ana@x.com"], "pattern": "src/app.py"}]


def test_an_author_is_compared_with_the_owners_in_lowercase():
    # a hand-written rule may name an owner in any case, and so may a commit's author
    rules = {"rules": [{"owners": ["Ana@X.com"], "pattern": "src/app.py"}], "schema_version": 1}

    assert check_ownership(rules, [_commit("c0", "ANA@x.COM", "src/app.py")]) == []


def test_a_rename_is_judged_under_its_old_path_only():
    rules = {"rules": [{"owners": ["ana@x.com"], "pattern": "src/old.py"}], "schema_version": 1}
    moved = ("src/new.py", "RENAMED", "src/old.py")

    # the owner may move their own file, even to a path no rule covers
    assert check_ownership(rules, [_commit("c0", "ana@x.com", moved)]) == []

    # a non-owner cannot move it out from under the rule
    violations = check_ownership(rules, [_commit("c0", "bob@x.com", moved)])
    assert [(v["author"], v["owners"], v["path"]) for v in violations] == [
        ("bob@x.com", ["ana@x.com"], "src/old.py")
    ]


def test_a_merge_is_never_judged():
    rules = {"rules": [{"owners": ["ana@x.com"], "pattern": "src/app.py"}], "schema_version": 1}
    merge = _commit("c0", "bob@x.com", "src/app.py", parents=("p1", "p2"))

    assert check_ownership(rules, [merge]) == []

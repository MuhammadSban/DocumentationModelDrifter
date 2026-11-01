# checks the ownership model against spec 3.2, docs/models/model-seam.md and docs/models/comparison.md

from models.ownership_model import CommitRecord, PathTouch, check_ownership, propose_ownership


def history(*commits):
    # builds records newest first, each commit the parent of the one before it: (email, [paths])
    shas = [f"{i:040x}" for i in range(len(commits), 0, -1)]
    records = []
    for i, (email, paths) in enumerate(commits):
        parents = (shas[i + 1],) if i + 1 < len(shas) else ()
        records.append(CommitRecord(shas[i], email, parents, tuple(PathTouch(p, "MODIFIED") for p in paths)))
    return shas[0], records


def rules(*pairs):
    # builds an ownership.json from (pattern, owners) pairs
    return {"rules": [{"owners": owners, "pattern": pattern} for pattern, owners in pairs], "schema_version": 1}


def test_rules_use_the_pattern_key():
    head, records = history(("a@x.com", ["src/app.py"]))
    assert propose_ownership(head, records)["rules"] == [{"owners": ["a@x.com"], "pattern": "src/app.py"}]


def test_window_is_the_last_10_commits_of_a_file():
    head, records = history(*[(f"u{i}@x.com", ["src/app.py"]) for i in range(11)])
    owners = propose_ownership(head, records)["rules"][0]["owners"]
    assert owners == sorted(f"u{i}@x.com" for i in range(10))


def test_vendored_files_get_no_rule_at_any_depth():
    head, records = history(("a@x.com", ["vendor/x.py", "lib/third_party/y.py", "web/node_modules/z.js", "src/app.py"]))
    assert [r["pattern"] for r in propose_ownership(head, records)["rules"]] == ["src/app.py"]


def test_only_the_root_models_folder_is_skipped():
    head, records = history(("a@x.com", ["models/scope.json", "src/models/order.py"]))
    assert [r["pattern"] for r in propose_ownership(head, records)["rules"]] == ["src/models/order.py"]


def test_proposed_owners_are_lowercase():
    head, records = history(("Kaan@X.com", ["src/app.py"]))
    assert propose_ownership(head, records)["rules"][0]["owners"] == ["kaan@x.com"]


def test_check_compares_emails_in_lowercase():
    commit = CommitRecord("a" * 40, "Kaan@X.com", ("b" * 40,), (PathTouch("src/app.py", "MODIFIED"),))
    assert check_ownership(rules(("src/app.py", ["kaan@x.com"])), [commit]) == []
    assert check_ownership(rules(("src/app.py", ["KAAN@x.com"])), [commit]) == []


def test_a_rename_is_judged_under_its_old_path_only():
    move = PathTouch("src/new.py", "RENAMED", "src/old.py")
    owned = rules(("src/old.py", ["owner@x.com"]), ("src/new.py", ["other@x.com"]))
    by_owner = CommitRecord("a" * 40, "owner@x.com", ("b" * 40,), (move,))
    by_stranger = CommitRecord("c" * 40, "stranger@x.com", ("b" * 40,), (move,))
    assert check_ownership(owned, [by_owner]) == []
    assert [v["path"] for v in check_ownership(owned, [by_stranger])] == ["src/old.py"]

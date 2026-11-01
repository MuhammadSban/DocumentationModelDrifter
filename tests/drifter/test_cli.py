# checks drifter check on a local checkout: the four-field answer as canonical JSON, exit 0 on
# no drift and 1 on drift, and the diff by id through a fake generator (issue #14)

import json
import subprocess

import pytest

from drifter import check, cli
from models.common import write_model
from models.structural_model import generate_structural

CODE = {"src/app.py": "def charge(amount):\n    return amount\n"}
SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}
NO_RULES = {"rules": [], "schema_version": 1}


def _repo(path, files, behavioral=None):
    # commits files and four /models files that match them, so the check starts aligned
    models = {
        "models/behavioral.json": behavioral or {"schema_version": 1},
        "models/ownership.json": NO_RULES,
        "models/scope.json": SCOPE,
        "models/structural.json": generate_structural(files),
    }
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    for name, text in {**files, **{k: write_model(v) for k, v in models.items()}}.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_bytes(text.encode())
    _commit(path, "first")
    return path


def _commit(path, message):
    # commits everything in the work tree as one scripted author
    git = ["git", "-C", str(path), "-c", "user.email=ana@x.com", "-c", "user.name=ana"]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", message], check=True)


def _check(path, monkeypatch, capsysbinary, *args):
    # runs drifter check in path and returns its exit code and stdout bytes
    monkeypatch.chdir(path)
    code = cli.main(["check", *args])
    return code, capsysbinary.readouterr().out


def test_an_aligned_checkout_prints_the_answer_and_exits_0(tmp_path, monkeypatch, capsysbinary):
    repo = _repo(tmp_path, CODE)

    code, out = _check(repo, monkeypatch, capsysbinary)

    assert code == 0
    assert out == b'{\n  "aligned": true,\n  "behavioral": [],\n  "ownership": [],\n  "structural": []\n}\n'


def test_new_code_is_drift_and_exits_1(tmp_path, monkeypatch, capsysbinary):
    repo = _repo(tmp_path, CODE)
    (repo / "src" / "app.py").write_text(CODE["src/app.py"] + "\n\ndef refund(amount):\n    return -amount\n")
    _commit(repo, "add refund")

    code, out = _check(repo, monkeypatch, capsysbinary)

    assert code == 1
    assert json.loads(out)["structural"] == [
        {"change": "ADDED", "file": "src/app.py", "id": "app:refund", "kind": "function"},
    ]


# ------------------------------------------------- the diff by id, through a fake behavioral plugin

# commits a behavioral model in the owner's own list names; schema_version is not an element
COMMITTED = {
    "schema_version": 1,
    "states": [
        {"file": "src/app.py", "id": "Order.open", "kind": "state"},
        {"file": "src/app.py", "id": "Order.paid", "kind": "state"},
    ],
    "transitions": [
        {"file": "src/app.py", "id": "Order.open->paid", "kind": "transition", "on": "pay"},
    ],
}


def _behavioral(tmp_path, monkeypatch, capsysbinary, fresh):
    # registers a fake behavioral generator returning fresh, then checks a repo committing COMMITTED
    monkeypatch.setitem(check.GENERATORS, "behavioral", lambda files: fresh)
    code, out = _check(_repo(tmp_path, CODE, COMMITTED), monkeypatch, capsysbinary)
    return code, json.loads(out)


def test_a_fake_plugin_matching_the_model_reports_no_change(tmp_path, monkeypatch, capsysbinary):
    code, answer = _behavioral(tmp_path, monkeypatch, capsysbinary, {**COMMITTED, "schema_version": 2})

    assert code == 0
    assert answer["behavioral"] == []


def test_an_element_only_in_the_code_is_added(tmp_path, monkeypatch, capsysbinary):
    shipped = {"file": "src/ship.py", "id": "Order.shipped", "kind": "state"}
    fresh = {**COMMITTED, "states": [*COMMITTED["states"], shipped]}

    code, answer = _behavioral(tmp_path, monkeypatch, capsysbinary, fresh)

    assert code == 1
    assert answer["behavioral"] == [
        {"change": "ADDED", "file": "src/ship.py", "id": "Order.shipped", "kind": "state"},
    ]


def test_an_element_only_in_the_model_is_removed(tmp_path, monkeypatch, capsysbinary):
    fresh = {**COMMITTED, "transitions": []}

    code, answer = _behavioral(tmp_path, monkeypatch, capsysbinary, fresh)

    assert code == 1
    assert answer["behavioral"] == [
        {"change": "REMOVED", "file": "src/app.py", "id": "Order.open->paid", "kind": "transition"},
    ]


def test_an_element_whose_fields_differ_is_modified_with_the_fresh_file_and_kind(tmp_path, monkeypatch, capsysbinary):
    moved = {"file": "src/pay.py", "id": "Order.open->paid", "kind": "event", "on": "charge"}
    fresh = {**COMMITTED, "transitions": [moved]}

    code, answer = _behavioral(tmp_path, monkeypatch, capsysbinary, fresh)

    assert code == 1
    assert answer["behavioral"] == [
        {"change": "MODIFIED", "file": "src/pay.py", "id": "Order.open->paid", "kind": "event"},
    ]


def test_differences_are_sorted_by_id_across_lists(tmp_path, monkeypatch, capsysbinary):
    fresh = {
        "schema_version": 1,
        "states": [{"file": "src/app.py", "id": "B", "kind": "state"}],
        "transitions": [{"file": "src/app.py", "id": "A", "kind": "transition"}],
    }

    _, answer = _behavioral(tmp_path, monkeypatch, capsysbinary, fresh)

    assert [d["id"] for d in answer["behavioral"]] == ["A", "B", "Order.open", "Order.open->paid", "Order.paid"]


def test_two_runs_print_the_same_bytes(tmp_path, monkeypatch, capsysbinary):
    repo = _repo(tmp_path, CODE)
    (repo / "src" / "app.py").write_text("class Order:\n    pass\n")
    _commit(repo, "replace charge")

    first = _check(repo, monkeypatch, capsysbinary)
    second = _check(repo, monkeypatch, capsysbinary)

    assert first[0] == 1
    assert first == second

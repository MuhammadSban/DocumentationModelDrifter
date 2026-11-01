# checks drifter check on a local checkout: the four-field answer as canonical JSON, exit 0 on
# no drift and 1 on drift, and the diff by id through a fake generator (issue #14)

import json
import subprocess
import sys
import tomllib
from pathlib import Path

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


def test_a_repeated_id_in_a_committed_model_gives_no_verdict(tmp_path, monkeypatch, capsysbinary):
    twice = {**COMMITTED, "transitions": [{"file": "src/app.py", "id": "Order.open", "kind": "transition"}]}

    code, out = _check(_repo(tmp_path, CODE, twice), monkeypatch, capsysbinary)

    assert code == 2
    error = json.loads(out)["drift_error"]
    assert error["code"] == "INVALID_MODELS"
    assert "models/behavioral.json" in error["message"] and "Order.open" in error["message"]


def test_the_drifter_script_runs_check_without_fastapi(tmp_path):
    # runs pyproject's drifter target as its console script would, in a clean interpreter
    root = Path(__file__).resolve().parents[2]
    target = tomllib.loads((root / "pyproject.toml").read_text())["project"]["scripts"]["drifter"]
    module, function = target.split(":")
    script = (
        f"import sys; sys.path.insert(0, {str(root / 'Source')!r}); sys.modules['fastapi'] = None\n"
        f"sys.argv = ['drifter', 'check']\n"
        f"from {module} import {function}; sys.exit({function}())"
    )
    repo = _repo(tmp_path, CODE)

    proc = subprocess.run([sys.executable, "-I", "-c", script], cwd=repo, capture_output=True)

    assert proc.returncode == 0, proc.stderr.decode()
    assert json.loads(proc.stdout)["aligned"] is True


# ------------------------------------------- no verdict: the four drift_error codes, exit 2 (#15)

# holds exactly the size limit: a comment line padded to 1,048,576 bytes
LIMIT = b"#" * (1024 * 1024 - 1) + b"\n"


def _no_verdict(path, monkeypatch, capsysbinary, files, models=None):
    # commits files and the models CODE deserves, models overriding (None removes one), then
    # checks through the entry point and the CLI and returns the CLI's drift_error
    repo = _repo(path, CODE)
    for name, text in {**files, **(models or {})}.items():
        target = repo / name
        if text is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text if isinstance(text, bytes) else text.encode())
    _commit(repo, "break it")
    try:
        check.local_sources(repo)
        raised = None
    except check.DriftError as exc:
        raised = exc.body()
    code, out = _check(repo, monkeypatch, capsysbinary)
    body = json.loads(out)
    assert code == 2
    assert body["drift"] is None
    assert body["drift_error"] == raised
    return body["drift_error"]


def test_no_models_folder_is_models_not_found(tmp_path, monkeypatch, capsysbinary):
    gone = {f"models/{name}": None for name in check.MODEL_FILES}

    error = _no_verdict(tmp_path, monkeypatch, capsysbinary, {}, gone)

    assert error["code"] == "MODELS_NOT_FOUND"


def test_one_missing_model_file_is_models_not_found(tmp_path, monkeypatch, capsysbinary):
    error = _no_verdict(tmp_path, monkeypatch, capsysbinary, {}, {"models/ownership.json": None})

    assert error["code"] == "MODELS_NOT_FOUND"
    assert "models/ownership.json" in error["message"]


ELEMENT = {"file": "src/app.py", "id": "A", "kind": "state"}


@pytest.mark.parametrize(
    "name, text",
    [
        pytest.param("structural.json", "{not json", id="bad-json"),
        pytest.param("behavioral.json", write_model({"states": [ELEMENT, ELEMENT]}), id="duplicate-id"),
        pytest.param("behavioral.json", write_model({"states": [{"id": "A", "kind": "state"}]}), id="missing-file"),
        pytest.param("behavioral.json", write_model({"states": ["A"]}), id="element-not-object"),
        pytest.param("structural.json", "[]\n", id="model-not-object"),
        pytest.param("scope.json", write_model({"include": "**/*.py"}), id="scope-not-list"),
        pytest.param("scope.json", "[]\n", id="scope-not-object"),
        pytest.param("ownership.json", "[]\n", id="ownership-not-object"),
        pytest.param("ownership.json", write_model({"rules": "src/**"}), id="rules-not-list"),
        pytest.param("ownership.json", write_model({"rules": ["src/**"]}), id="rule-not-object"),
        pytest.param("ownership.json", write_model({"rules": [{"pattern": "src/**"}]}), id="rule-without-owners"),
        pytest.param("ownership.json", write_model({"rules": [{"owners": ["ana@x.com"]}]}), id="rule-without-pattern"),
    ],
)
def test_a_bad_model_file_is_invalid_models_naming_it(tmp_path, monkeypatch, capsysbinary, name, text):
    error = _no_verdict(tmp_path, monkeypatch, capsysbinary, {}, {f"models/{name}": text})

    assert error["code"] == "INVALID_MODELS"
    assert f"models/{name}" in error["message"]


def test_one_byte_over_1_mb_is_file_too_large(tmp_path, monkeypatch, capsysbinary):
    error = _no_verdict(tmp_path, monkeypatch, capsysbinary, {"src/big.py": LIMIT + b"\n"})

    assert error == {"code": "FILE_TOO_LARGE", "message": "src/big.py is 1048577 bytes, over 1 MB"}


def test_exactly_1_mb_passes(tmp_path, monkeypatch, capsysbinary):
    repo = _repo(tmp_path, {**CODE, "src/big.py": LIMIT.decode()})

    code, _ = _check(repo, monkeypatch, capsysbinary)

    assert code == 0


@pytest.mark.parametrize(
    "data, words",
    [
        pytest.param(b"def f(:\n", ["src/bad.py", "line 1"], id="syntax"),
        pytest.param("name = 'café'\n".encode("latin-1"), ["src/bad.py", "UTF-8"], id="latin-1"),
        pytest.param(b"x = 1\x00\n", ["src/bad.py", "null byte"], id="null-byte"),
    ],
)
def test_an_unreadable_file_is_parse_failed_naming_it(tmp_path, monkeypatch, capsysbinary, data, words):
    error = _no_verdict(tmp_path, monkeypatch, capsysbinary, {"src/bad.py": data})

    assert error["code"] == "PARSE_FAILED"
    assert all(word in error["message"] for word in words)


def test_of_two_bad_files_the_first_in_path_order_wins_every_run(tmp_path, monkeypatch, capsysbinary):
    # a syntax error in src/a.py comes before a too-large src/b.py, though size is judged first
    bad = {"src/a.py": b"def f(:\n", "src/b.py": LIMIT + b"\n"}

    first = _no_verdict(tmp_path / "one", monkeypatch, capsysbinary, bad)
    second = _no_verdict(tmp_path / "two", monkeypatch, capsysbinary, bad)

    assert first["code"] == "PARSE_FAILED" and "src/a.py" in first["message"]
    assert first == second

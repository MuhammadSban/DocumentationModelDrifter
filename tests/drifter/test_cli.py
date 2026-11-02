# checks drifter check on a local checkout: the four-field answer as canonical JSON, exit 0 on
# no drift and 1 on drift, and the diff by id through a fake generator (issue #14); ownership
# violations on scripted-author repos (#16)

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


def _repo(path, files, behavioral=None, ownership=NO_RULES):
    # commits files and four /models files that match them, so the check starts aligned
    models = {
        "models/behavioral.json": behavioral or {"schema_version": 1},
        "models/ownership.json": ownership,
        "models/scope.json": SCOPE,
        "models/structural.json": generate_structural(files),
    }
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    for name, text in {**files, **{k: write_model(v) for k, v in models.items()}}.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_bytes(text.encode())
    _commit(path, "first")
    return path


def _git(path, author):
    # builds a git command prefix that acts as one scripted author
    return ["git", "-C", str(path), "-c", f"user.email={author}", "-c", f"user.name={author.split('@')[0]}"]


def _commit(path, message, author="ana@x.com"):
    # commits everything in the work tree as one scripted author
    git = _git(path, author)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", message], check=True)


def _check(path, monkeypatch, capsysbinary, *args):
    # runs drifter check in path and returns its exit code and stdout bytes
    return _run(path, monkeypatch, capsysbinary, "check", *args)


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

# passes the element rule but breaks structural.schema.json: an edge kind structure.md does not have
STRUCTURAL = generate_structural(CODE)
UNKNOWN_EDGE = {**STRUCTURAL, "edges": [{"file": "src/app.py", "id": "calls:app->app", "kind": "calls",
                                         "source": "app", "target": "app"}]}


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
        pytest.param("structural.json", write_model(UNKNOWN_EDGE), id="structural-schema-unknown-edge-kind"),
        pytest.param("structural.json", write_model({**STRUCTURAL, "schema_version": 2}), id="structural-schema-version"),
        pytest.param("structural.json", write_model({**STRUCTURAL, "calls": []}), id="structural-schema-unknown-key"),
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


# ------------------------------------------ ownership: each non-merge commit judged by its author (#16)


def _owned(path, *rules):
    # commits CODE with ownership rules given as (pattern, owners) pairs, as ana
    return _repo(path, CODE, ownership={"rules": [{"owners": o, "pattern": p} for p, o in rules], "schema_version": 1})


def _append(repo, name, line):
    # appends one line to a file, creating it and its folders when missing
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a") as f:
        f.write(f"{line}\n")


def _edit(repo, name, author, line="edit"):
    # appends a line to one file and commits it as author, returning the new commit's sha
    _append(repo, name, line)
    _commit(repo, "edit", author)
    return _sha(repo)


def _sha(repo, rev="HEAD"):
    # returns the full sha of one revision
    proc = subprocess.run(["git", "-C", str(repo), "rev-parse", rev], capture_output=True, check=True, text=True)
    return proc.stdout.strip()


def _ownership(repo, monkeypatch, capsysbinary, *args):
    # runs drifter check and returns its exit code and the ownership list
    code, out = _check(repo, monkeypatch, capsysbinary, *args)
    return code, json.loads(out)["ownership"]


def test_a_non_owners_commit_is_one_violation_naming_them_in_lowercase(tmp_path, monkeypatch, capsysbinary):
    repo = _owned(tmp_path, ("docs/guide.md", ["bea@x.com"]))
    sha = _edit(repo, "docs/guide.md", "Zed@X.com")

    code, ownership = _ownership(repo, monkeypatch, capsysbinary)

    assert code == 1
    assert ownership == [
        {
            "author": "zed@x.com", "change": "VIOLATION", "commit": sha,
            "owners": ["bea@x.com"], "path": "docs/guide.md",
        },
    ]


def test_an_owners_commit_is_no_violation(tmp_path, monkeypatch, capsysbinary):
    repo = _owned(tmp_path, ("docs/guide.md", ["bea@x.com"]))
    _edit(repo, "docs/guide.md", "bea@x.com")

    assert _ownership(repo, monkeypatch, capsysbinary) == (0, [])


def test_a_merge_commit_is_not_judged(tmp_path, monkeypatch, capsysbinary):
    # judges only the side branch's own commit, not zed's merge of it into main
    repo = _owned(tmp_path, ("docs/**", ["bea@x.com"]))
    git = _git(repo, "zed@x.com")
    subprocess.run([*git, "checkout", "-q", "-b", "side"], check=True)
    side = _edit(repo, "docs/side.md", "zed@x.com")
    subprocess.run([*git, "checkout", "-q", "main"], check=True)
    _edit(repo, "docs/main.md", "bea@x.com")
    subprocess.run([*git, "merge", "-q", "--no-ff", "-m", "merge", "side"], check=True)

    _, ownership = _ownership(repo, monkeypatch, capsysbinary)

    assert [(v["commit"], v["path"]) for v in ownership] == [(side, "docs/side.md")]


def test_a_rename_is_judged_under_its_old_path_only(tmp_path, monkeypatch, capsysbinary):
    # gives one violation under the old name only, though bea owns both names
    repo = _owned(tmp_path, ("docs/old.md", ["bea@x.com"]), ("docs/new.md", ["bea@x.com"]))
    _edit(repo, "docs/old.md", "bea@x.com", "a line long enough for git to see the same file after the move")
    subprocess.run(["git", "-C", str(repo), "mv", "docs/old.md", "docs/new.md"], check=True)
    _commit(repo, "move", "zed@x.com")

    _, ownership = _ownership(repo, monkeypatch, capsysbinary)

    assert [(v["path"], v["author"]) for v in ownership] == [("docs/old.md", "zed@x.com")]


def test_a_path_with_no_rule_is_open_to_anyone(tmp_path, monkeypatch, capsysbinary):
    repo = _owned(tmp_path, ("docs/**", ["bea@x.com"]))
    _edit(repo, "notes.txt", "zed@x.com")

    assert _ownership(repo, monkeypatch, capsysbinary) == (0, [])


def test_of_two_matching_rules_the_first_wins(tmp_path, monkeypatch, capsysbinary):
    # applies bea's first rule, so zed's ownership by the second rule never counts
    repo = _owned(tmp_path, ("docs/**", ["bea@x.com"]), ("docs/a.md", ["zed@x.com"]))
    _edit(repo, "docs/a.md", "zed@x.com")

    _, ownership = _ownership(repo, monkeypatch, capsysbinary)

    assert [(v["path"], v["owners"]) for v in ownership] == [("docs/a.md", ["bea@x.com"])]


def test_a_mixed_case_author_matches_a_lowercase_owner(tmp_path, monkeypatch, capsysbinary):
    repo = _owned(tmp_path, ("docs/**", ["bea@x.com"]))
    _edit(repo, "docs/a.md", "Bea@X.com")

    assert _ownership(repo, monkeypatch, capsysbinary) == (0, [])


def test_violations_sort_by_commit_then_path_and_ignore_scope(tmp_path, monkeypatch, capsysbinary):
    # judges tests/ and docs/ though scope.json excludes the one and never includes the other
    repo = _owned(tmp_path, ("**", ["cal@x.com", "bea@x.com"]))
    base = _sha(repo)
    for message in ("one", "two"):
        for name in ("tests/test_z.py", "docs/a.md"):
            _append(repo, name, f"{message} = 1")
        _commit(repo, message, "zed@x.com")
    one, two = _sha(repo, "HEAD~1"), _sha(repo)

    _, ownership = _ownership(repo, monkeypatch, capsysbinary, "--base", base)

    first, second = sorted([one, two])
    assert [(v["commit"], v["path"]) for v in ownership] == [
        (first, "docs/a.md"), (first, "tests/test_z.py"), (second, "docs/a.md"), (second, "tests/test_z.py"),
    ]
    assert all(v["owners"] == ["bea@x.com", "cal@x.com"] for v in ownership)


def test_the_default_base_judges_the_head_commit_only(tmp_path, monkeypatch, capsysbinary):
    repo = _owned(tmp_path, ("docs/**", ["bea@x.com"]))
    _edit(repo, "docs/a.md", "zed@x.com", "earlier")
    head = _edit(repo, "docs/b.md", "zed@x.com", "later")

    _, ownership = _ownership(repo, monkeypatch, capsysbinary)

    assert [(v["commit"], v["path"]) for v in ownership] == [(head, "docs/b.md")]


def test_a_root_commit_judges_only_itself(tmp_path, monkeypatch, capsysbinary):
    # judges ana's root commit, which adds bea's src/app.py, and not zed's later commit
    repo = _owned(tmp_path, ("src/app.py", ["bea@x.com"]), ("docs/**", ["bea@x.com"]))
    root = _sha(repo)
    _edit(repo, "docs/a.md", "zed@x.com")

    _, ownership = _ownership(repo, monkeypatch, capsysbinary, root)

    assert ownership == [
        {"author": "ana@x.com", "change": "VIOLATION", "commit": root, "owners": ["bea@x.com"], "path": "src/app.py"},
    ]


# ---------------------------------------------------------------- drifter init and update (#17)


def _code_repo(path, files):
    # commits only code, no /models, as a repository looks before init
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_bytes(text.encode())
    _commit(path, "first")
    return path


def _run(path, monkeypatch, capsysbinary, *args):
    # runs one drifter command in path and returns its exit code and stdout bytes
    monkeypatch.chdir(path)
    code = cli.main(list(args))
    return code, capsysbinary.readouterr().out


def test_init_writes_four_canonical_files(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)

    code, _ = _run(repo, monkeypatch, capsysbinary, "init")

    assert code == 0
    written = {p.name: p.read_bytes() for p in (repo / "models").iterdir()}
    assert written == {
        "behavioral.json": b'{\n  "schema_version": 1,\n  "states": [],\n  "transitions": []\n}\n',
        "ownership.json": b'{\n  "rules": [\n    {\n      "owners": [\n        "ana@x.com"\n      ],\n'
        b'      "pattern": "src/app.py"\n    }\n  ],\n  "schema_version": 1\n}\n',
        "scope.json": b'{\n  "exclude": [\n    "tests/**"\n  ],\n  "include": [\n    "**/*.py"\n  ]\n}\n',
        "structural.json": write_model(generate_structural(CODE)).encode(),
    }


def test_init_then_commit_checks_aligned(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, {**CODE, "tests/test_app.py": "def test_x():\n    pass\n"})
    _run(repo, monkeypatch, capsysbinary, "init")
    _commit(repo, "add models")

    code, _ = _run(repo, monkeypatch, capsysbinary, "check")

    assert code == 0


def test_init_refuses_existing_models_unless_forced(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)
    (repo / "models").mkdir()
    (repo / "models" / "scope.json").write_bytes(b"hand made\n")

    refused, _ = _run(repo, monkeypatch, capsysbinary, "init")
    kept = (repo / "models" / "scope.json").read_bytes()
    forced, _ = _run(repo, monkeypatch, capsysbinary, "init", "--force")

    assert (refused, kept) == (1, b"hand made\n")
    assert forced == 0
    assert (repo / "models" / "scope.json").read_bytes() == write_model(SCOPE).encode()


def test_two_inits_give_identical_bytes(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)
    _run(repo, monkeypatch, capsysbinary, "init")
    first = {p.name: p.read_bytes() for p in (repo / "models").iterdir()}

    _run(repo, monkeypatch, capsysbinary, "init", "--force")

    assert {p.name: p.read_bytes() for p in (repo / "models").iterdir()} == first


def test_init_from_a_subfolder_writes_the_top_level_models(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)

    code, _ = _run(repo / "src", monkeypatch, capsysbinary, "init")

    assert code == 0
    assert sorted(p.name for p in (repo / "models").iterdir()) == list(check.MODEL_FILES)
    assert not (repo / "src" / "models").exists()


def test_update_accepts_drift_and_keeps_hand_edits(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)
    _run(repo, monkeypatch, capsysbinary, "init")
    ownership = b'{"rules": [{"pattern": "src/**", "owners": ["ana@x.com", "bo@x.com"]}], "schema_version": 1}'
    scope = b'{"include": ["**/*.py"], "exclude": ["tests/**", "docs/**"]}'
    (repo / "models" / "ownership.json").write_bytes(ownership)
    (repo / "models" / "scope.json").write_bytes(scope)
    (repo / "src" / "app.py").write_text(CODE["src/app.py"] + "\n\ndef refund(amount):\n    return -amount\n")
    _commit(repo, "add refund and hand-edit models")
    drifted, _ = _run(repo, monkeypatch, capsysbinary, "check")

    code, _ = _run(repo, monkeypatch, capsysbinary, "update")
    _commit(repo, "accept refund")
    aligned, _ = _run(repo, monkeypatch, capsysbinary, "check")

    assert (drifted, code, aligned) == (1, 0, 0)
    assert (repo / "models" / "ownership.json").read_bytes() == ownership
    assert (repo / "models" / "scope.json").read_bytes() == scope


# --------------------------------------------------------------- the behavioral model (#31)

MACHINE = {"src/order.py": (
    "class Order:\n"
    "    def advance(self):\n"
    "        if self.status == 'open':\n"
    "            self.status = 'paid'\n"
)}

# adds one elif moving self.status to a new string state, with no structural change
NEW_STATE = MACHINE["src/order.py"] + (
    "        elif self.status == 'paid':\n"
    "            self.status = 'shipped'\n"
)


def test_a_new_elif_state_is_one_added_state_and_one_added_transition(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, MACHINE)
    _run(repo, monkeypatch, capsysbinary, "init")
    _commit(repo, "add models")
    (repo / "src" / "order.py").write_text(NEW_STATE)
    _commit(repo, "ship paid orders")

    code, out = _check(repo, monkeypatch, capsysbinary)

    assert code == 1
    answer = json.loads(out)
    assert (answer["structural"], answer["ownership"]) == ([], [])
    assert answer["behavioral"] == [
        {"change": "ADDED", "file": "src/order.py", "kind": "state",
         "id": 'state:["src/order.py","order:Order","self.status","shipped"]'},
        {"change": "ADDED", "file": "src/order.py", "kind": "transition",
         "id": 'transition:["src/order.py","order:Order.advance",'
               '"state:[\\"src/order.py\\",\\"order:Order\\",\\"self.status\\",\\"paid\\"]",'
               '"state:[\\"src/order.py\\",\\"order:Order\\",\\"self.status\\",\\"shipped\\"]"]'},
    ]


def test_update_regenerates_behavioral_as_init_writes_it(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, MACHINE)
    _run(repo, monkeypatch, capsysbinary, "init")
    _commit(repo, "add models")
    (repo / "src" / "order.py").write_text(NEW_STATE)
    _commit(repo, "ship paid orders")
    _run(repo, monkeypatch, capsysbinary, "init", "--force")
    initialised = (repo / "models" / "behavioral.json").read_bytes()
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--", "models"], check=True)

    code, _ = _run(repo, monkeypatch, capsysbinary, "update")

    assert code == 0
    assert (repo / "models" / "behavioral.json").read_bytes() == initialised
    assert b'"shipped"' in initialised


def test_update_replaces_a_broken_structural_model(tmp_path, monkeypatch, capsysbinary):
    repo = _code_repo(tmp_path, CODE)
    _run(repo, monkeypatch, capsysbinary, "init")
    (repo / "models" / "structural.json").write_bytes(b"not json")
    _commit(repo, "break structural.json")

    code, _ = _run(repo, monkeypatch, capsysbinary, "update")

    assert code == 0
    assert (repo / "models" / "structural.json").read_bytes() == write_model(generate_structural(CODE)).encode()


def test_the_package_installs_the_schema_validator_and_ships_the_schemas():
    # pins what pip install -e . gives the CLI, so it validates as the service does
    pyproject = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text())

    assert "jsonschema" in pyproject["project"]["dependencies"]
    assert "*.schema.json" in pyproject["tool"]["setuptools"]["package-data"]["models"]

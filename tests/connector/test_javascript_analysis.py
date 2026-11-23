# checks mixed-language extraction through the hosted entry points and shared core

import json
import subprocess
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from drifter import check, cli
from Frontend import model_drift
from GitHub_Connector import analysis, api
from GitHub_Connector.settings import get_settings

PYTHON = "def python_task(value): return value\n"
JAVASCRIPT = "export class Order {pay(){if(this.status==='open')this.status='paid';}} export const charge=(amount)=>amount;"
REQUEST = {"repository": "owner/repo", "commit_id": "a" * 40}


class Reader:
    head = "a" * 40
    base = None
    changes = []
    skipped = []

    def __init__(self, files):
        self.files = {path: text.encode() if isinstance(text, str) else text for path, text in files.items()}
        self.author = "ana@x.com"

    def tree(self):
        return {path: path for path in self.files}

    def tree_at(self, commit):
        return self.tree()

    def read(self, paths, commit=None):
        return {path: self.files[path] for path in paths}

    def history(self):
        entries = "".join("A\0" + path + "\0" for path in sorted(self.files))
        return "\x01" + self.head + "\x1f" + self.author + "\x1f\0" + entries

    def log(self):
        return self.history()

    def commit_models(self):
        for name, text in check.generate_models(self, verbosity=None).items():
            self.files["models/" + name] = text.encode()


@pytest.fixture
def served(tmp_path, monkeypatch):
    reader = Reader({"src/app.py": PYTHON, "src/order.js": JAVASCRIPT})

    @contextmanager
    def fake_fetch(*args, **kwargs):
        yield reader

    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(api, "fetch", fake_fetch)
    monkeypatch.setenv("DRIFTER_RUNS_DIR", str(tmp_path / "runs"))
    get_settings.cache_clear()
    yield reader, TestClient(api.app)
    get_settings.cache_clear()


def test_generate_includes_python_javascript_behavior_and_ownership(served):
    _, client = served
    response = client.post("/system/generate", json=REQUEST)
    assert response.status_code == 200
    files = {name: json.loads(text) for name, text in response.json()["files"].items()}
    modules = {n["id"] for n in files["structural.json"]["nodes"] if n["kind"] == "module"}
    assert modules == {"app", "./src/order.js"}
    assert len(files["behavioral.json"]["transitions"]) == 1
    assert {r["pattern"] for r in files["ownership.json"]["rules"]} == {"src/app.py", "src/order.js"}
    assert "**/*.js" in files["scope.json"]["include"]


def test_analyze_matches_the_same_pure_core_answer(served):
    reader, client = served
    reader.commit_models()
    expected = check.answer(check.read_sources(reader))
    response = client.post("/system/analyze", json=REQUEST)
    assert response.status_code == 200
    assert response.json()["drift"] == expected == {"aligned": True, "behavioral": [], "ownership": [], "structural": []}
    assert response.json()["drift_error"] is None
    assert client.get("/system/analysis/" + response.json()["analysis_id"]).content == response.content


def test_javascript_signature_drift_is_reported(served):
    reader, client = served
    reader.commit_models()
    reader.files["src/order.js"] = JAVASCRIPT.replace("(amount)", "(amount, currency)").encode()
    body = client.post("/system/analyze", json=REQUEST).json()
    assert body["drift"]["aligned"] is False
    assert body["drift"]["structural"] == [{"change": "MODIFIED", "file": "src/order.js", "id": "./src/order.js:charge", "kind": "function"}]


def test_javascript_behavioral_drift_is_reported(served):
    reader, client = served
    reader.commit_models()
    reader.files["src/order.js"] = JAVASCRIPT.replace("'paid'", "'cancelled'").encode()
    drift = client.post("/system/analyze", json=REQUEST).json()["drift"]
    assert drift["structural"] == []
    assert {d["change"] for d in drift["behavioral"]} == {"ADDED", "REMOVED"}


def test_javascript_changes_are_judged_by_existing_ownership_rules(served):
    reader, client = served
    reader.commit_models()
    reader.author = "bob@x.com"
    violations = client.post("/system/analyze", json=REQUEST).json()["drift"]["ownership"]
    assert any(v["path"] == "src/order.js" and v["author"] == "bob@x.com" for v in violations)


def test_existing_python_scope_is_never_widened(served):
    reader, client = served
    reader.files["models/scope.json"] = json.dumps(check.DEFAULT_SCOPE).encode()
    reader.files["src/order.js"] = b"invalid {{{"
    response = client.post("/system/generate", json=REQUEST)
    assert response.status_code == 200
    files = response.json()["files"]
    assert json.loads(files["scope.json"]) == check.DEFAULT_SCOPE
    assert {n["id"] for n in json.loads(files["structural.json"])["nodes"] if n["kind"] == "module"} == {"app"}


def test_committed_empty_scope_keeps_legacy_defaults(served):
    reader, client = served
    reader.files["models/scope.json"] = b"{}"
    files = client.post("/system/generate", json=REQUEST).json()["files"]
    assert json.loads(files["scope.json"]) == {}
    assert {n["id"] for n in json.loads(files["structural.json"])["nodes"] if n["kind"] == "module"} == {"app"}


def test_invalid_committed_scope_is_not_replaced_by_an_expanded_default(served):
    reader, client = served
    reader.files["models/scope.json"] = b"not JSON"
    response = client.post("/system/generate", json=REQUEST)
    assert response.status_code == 500 and response.json()["code"] == "ANALYSIS_FAILED"


def test_javascript_syntax_error_is_an_explicit_no_verdict(served):
    reader, client = served
    reader.commit_models()
    reader.files["src/order.js"] = b"function {"
    body = client.post("/system/analyze", json=REQUEST).json()
    assert body["drift"] is None and body["drift_error"]["code"] == "PARSE_FAILED"


def test_default_scope_ignores_vendored_javascript_and_tests():
    paths = ["app.py", "node_modules/lib/x.js", "src/vendor/x.js", "tests/bad.js"]
    assert check.default_scope(paths) == check.DEFAULT_SCOPE
    paths += ["src/app.mjs"]
    scope = check.default_scope(paths)
    assert check.in_scope(paths, scope) == ["app.py", "src/app.mjs"]


def test_direct_core_preserves_parameters_and_ownership_for_both_languages():
    reader = Reader({"app.py": PYTHON, "order.js": JAVASCRIPT})
    scope = {**check.default_scope(reader.tree()), "verbosity": 1, "volatility": 3}
    reader.files["models/scope.json"] = json.dumps(scope).encode()
    reader.commit_models()
    assert json.loads(reader.files["models/scope.json"]) == scope
    assert check.answer(check.read_sources(reader))["aligned"] is True
    reader.author = "bob@x.com"
    answer = check.answer(check.read_sources(reader))
    assert answer["aligned"] is False
    assert {v["path"] for v in answer["ownership"]} >= {"app.py", "order.js"}


def test_direct_core_keeps_the_teams_javascript_node_budget():
    reader = Reader({f"src/module{i}.js": "export function run(){}" for i in range(10)})
    files = check.generate_models(reader, verbosity=1)
    nodes = json.loads(files["structural.json"])["nodes"]
    assert len(nodes) == 6
    assert {node["kind"] for node in nodes} == {"module"}


def test_direct_core_reports_authored_javascript_behavioral_model_drift():
    reader = Reader({"order.js": JAVASCRIPT})
    reader.commit_models()
    model = json.loads(reader.files["models/behavioral.json"])
    model["transitions"] = []
    reader.files["models/behavioral.json"] = json.dumps(model).encode()
    answer = check.answer(check.read_sources(reader))
    assert answer["aligned"] is False
    assert answer["behavioral"] and answer["structural"] == []


def test_direct_core_keeps_volatile_javascript_differences_visible():
    reader = Reader({"order.js": JAVASCRIPT})
    reader.files["models/scope.json"] = json.dumps({**check.default_scope(reader.tree()), "volatility": 3}).encode()
    reader.commit_models()
    reader.files["order.js"] = JAVASCRIPT.replace("(amount)", "(amount, currency)").encode()
    answer = check.answer(check.read_sources(reader))
    assert answer["aligned"] is True
    assert answer["structural"] == [{"change": "MODIFIED", "file": "order.js", "id": "./order.js:charge", "kind": "function"}]


def test_models_view_uses_the_same_javascript_fallback(served):
    reader, client = served
    assert "structural.json" in model_drift.snapshot(reader, reader.head)
    response = client.get("/models/view", params=REQUEST)
    assert response.status_code == 200
    assert "2</b> modules" in response.text
    assert "1</b> transition" in response.text


def test_generate_preserves_the_committed_verbosity(served):
    reader, client = served
    reader.files["models/scope.json"] = json.dumps({**check.default_scope(reader.tree()), "verbosity": 1}).encode()
    files = client.post("/system/generate", json=REQUEST).json()["files"]
    assert {n["kind"] for n in json.loads(files["structural.json"])["nodes"]} == {"module"}
    assert json.loads(files["scope.json"])["verbosity"] == 1


def test_cli_round_trip_with_mixed_source(tmp_path, capsysbinary):
    # verifies real committed inputs, initialization, drift and update through the local reader
    repo = tmp_path / "mixed"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=ana", "-c", "user.email=ana@x.com"]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True, capture_output=True)
    (repo / "app.py").write_text(PYTHON, encoding="utf-8")
    (repo / "order.js").write_text(JAVASCRIPT, encoding="utf-8")

    def commit():
        subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
        subprocess.run([*git, "commit", "-qm", "change"], check=True, capture_output=True)

    commit()
    assert cli.main(["init", "--repo", str(repo)]) == 0
    commit()
    assert cli.main(["check", "--repo", str(repo)]) == 0
    capsysbinary.readouterr()
    (repo / "order.js").write_text(JAVASCRIPT.replace("(amount)", "(amount, currency)"), encoding="utf-8")
    commit()
    assert cli.main(["check", "--repo", str(repo)]) == 1
    assert json.loads(capsysbinary.readouterr().out)["structural"][0]["id"] == "./order.js:charge"
    assert cli.main(["update", "--repo", str(repo)]) == 0
    commit()
    assert cli.main(["check", "--repo", str(repo)]) == 0


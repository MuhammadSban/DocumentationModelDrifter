# checks drift and drift_error on POST /system/analyze against local bare repos: the same answer
# drifter check gives, a no-verdict that keeps 200 and SUCCESS, and a check that still runs over
# the change limit (issue #19)

import json
import subprocess

import pytest
from fastapi.testclient import TestClient

from drifter import cli
from GitHub_Connector import api, rules
from GitHub_Connector.settings import get_settings
from models.common import write_model
from models.structural_model import generate_structural

CODE = {"src/app.py": "def charge(amount):\n    return amount\n"}
OWNED = {"rules": [{"owners": ["ana@x.com"], "pattern": "src/app.py"}], "schema_version": 1}
SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}


def _git(cwd, *args, author="ana@x.com"):
    # runs one git command as a scripted author and returns its text
    return subprocess.run(["git", "-C", str(cwd), "-c", f"user.email={author}", "-c", "user.name=x", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def _commit(work, files, author="ana@x.com"):
    # writes files, commits them as author and returns the new head SHA
    for path, text in files.items():
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_bytes(text.encode())
    _git(work, "add", "-A", author=author)
    _git(work, "commit", "-qm", "change", author=author)
    return _git(work, "rev-parse", "HEAD")


def _models(files):
    # renders four /models files that match files, so the commit starts aligned
    return {
        "models/behavioral.json": write_model({"schema_version": 1}),
        "models/ownership.json": write_model(OWNED),
        "models/scope.json": write_model(SCOPE),
        "models/structural.json": write_model(generate_structural(files)),
    }


@pytest.fixture
def repo(tmp_path, monkeypatch):
    # returns the work checkout and a publish() that serves its current state as the bare repo owner/repo
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    bare = tmp_path / "remotes" / "owner" / "repo.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")

    def publish():
        # pushes every commit so far to the bare repo the service clones
        _git(work, "push", "-q", str(bare), "main")

    monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", (tmp_path / "remotes").as_uri() + "/")
    monkeypatch.setenv("DRIFTER_RUNS_DIR", str(tmp_path / "runs"))
    get_settings.cache_clear()
    yield work, publish
    get_settings.cache_clear()


def _analyze(commit):
    # calls the route the way a tester does
    return TestClient(api.app).post("/system/analyze", json={"repository": "owner/repo", "commit_id": commit})


def _cli_check(work, commit, capsysbinary):
    # runs drifter check on the work checkout, expecting drift (exit 1), and returns its stdout bytes
    assert cli.main(["check", commit, "--repo", str(work)]) == 1
    return capsysbinary.readouterr().out


def _drifted(work):
    # commits aligned code, then a second author adds a function: structural drift and an ownership violation
    _commit(work, {**CODE, **_models(CODE)})
    return _commit(work, {"src/app.py": CODE["src/app.py"] + "\n\ndef refund(amount):\n    return -amount\n"},
                   author="bob@x.com")


def test_an_aligned_commit_is_aligned_and_saved_with_drift_and_drift_error(repo):
    work, publish = repo
    head = _commit(work, {**CODE, **_models(CODE)})
    publish()

    resp = _analyze(head)

    assert resp.status_code == 200
    body = resp.json()
    assert (body["status"], body["drift"], body["drift_error"]) == (
        "SUCCESS", {"aligned": True, "behavioral": [], "ownership": [], "structural": []}, None)
    saved = TestClient(api.app).get(f"/system/analysis/{body['analysis_id']}")
    assert saved.content == resp.content


def test_a_commit_without_models_is_200_success_with_models_not_found(repo):
    work, publish = repo
    head = _commit(work, CODE)
    publish()

    resp = _analyze(head)

    assert resp.status_code == 200
    body = resp.json()
    assert (body["status"], body["drift"], body["drift_error"]["code"]) == ("SUCCESS", None, "MODELS_NOT_FOUND")


def test_a_structural_model_breaking_its_schema_is_200_success_with_invalid_models(repo):
    work, publish = repo
    unknown_edge = {**generate_structural(CODE), "edges": [
        {"file": "src/app.py", "id": "calls:app->app", "kind": "calls", "source": "app", "target": "app"}]}
    head = _commit(work, {**CODE, **_models(CODE), "models/structural.json": write_model(unknown_edge)})
    publish()

    body = _analyze(head).json()

    assert (body["status"], body["drift"], body["drift_error"]["code"]) == ("SUCCESS", None, "INVALID_MODELS")
    assert "models/structural.json" in body["drift_error"]["message"]


def test_drift_written_canonically_is_byte_identical_to_drifter_check(repo, capsysbinary):
    work, publish = repo
    head = _drifted(work)
    publish()

    body = _analyze(head).json()

    out = _cli_check(work, head, capsysbinary)
    assert write_model(body["drift"]).encode("utf-8") == out
    # pins the drift both found, so an empty answer on both sides cannot pass
    assert [d["id"] for d in body["drift"]["structural"]] == ["app:refund"]
    assert [v["author"] for v in body["drift"]["ownership"]] == ["bob@x.com"]


def test_a_new_elif_state_gives_the_same_behavioral_drift_as_drifter_check(repo, capsysbinary):
    work, publish = repo
    machine = "class Order:\n    def advance(self):\n        if self.status == 'open':\n            self.status = 'paid'\n"
    first = _commit(work, {"src/order.py": machine})
    assert cli.main(["init", first, "--repo", str(work)]) == 0
    _commit(work, {})
    head = _commit(work, {"src/order.py": machine + (
        "        elif self.status == 'paid':\n            self.status = 'shipped'\n")})
    publish()
    capsysbinary.readouterr()

    body = _analyze(head).json()

    out = _cli_check(work, head, capsysbinary)
    assert write_model(body["drift"]).encode("utf-8") == out
    assert [(d["change"], d["kind"]) for d in body["drift"]["behavioral"]] == [
        ("ADDED", "state"), ("ADDED", "transition")]
    assert (body["drift"]["structural"], body["drift"]["ownership"]) == ([], [])


def test_over_the_change_limit_drift_still_equals_drifter_check(repo, monkeypatch, capsysbinary):
    work, publish = repo
    head = _drifted(work)
    publish()
    monkeypatch.setattr(rules, "max_changed_files", lambda: 0)

    body = _analyze(head).json()

    assert (body["status"], body["error"]["code"]) == ("ERROR", "CHANGE_LIMIT_EXCEEDED")
    assert body["drift"] == json.loads(_cli_check(work, head, capsysbinary))
    assert body["drift"]["aligned"] is False

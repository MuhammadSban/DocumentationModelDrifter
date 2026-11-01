# checks the drift pair on /analyze against real clones: one verdict per outcome, one per
# no-verdict code (spec 5.2, phase4.md v1.1)

import json
import subprocess

import pytest

from GitHub_Connector import analysis, runs
from GitHub_Connector.schemas import AnalysisRequest
from GitHub_Connector.settings import get_settings
from models.common import write_model
from models.structural_model import generate_structural

# the smallest repository the check accepts: one in-scope file and all four model files
CODE = {"src/app.py": "def charge(amount):\n    return amount\n"}
SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}
EMPTY_BEHAVIORAL = {"schema_version": 1, "states": [], "transitions": []}
NO_RULES = {"rules": [], "schema_version": 1}


def _git(cwd, *args, author="ana@x.com"):
    # runs one git command with a scripted author, so ownership has something to judge
    env = ["-c", "user.email=" + author, "-c", "user.name=" + author.split("@")[0]]
    subprocess.run(["git", "-C", str(cwd), *env, *args], check=True, capture_output=True)


def _repo(tmp_path, files, author="ana@x.com", second=None):
    # builds a bare repository holding files, and points the connector's clone URL at its folder;
    # returns owner/name and the head SHA. A second dict adds one more commit on top.
    work = tmp_path / "work"
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    for commit in (files, second):
        if commit is None:
            continue
        for path, text in commit.items():
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text if isinstance(text, bytes) else text.encode())
        _git(work, "add", "-A", author=author)
        _git(work, "commit", "-qm", "change", author=author)
    bare = tmp_path / "remotes" / "owner" / "repo.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    # lets a partial clone filter and ask for objects by id, as GitHub does
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    return "owner/repo", head, tmp_path / "remotes"


def _models(code, **overrides):
    # writes the four model files that match code, before any override makes one of them wrong
    files = {
        "models/structural.json": write_model(generate_structural(code)),
        "models/behavioral.json": write_model(EMPTY_BEHAVIORAL),
        "models/ownership.json": write_model(NO_RULES),
        "models/scope.json": write_model(SCOPE),
    }
    files.update(overrides)
    return files


def _analyze(tmp_path, monkeypatch, files, author="ana@x.com", second=None):
    # runs one analysis against a fresh local repository and returns the result
    repo, head, remotes = _repo(tmp_path, files, author=author, second=second)
    monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", remotes.as_uri() + "/")
    monkeypatch.setattr(runs, "save", lambda *args: None)
    get_settings.cache_clear()
    try:
        return analysis.analyze(AnalysisRequest(repository=repo, commit_id=head))
    finally:
        get_settings.cache_clear()


def test_models_that_match_the_code_are_aligned(tmp_path, monkeypatch):
    result = _analyze(tmp_path, monkeypatch, {**CODE, **_models(CODE)})

    assert result.drift_error is None
    assert result.drift.aligned is True
    assert (result.drift.structural, result.drift.behavioral, result.drift.ownership) == ([], [], [])


def test_code_the_model_does_not_know_is_one_added_difference(tmp_path, monkeypatch):
    # commits models for CODE, then adds a function without updating them
    grown = {"src/app.py": CODE["src/app.py"] + "\n\ndef refund(amount):\n    return -amount\n"}

    result = _analyze(tmp_path, monkeypatch, {**CODE, **_models(CODE)}, second=grown)

    assert result.drift.aligned is False
    assert [(d.change, d.id, d.kind) for d in result.drift.structural] == [
        ("ADDED", "app:refund", "function")
    ]


def test_a_commit_by_a_non_owner_is_one_violation(tmp_path, monkeypatch):
    rules = {"rules": [{"owners": ["bob@x.com"], "pattern": "src/app.py"}], "schema_version": 1}
    files = {**CODE, **_models(CODE, **{"models/ownership.json": write_model(rules)})}

    result = _analyze(tmp_path, monkeypatch, files, author="ana@x.com")

    assert result.drift.aligned is False
    assert [(v.author, v.change, v.owners, v.path) for v in result.drift.ownership] == [
        ("ana@x.com", "VIOLATION", ["bob@x.com"], "src/app.py")
    ]


def test_an_owners_own_commit_is_no_violation(tmp_path, monkeypatch):
    rules = {"rules": [{"owners": ["ana@x.com"], "pattern": "src/**"}], "schema_version": 1}
    files = {**CODE, **_models(CODE, **{"models/ownership.json": write_model(rules)})}

    result = _analyze(tmp_path, monkeypatch, files, author="ana@x.com")

    assert result.drift.ownership == []


@pytest.mark.parametrize(
    "code, overrides, expected",
    [
        pytest.param(CODE, {"models/structural.json": None}, "MODELS_NOT_FOUND", id="MODELS_NOT_FOUND"),
        pytest.param(CODE, {"models/scope.json": "{not json"}, "INVALID_MODELS", id="INVALID_MODELS"),
        pytest.param({"src/app.py": "def f(:\n"}, {}, "PARSE_FAILED", id="PARSE_FAILED-syntax"),
        pytest.param({"src/app.py": b"\xff\xfe\x00bin"}, {}, "PARSE_FAILED", id="PARSE_FAILED-not-utf8"),
        pytest.param({"src/app.py": "x = 1\n" + "# pad\n" * 180_000}, {}, "FILE_TOO_LARGE", id="FILE_TOO_LARGE"),
    ],
)
def test_each_no_verdict_code(tmp_path, monkeypatch, code, overrides, expected):
    # every one of the four codes leaves status SUCCESS, drift null and change detection intact
    # the models are always the ones CODE deserves: each case fails before any comparison
    files = {**code, **_models(CODE)}
    for path, text in overrides.items():
        files.pop(path) if text is None else files.update({path: text})

    result = _analyze(tmp_path, monkeypatch, files)

    assert result.drift is None
    assert result.drift_error.code == expected
    assert result.status == "SUCCESS"
    assert result.changes


def test_drift_is_byte_identical_across_runs(tmp_path, monkeypatch):
    # REQ-07: the same repository and models give the same answer every time
    files = {**CODE, **_models(CODE)}

    first = _analyze(tmp_path / "a", monkeypatch, files)
    second = _analyze(tmp_path / "b", monkeypatch, files)

    assert json.dumps(first.drift.model_dump(mode="json"), sort_keys=True) == json.dumps(
        second.drift.model_dump(mode="json"), sort_keys=True
    )

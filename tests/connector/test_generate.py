# checks POST /system/generate against local bare repos: the four /models texts as drifter init
# writes them, and the same 400 and 404 codes as /analyze (issue #20)

import subprocess
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from drifter import cli
from GitHub_Connector import api
from GitHub_Connector.settings import get_settings

CODE = {
    "src/app.py": "def charge(amount):\n    return amount\n",
    "src/order.py": "class Order:\n    def pay(self):\n        if self.status == 'open':\n            self.status = 'paid'\n",
    "tests/test_app.py": "def test_x():\n    pass\n",
}
CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "contract" / "pod-contract.openapi.yml"


def _git(cwd, *args):
    # runs one git command as a scripted author, so ownership has someone to propose
    subprocess.run(["git", "-C", str(cwd), "-c", "user.email=ana@x.com", "-c", "user.name=ana", *args],
                   check=True, capture_output=True)


@pytest.fixture
def served(tmp_path, monkeypatch):
    # commits CODE, serves it as the bare repo owner/repo and returns the work checkout and head SHA
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    for path, text in CODE.items():
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_bytes(text.encode())
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "first")
    bare = tmp_path / "remotes" / "owner" / "repo.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", (tmp_path / "remotes").as_uri() + "/")
    get_settings.cache_clear()
    yield work, head
    get_settings.cache_clear()


def _post(body):
    # calls the route the way a tester does
    return TestClient(api.app).post("/system/generate", json=body)


def test_the_four_texts_equal_drifter_init_byte_for_byte(served):
    work, head = served

    resp = _post({"repository": "owner/repo", "commit_id": head})
    assert cli.main(["init", head, "--repo", str(work)]) == 0

    assert resp.status_code == 200
    written = {p.name: p.read_bytes() for p in (work / "models").iterdir()}
    assert {name: text.encode("utf-8") for name, text in resp.json()["files"].items()} == written
    # pins a real behavioral model, so a placeholder on both sides cannot pass
    assert '"paid"' in resp.json()["files"]["behavioral.json"]


@pytest.mark.parametrize("body", [{"repository": "no-slash", "commit_id": "a" * 40}, {"repository": "owner/repo"}])
def test_a_bad_request_is_400(served, body):
    resp = _post(body)

    assert (resp.status_code, resp.json()["code"]) == (400, "INVALID_REQUEST")


@pytest.mark.parametrize("repository, commit, code", [
    ("owner/missing", None, "REPOSITORY_NOT_FOUND"),
    ("owner/repo", "b" * 40, "COMMIT_NOT_FOUND"),
])
def test_an_unknown_repository_or_commit_is_404(served, repository, commit, code):
    _, head = served

    resp = _post({"repository": repository, "commit_id": commit or head})

    assert (resp.status_code, resp.json()["code"]) == (404, code)


def test_the_response_follows_the_contracts_generate_result(served):
    _, head = served
    schema = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["components"]["schemas"]["GenerateResult"]

    body = _post({"repository": "owner/repo", "commit_id": head}).json()

    assert set(body) == set(schema["properties"]) and set(schema["required"]) <= set(body)
    assert all(isinstance(body[key], str) for key in ("repository", "head_commit", "tool_version"))
    assert body["head_commit"] == head
    assert set(body["files"]) == set(schema["properties"]["files"]["properties"])
    assert all(isinstance(text, str) for text in body["files"].values())

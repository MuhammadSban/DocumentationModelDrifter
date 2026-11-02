# replays contract/model-golden-outputs.json: builds the model fixture with its script, serves it as the
# fixture repository and checks /system/analyze answers every case as the golden file says (contract §4)

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from GitHub_Connector import api
from GitHub_Connector.settings import get_settings

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "docs" / "contract" / "model-golden-outputs.json").read_text(encoding="utf-8"))
CASES = GOLDEN["cases"]


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    # builds the fixture once and mirrors it to the bare repo the service clones; returns the build and remotes
    base = tmp_path_factory.mktemp("model-fixture")
    work = base / "build"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "model_fixture.py"), str(work)], check=True)
    remotes = base / "remotes"
    bare = remotes / (GOLDEN["fixture_repo"] + ".git")
    subprocess.run(["git", "clone", "-q", "--mirror", str(work), str(bare)], check=True)
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    return work, remotes


@pytest.fixture
def service(fixture, tmp_path, monkeypatch):
    # points the service at the mirrored fixture
    monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", fixture[1].as_uri() + "/")
    monkeypatch.setenv("DRIFTER_RUNS_DIR", str(tmp_path / "runs"))
    get_settings.cache_clear()
    yield TestClient(api.app)
    get_settings.cache_clear()


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_the_build_tags_each_case_at_its_published_sha(fixture, case):
    assert _git(fixture[0], "rev-parse", case["case"]) == case["request"]["commit_id"]


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_analyze_answers_each_case_as_published(service, case):
    resp = service.post("/system/analyze", json=case["request"])

    assert resp.status_code == 200
    body = resp.json()

    want = case["expected"]
    assert body["drift"] == want["drift"]
    if want["drift_error"] is None:
        assert body["drift_error"] is None
    else:
        # compares the code only, so a reworded message never fails (contract §4, T-32)
        assert body["drift_error"]["code"] == want["drift_error"]["code"]

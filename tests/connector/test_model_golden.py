# replays contract/model-golden-outputs.json: builds the model fixture with its script, serves it as the
# fixture repository and checks /system/analyze, /system/generate and drifter check answer every case as the
# golden file says (contract §4)

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from drifter import cli
from GitHub_Connector import api
from GitHub_Connector.settings import get_settings

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "docs" / "contract" / "model-golden-outputs.json").read_text(encoding="utf-8"))
CASES = [c for c in GOLDEN["cases"] if "drift" in c["expected"]]
GENERATE = next(c for c in GOLDEN["cases"] if c["case"] == "L0-generate")

# pins drifter check's exit code per case, from spec §4.2's expected verdicts rather than the golden file
EXIT = {"L-pre": 2, "L0": 0, "L1": 0, "L2": 1, "L3": 1, "L4": 1, "L5": 0, "L6": 1, "L7": 1}


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


def test_the_golden_file_has_every_case_and_the_l0_generate_case():
    assert [c["case"] for c in CASES] == list(EXIT)
    assert GENERATE["request"] == next(c for c in CASES if c["case"] == "L0")["request"]


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_the_build_tags_each_case_at_its_published_sha(fixture, case):
    assert _git(fixture[0], "rev-parse", case["case"]) == case["request"]["commit_id"]


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_analyze_answers_each_case_as_published(service, case):
    resp = service.post("/system/analyze", json=case["request"])

    assert resp.status_code == 200
    body = resp.json()

    want = case["expected"]
    # compares the whole drift object, list order included (contract §4)
    assert body["drift"] == want["drift"]
    if want["drift_error"] is None:
        assert body["drift_error"] is None
    else:
        # compares the code only, so a reworded message never fails (contract §4, T-32)
        assert body["drift_error"]["code"] == want["drift_error"]["code"]


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_drifter_check_answers_each_case_as_published(fixture, case, capsys):
    code = cli.main(["check", case["request"]["commit_id"], "--repo", str(fixture[0])])

    got = json.loads(capsys.readouterr().out)
    assert code == EXIT[case["case"]]
    assert got.get("drift", got) == case["expected"]["drift"]
    if case["expected"]["drift_error"] is not None:
        assert got["drift_error"]["code"] == case["expected"]["drift_error"]["code"]


def test_generate_at_l0_returns_the_three_texts_as_published_and_committed(service, fixture):
    resp = service.post("/system/generate", json=GENERATE["request"])

    assert resp.status_code == 200
    files = resp.json()["files"]
    want = GENERATE["expected"]["files"]
    assert set(want) == {"behavioral.json", "scope.json", "structural.json"}
    for name, text in want.items():
        assert files[name] == text
        # ties the golden text to the bytes committed at L0, so T-33 checks generate against the commit
        committed = subprocess.run(["git", "-C", str(fixture[0]), "show", f"L0:models/{name}"],
                                   check=True, capture_output=True).stdout
        assert text.encode("utf-8") == committed

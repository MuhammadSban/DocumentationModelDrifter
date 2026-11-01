# checks every case of Team 16's golden-outputs.json against a real clone of their fixture (v1.1 SPEC section 9)

import json
import subprocess
from pathlib import Path

import pytest

from GitHub_Connector import analysis, runs
from GitHub_Connector.schemas import AnalysisRequest

GOLDEN = json.loads((Path(__file__).resolve().parents[2] / "docs/contract/golden-outputs.json").read_text("utf-8"))

# compares what T-01 to T-17 compare; issues is judged only in T-18 to T-21 (contract section 3)
FIELDS = ["head_commit", "base_commit", "config_version", "status", "error", "changes", "skipped", "unmapped"]


def _online() -> bool:
    # tells whether the fixture repository can be reached, so the test skips offline instead of failing
    url = f"https://github.com/{GOLDEN['fixture_repo']}.git"
    try:
        return subprocess.run(["git", "ls-remote", url], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


pytestmark = pytest.mark.skipif(not _online(), reason="the fixture repository on GitHub cannot be reached")


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda c: c["case"])
def test_golden_case(case, monkeypatch):
    monkeypatch.setattr(runs, "save", lambda *args: None)
    request = AnalysisRequest(repository=GOLDEN["fixture_repo"], **case["request"])

    got = analysis.analyze(request).model_dump(mode="json")

    assert {f: got.get(f) for f in FIELDS} == {f: case["expected"][f] for f in FIELDS}

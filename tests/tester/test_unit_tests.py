# tests the pytest group runner the /tester page uses

from Tester import unit_tests
from Tester.unit_tests import run_group


def test_group_reports_each_test():
    answer = run_group("common")
    assert answer["title"] == "Shared tests"
    assert len(answer["tests"]) >= 6
    # allows skips, the seam test skips a schema check until its owner writes the schema
    assert {t["outcome"] for t in answer["tests"]} <= {"pass", "skip"}
    assert all(t["name"].startswith(("test_common::", "test_seam::")) for t in answer["tests"])


def test_summary_has_no_color_codes(monkeypatch):
    # keeps the page's summary line plain when the server's environment asks pytest for color
    monkeypatch.setenv("PY_COLORS", "1")
    assert "\x1b" not in run_group("common")["summary"]


def test_empty_group_says_so(tmp_path, monkeypatch):
    # runs the group against an empty folder, since every real group now has tests
    (tmp_path / "tests" / "behavioral").mkdir(parents=True)
    monkeypatch.setattr(unit_tests, "REPO_ROOT", tmp_path)
    assert run_group("behavioral") == {"group": "behavioral", "summary": "no tests yet", "tests": [],
                                       "title": "Behavioral model tests"}

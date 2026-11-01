# checks that failures answer with the contract's codes (pod-contract.md section 7)

from fastapi.testclient import TestClient

from GitHub_Connector import analysis, api, runs
from GitHub_Connector.schemas import ErrorCode
from GitHub_Connector.settings import get_settings
from test_analysis import fake_fetch

REQUEST = {"repository": "owner/repo", "commit_id": "a" * 40}


def test_codes_are_the_contracts():
    assert {c.value for c in ErrorCode} == {
        "INVALID_REQUEST", "REPOSITORY_NOT_FOUND", "COMMIT_NOT_FOUND",
        "ANALYSIS_NOT_FOUND", "ANALYSIS_FAILED", "STORAGE_FAILED",
    }


def test_deadline_is_80_s():
    assert get_settings().analysis_deadline == 80


def test_a_failed_save_is_storage_failed(monkeypatch):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)

    def broken_save(*args):
        raise OSError("disk full")

    monkeypatch.setattr(runs, "save", broken_save)
    resp = TestClient(api.app).post("/system/analyze", json=REQUEST)

    assert resp.status_code == 500
    assert resp.json()["code"] == "STORAGE_FAILED"


def test_an_unexpected_crash_is_analysis_failed(monkeypatch):
    def crash(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(analysis, "fetch", crash)
    resp = TestClient(api.app, raise_server_exceptions=False).post("/system/analyze", json=REQUEST)

    assert resp.status_code == 500
    assert resp.json()["code"] == "ANALYSIS_FAILED"

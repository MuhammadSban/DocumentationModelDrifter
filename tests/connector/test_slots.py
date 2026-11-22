# checks the 2 check slots: a wait for one counts against the check's own deadline (spec 7.3)

import json
import socket
import threading
import time
import urllib.request
from contextlib import contextmanager

import pytest
import uvicorn
from fastapi.testclient import TestClient

from GitHub_Connector import analysis, api, runs
from GitHub_Connector.settings import get_settings
from test_analysis import fake_fetch

REQUEST = {"repository": "owner/repo", "commit_id": "a" * 40}
JOIN = 10  # caps each join, so a request that would wait forever fails the test instead of hanging it


@pytest.fixture
def slots():
    # holds both slots for the test, released in the finally of the fixture whatever the test did
    sem = analysis.slot()
    held = [sem.acquire(timeout=1) for _ in range(get_settings().max_concurrent)]
    assert all(held), "a slot was still taken by an earlier test"
    state = {"held": len(held)}

    def release():
        while state["held"]:
            state["held"] -= 1
            sem.release()

    yield release
    release()


@pytest.fixture
def deadline(monkeypatch):
    # shortens the check's deadline, the cached settings object is the one the code reads
    def set_to(seconds):
        monkeypatch.setattr(get_settings(), "analysis_deadline", seconds)

    return set_to


def call_in_thread(method, path, **kwargs):
    # sends one request in a thread and hands back the thread and a box for its response
    box = {}

    def run():
        box["resp"] = TestClient(api.app, raise_server_exceptions=False).request(method, path, **kwargs)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, box


def test_slot_wait_past_the_deadline_is_analysis_failed(monkeypatch, slots, deadline):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)
    deadline(0.5)
    try:
        thread, box = call_in_thread("POST", "/system/analyze", json=REQUEST)
        thread.join(JOIN)
        assert not thread.is_alive(), "the check still waits for a slot past its deadline"
    finally:
        slots()
        thread.join(JOIN)
    assert box["resp"].status_code == 500
    assert box["resp"].json()["code"] == "ANALYSIS_FAILED"


def test_slot_wait_counts_against_the_deadline(monkeypatch, slots, deadline):
    seen = []

    @contextmanager
    def recording_fetch(repo, head, base, deadline):
        seen.append(deadline)
        with fake_fetch(repo, head, base, deadline) as cmp:
            yield cmp

    monkeypatch.setattr(analysis, "fetch", recording_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)
    deadline(5)
    held = 1.0
    before = time.monotonic()
    try:
        thread, box = call_in_thread("POST", "/system/analyze", json=REQUEST)
        time.sleep(held)
    finally:
        slots()
        thread.join(JOIN)
    assert box["resp"].status_code == 200
    # arrival is after `before`, and nowhere near the end of the held wait
    assert before + 5 <= seen[0] < before + 5 + held / 2


def test_slot_wait_past_the_deadline_fails_generate_too(monkeypatch, slots, deadline):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    deadline(0.5)
    try:
        thread, box = call_in_thread("POST", "/system/generate", json=REQUEST)
        thread.join(JOIN)
        assert not thread.is_alive(), "generate still waits for a slot past its deadline"
    finally:
        slots()
        thread.join(JOIN)
    assert box["resp"].status_code == 500
    assert box["resp"].json()["code"] == "ANALYSIS_FAILED"


def test_slot_is_free_again_after_a_check(monkeypatch):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)
    resp = TestClient(api.app).post("/system/analyze", json=REQUEST)
    assert resp.status_code == 200
    sem = analysis.slot()
    held = [sem.acquire(blocking=False) for _ in range(get_settings().max_concurrent)]
    for taken in held:
        if taken:
            sem.release()
    assert all(held)


VIEW = "/models/view?repository=owner/repo&commit_id=" + "a" * 40


def test_models_view_waits_for_a_slot_and_fails_at_its_deadline(monkeypatch, slots, deadline):
    calls = []

    def counting_fetch(*args):
        calls.append(args)
        raise AssertionError("fetch was called without a slot")

    monkeypatch.setattr(api, "fetch", counting_fetch)
    deadline(0.5)
    try:
        thread, box = call_in_thread("GET", VIEW)
        thread.join(JOIN)
        assert not thread.is_alive(), "the view still waits for a slot past its deadline"
    finally:
        slots()
        thread.join(JOIN)
    assert calls == []
    assert box["resp"].status_code == 500
    assert box["resp"].json()["code"] == "ANALYSIS_FAILED"


def test_models_view_frees_its_slot(monkeypatch):
    def missing_fetch(*args):
        raise analysis.AnalysisError(analysis.ErrorCode.REPOSITORY_NOT_FOUND, "no such repository")

    monkeypatch.setattr(api, "fetch", missing_fetch)
    assert TestClient(api.app).get(VIEW).status_code == 404
    sem = analysis.slot()
    held = [sem.acquire(blocking=False) for _ in range(get_settings().max_concurrent)]
    for taken in held:
        if taken:
            sem.release()
    assert all(held)


@pytest.fixture
def served():
    # serves the real app under uvicorn, so routes share its real 40-thread pool
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(api.app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(5)


def test_health_answers_while_40_checks_wait(monkeypatch, slots, deadline, served):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)
    arrived = threading.Semaphore(0)
    real_validate = analysis.validate

    def counting_validate(request):
        arrived.release()
        real_validate(request)

    monkeypatch.setattr(analysis, "validate", counting_validate)
    deadline(60)
    body = json.dumps(REQUEST).encode()

    def check():
        request = urllib.request.Request(served + "/system/analyze", data=body, method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as resp:
            resp.read()

    checks = [threading.Thread(target=check, daemon=True) for _ in range(40)]
    try:
        for thread in checks:
            thread.start()
        for _ in checks:
            assert arrived.acquire(timeout=JOIN), "not all 40 checks reached the route"
        start = time.monotonic()
        with urllib.request.urlopen(served + "/system/health", timeout=1) as resp:
            assert resp.status == 200
        assert time.monotonic() - start < 1
    finally:
        slots()
        for thread in checks:
            thread.join(JOIN)

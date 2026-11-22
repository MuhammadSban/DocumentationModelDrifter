# tests the /tester routes on the real app, served locally, with the fake target as the system under test

import socket
import threading
import time

import pytest
import uvicorn

from Tester import client


@pytest.fixture(scope="module")
def app_url():
    from GitHub_Connector.api import app

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}/tester"
    server.should_exit = True
    thread.join(5)


def post(url, payload=None, raw=None):
    return client.call("POST", url, payload, raw)


def test_full_session(app_url, fake):
    setup = post(app_url + "/test/setup", {"target_url": fake.url})
    assert setup.status == 201
    session_id = setup.body["session_id"]

    run = post(app_url + "/test/run", {"session_id": session_id})
    assert run.status == 200
    assert sorted(run.body) == ["coverage", "results", "session_id", "target_url"]
    assert len(run.body["results"]) == 33

    assert post(app_url + "/test/run", {"session_id": session_id}).status == 409
    report = client.call("GET", f"{app_url}/test/report?session_id={session_id}")
    assert (report.status, report.body) == (200, run.body)


@pytest.mark.parametrize("payload, raw", [
    (None, b"not json"),
    ({}, None),
    ({"target_url": "ftp://host/system"}, None),
    ({"target_url": "https://user@host/system"}, None),
])
def test_setup_rejects_a_bad_target_url(app_url, payload, raw):
    reply = post(app_url + "/test/setup", payload, raw)
    assert (reply.status, reply.body["source"]) == (400, "tester")


def test_setup_without_an_answer_is_a_communication_error(app_url, closed_url):
    reply = post(app_url + "/test/setup", {"target_url": closed_url})
    assert (reply.status, reply.body["source"]) == (500, "communication")


def test_setup_passes_a_system_failure_through(app_url, fake):
    fake.setup_answer = (409, {"message": "another session is active", "source": "system"})
    reply = post(app_url + "/test/setup", {"target_url": fake.url})
    assert (reply.status, reply.body) == (409, {"message": "another session is active", "source": "system"})


def test_run_and_report_errors(app_url):
    assert post(app_url + "/test/run", {}).status == 400
    assert post(app_url + "/test/run", {"session_id": "nope"}).status == 404
    assert client.call("GET", app_url + "/test/report").status == 400
    assert client.call("GET", app_url + "/test/report?session_id=nope").status == 404
    assert client.call("GET", app_url + "/progress").status == 400
    assert client.call("GET", app_url + "/progress?session_id=nope").status == 404


def test_progress_shows_results_while_the_suite_runs(app_url, fake):
    fake.analyze_delay = 0.1
    session_id = post(app_url + "/test/setup", {"target_url": fake.url}).body["session_id"]
    progress_url = f"{app_url}/progress?session_id={session_id}"
    assert client.call("GET", progress_url).body == {"results": [], "session_id": session_id, "state": "ready"}

    answers = []
    thread = threading.Thread(target=lambda: answers.append(post(app_url + "/test/run", {"session_id": session_id})))
    thread.start()
    partial = {"results": []}
    for _ in range(200):
        partial = client.call("GET", progress_url).body
        if 0 < len(partial["results"]) < 33:
            break
        time.sleep(0.05)
    thread.join(60)

    assert partial["state"] == "running" and 0 < len(partial["results"]) < 33
    final = client.call("GET", progress_url).body
    assert final["state"] == "done" and final["results"] == answers[0].body["results"]
    assert partial["results"] == final["results"][:len(partial["results"])]


def test_page_and_catalog(app_url):
    page = client.call("GET", app_url)
    assert page.status == 200 and "Drifter tester" in page.text
    catalog = client.call("GET", app_url + "/catalog").body
    assert len(catalog["pod"]) == 33
    assert [g["key"] for g in catalog["unit_groups"]] == ["structural", "behavioral", "ownership", "common"]
    assert catalog["team16_url"] == "https://doc-tracker-team16.onrender.com/system"


def test_unknown_unit_group(app_url):
    assert post(app_url + "/unit/nope").status == 404


@pytest.fixture
def blocking_group(monkeypatch):
    # replaces the pytest run with a stand-in that holds until the test lets it go
    from Tester import unit_tests

    entered, release = threading.Event(), threading.Event()

    def run_group(group):
        entered.set()
        release.wait(10)
        return {"group": group, "summary": "", "tests": [], "title": unit_tests.GROUPS[group]}

    monkeypatch.setattr(unit_tests, "run_group", run_group)
    yield entered, release
    release.set()


def test_unit_run_second_call_gets_409_at_once(app_url, blocking_group):
    entered, release = blocking_group
    first = threading.Thread(target=post, args=(app_url + "/unit/common",), daemon=True)
    box = {}
    second = threading.Thread(target=lambda: box.update(reply=post(app_url + "/unit/common")), daemon=True)
    try:
        first.start()
        assert entered.wait(5), "the first run never started"
        second.start()
        second.join(3)
        assert not second.is_alive(), "the second run waited for the first"
    finally:
        release.set()
        first.join(10)
        second.join(10)
    assert box["reply"].status == 409
    assert box["reply"].body["source"] == "tester"


def test_unit_run_after_the_first_ended_runs(app_url, blocking_group):
    _, release = blocking_group
    release.set()
    assert post(app_url + "/unit/common").status == 200
    assert post(app_url + "/unit/common").status == 200


@pytest.fixture
def sessions(monkeypatch):
    # gives the tester a fresh session table, seeded in the order the seats were taken
    from Tester import api

    table = {}
    monkeypatch.setattr(api, "SESSIONS", table)

    def seed(*states):
        for i, state in enumerate(states):
            table[f"s{i}"] = {"report": None, "results": [], "state": state, "target_url": "http://x/system"}
        return table

    return seed


def test_session_cap_drops_the_oldest_finished_session(app_url, fake, sessions):
    table = sessions(*(["running"] * 5 + ["done"] * 5 + ["ready"] * 40))
    reply = post(app_url + "/test/setup", {"target_url": fake.url})
    assert reply.status == 201
    assert "s5" not in table and "s6" in table
    assert reply.body["session_id"] in table
    assert len(table) == 50


def test_session_cap_drops_the_oldest_unrun_session_when_none_finished(app_url, fake, sessions):
    table = sessions(*(["running"] * 5 + ["ready"] * 45))
    reply = post(app_url + "/test/setup", {"target_url": fake.url})
    assert reply.status == 201
    assert "s5" not in table and "s6" in table and "s0" in table
    assert len(table) == 50


def test_session_cap_refuses_setup_with_500_and_calls_no_target_when_all_are_running(app_url, fake, sessions):
    table = sessions(*["running"] * 50)
    reply = post(app_url + "/test/setup", {"target_url": fake.url})
    assert reply.status == 500
    assert reply.body["source"] == "tester"
    assert fake.setup_calls == 0
    assert len(table) == 50


def test_session_cap_frees_the_seat_of_a_setup_that_failed(app_url, fake, closed_url, sessions, monkeypatch):
    from Tester import api

    monkeypatch.setattr(api, "MAX_SESSIONS", 1)
    table = sessions()
    fake.setup_answer = (409, {"message": "another session is active", "source": "system"})
    assert post(app_url + "/test/setup", {"target_url": fake.url}).status == 409
    assert post(app_url + "/test/setup", {"target_url": closed_url}).status == 500
    fake.setup_answer = (201, None)
    reply = post(app_url + "/test/setup", {"target_url": fake.url})
    assert reply.status == 201
    assert list(table) == [reply.body["session_id"]]

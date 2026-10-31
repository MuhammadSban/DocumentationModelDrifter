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


def test_page_and_catalog(app_url):
    page = client.call("GET", app_url)
    assert page.status == 200 and "Drifter tester" in page.text
    catalog = client.call("GET", app_url + "/catalog").body
    assert len(catalog["pod"]) == 33
    assert [g["key"] for g in catalog["unit_groups"]] == ["structural", "behavioral", "ownership", "common"]
    assert catalog["team16_url"] == ""


def test_unknown_unit_group(app_url):
    assert post(app_url + "/unit/nope").status == 404

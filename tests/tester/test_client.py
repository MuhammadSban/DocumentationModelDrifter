# checks that the tester logs each call's time, so one full run can be timed call by call (phase4.md v1)

import io
import socket

import pytest

from Tester import client


class FakeResponse(io.BytesIO):
    # stands in for urlopen's answer
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_each_call_logs_its_method_url_status_and_time(monkeypatch, capsys):
    monkeypatch.setattr(client.OPENER, "open", lambda *a, **k: FakeResponse(b"{}"))

    client.call("POST", "https://host/system/analyze", {"x": 1})

    line = capsys.readouterr().out.strip()
    assert line.startswith("tester call POST https://host/system/analyze 200 ")
    assert line.endswith(" s")


def test_an_http_error_logs_its_status(monkeypatch, capsys):
    def http_error(*args, **kwargs):
        raise client.urllib.error.HTTPError("https://host/x", 404, "Not Found", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(client.OPENER, "open", http_error)

    assert client.call("GET", "https://host/x").status == 404
    assert capsys.readouterr().out.startswith("tester call GET https://host/x 404 ")


def test_a_call_with_no_reply_logs_no_reply(monkeypatch, capsys):
    def refused(*args, **kwargs):
        raise client.urllib.error.URLError("refused")

    monkeypatch.setattr(client.OPENER, "open", refused)

    with pytest.raises(client.NoReply):
        client.call("GET", "https://host/x")
    assert capsys.readouterr().out.startswith("tester call GET https://host/x no-reply ")


@pytest.fixture
def railway(monkeypatch):
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "p1")


def resolves_to(monkeypatch, *addresses):
    # makes every name resolve to the given addresses, and records the names looked up
    looked_up = []

    def getaddrinfo(host, port, *args, **kwargs):
        looked_up.append(host)
        return [(socket.AF_INET6 if ":" in a else socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, 0))
                for a in addresses]

    monkeypatch.setattr(client.socket, "getaddrinfo", getaddrinfo)
    return looked_up


def test_guard_refuses_localhost_on_railway(railway, monkeypatch):
    resolves_to(monkeypatch, "127.0.0.1")
    with pytest.raises(client.Refused):
        client.check_target("http://localhost:8000/system")


def test_guard_refuses_a_loopback_address_on_railway(railway):
    with pytest.raises(client.Refused):
        client.check_target("http://127.0.0.1:8000/system")


def test_guard_refuses_the_metadata_address_on_railway(railway):
    with pytest.raises(client.Refused):
        client.check_target("http://169.254.169.254/latest/meta-data")


def test_guard_refuses_an_internal_name_on_railway(railway, monkeypatch):
    looked_up = resolves_to(monkeypatch, "93.184.215.14")
    with pytest.raises(client.Refused):
        client.check_target("http://drifter.railway.internal:8000/system")
    assert looked_up == []


def test_guard_refuses_a_public_name_that_resolves_to_a_private_address_on_railway(railway, monkeypatch):
    resolves_to(monkeypatch, "93.184.215.14", "10.0.0.5")
    with pytest.raises(client.Refused):
        client.check_target("https://looks-public.example/system")


def test_guard_refuses_an_ipv4_mapped_loopback_address_on_railway(railway, monkeypatch):
    resolves_to(monkeypatch, "::ffff:127.0.0.1")
    with pytest.raises(client.Refused):
        client.check_target("https://mapped.example/system")


def test_guard_passes_a_public_address_on_railway(railway, monkeypatch):
    # passes the IPv4-mapped form of a public address too, which needs the guard's own unwrapping
    # rather than how a given Python version's ipaddress judges ::ffff:0:0/96
    looked_up = resolves_to(monkeypatch, "93.184.215.14", "::ffff:93.184.215.14")
    client.check_target("https://public.example/system")
    assert looked_up == ["public.example"]


def test_guard_sends_nothing_to_a_refused_target(railway, local_server):
    target = local_server()
    try:
        client.call("GET", target.url + "/health")
        error = None
    except Exception as exc:
        error = exc
    assert target.hits == 0
    assert isinstance(error, client.Refused)


def test_guard_lets_a_local_run_reach_localhost(monkeypatch, local_server):
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    target = local_server()
    assert client.call("GET", target.url + "/health").status == 200
    assert target.hits == 1


@pytest.fixture
def redirecting(local_server, monkeypatch):
    # gives a target whose every answer is a 302 to a second local server
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    first, second = local_server(), local_server()
    first.status = 302
    first.headers = {"Location": second.url + "/test/setup"}
    return first, second


def test_redirect_is_refused_and_names_the_new_url(redirecting):
    first, second = redirecting
    reply = client.call("POST", first.url + "/test/setup", {"session_id": "s", "setup": {}})
    assert reply.status == 302
    assert reply.new_url == second.url + "/test/setup"


def test_redirect_target_is_never_called(redirecting):
    first, second = redirecting
    client.call("GET", first.url + "/health")
    assert first.hits == 1
    assert second.hits == 0

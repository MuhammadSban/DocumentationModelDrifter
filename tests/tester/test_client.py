# checks that the tester logs each call's time, so one full run can be timed call by call (phase4.md v1)

import io

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
    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *a, **k: FakeResponse(b"{}"))

    client.call("POST", "https://host/system/analyze", {"x": 1})

    line = capsys.readouterr().out.strip()
    assert line.startswith("tester call POST https://host/system/analyze 200 ")
    assert line.endswith(" s")


def test_an_http_error_logs_its_status(monkeypatch, capsys):
    def http_error(*args, **kwargs):
        raise client.urllib.error.HTTPError("https://host/x", 404, "Not Found", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(client.urllib.request, "urlopen", http_error)

    assert client.call("GET", "https://host/x").status == 404
    assert capsys.readouterr().out.startswith("tester call GET https://host/x 404 ")


def test_a_call_with_no_reply_logs_no_reply(monkeypatch, capsys):
    def refused(*args, **kwargs):
        raise client.urllib.error.URLError("refused")

    monkeypatch.setattr(client.urllib.request, "urlopen", refused)

    with pytest.raises(client.NoReply):
        client.call("GET", "https://host/x")
    assert capsys.readouterr().out.startswith("tester call GET https://host/x no-reply ")

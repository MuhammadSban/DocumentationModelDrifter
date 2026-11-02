# checks that the tester logs each call's time, so one full run can be timed call by call (phase4.md v1)

import io

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

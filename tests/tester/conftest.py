# runs a fake target system on a local port that answers like a system meeting the contract, with switches to break it

import copy
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

import pytest

from Tester.pod_tests import CASES, REPOSITORY

BY_REQUEST = {(c["request"]["commit_id"], c["request"].get("base_commit")): c for c in CASES.values()}
CODE = {"basis": "fake line coverage", "covered": 3, "total": 10}


class FakeTarget:
    # holds the fake system's switches and saved results; url is its /system base
    def __init__(self):
        self.features = None  # None leaves features out of /health
        self.health_status = 200
        self.analyze_status = None  # a status every /analyze answers with instead of a result
        self.analyze_delay = 0.0
        self.break_case = None  # a case whose changes come back empty
        self.setup_answer = (201, None)
        self.saved = {}
        self.url = ""

    def analyze(self, raw: bytes):
        if self.analyze_status:
            return self.analyze_status, {"code": "ANALYSIS_FAILED", "message": "down"}
        time.sleep(self.analyze_delay)
        invalid = 400, {"code": "INVALID_REQUEST", "message": "bad request"}
        try:
            request = json.loads(raw)
        except ValueError:
            return invalid
        if not isinstance(request, dict) or not isinstance(request.get("commit_id"), str) \
                or not isinstance(request.get("repository"), str) or "/" not in request["repository"]:
            return invalid
        if request["repository"] != REPOSITORY:
            return 404, {"code": "REPOSITORY_NOT_FOUND", "message": "no such repository"}
        case = BY_REQUEST.get((request["commit_id"], request.get("base_commit")))
        if case is None:
            return 404, {"code": "COMMIT_NOT_FOUND", "message": "no such commit"}
        expected = copy.deepcopy(case["expected"])
        if case["case"] == self.break_case:
            expected["changes"] = []
        body = {**expected, "analysis_id": uuid.uuid4().hex, "created_at": "now", "repository": REPOSITORY,
                "tool_version": "fake"}
        self.saved[body["analysis_id"]] = body
        return 200, body


def _handler(fake: FakeTarget):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.partition("?")[0]
            if path == "/system/health":
                health = {"config_version": "mapping-v1.1", "status": "ok", "tool_version": "fake"}
                if fake.features is not None:
                    health["features"] = fake.features
                self._send(fake.health_status, health)
            elif path.startswith("/system/analysis/"):
                found = fake.saved.get(unquote(path[len("/system/analysis/"):]))
                if found:
                    self._send(200, found)
                else:
                    self._send(404, {"code": "ANALYSIS_NOT_FOUND", "message": "unknown id"})
            elif path == "/system/test/report":
                self._send(200, {"coverage": {"code": CODE}, "session_id": "any"})
            else:
                self._send(404, {"message": "no route", "source": "system"})

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path == "/system/analyze":
                self._send(*fake.analyze(raw))
            elif self.path == "/system/test/setup":
                status, body = fake.setup_answer
                self._send(status, body or {"session_id": json.loads(raw)["session_id"]})
            else:
                self._send(404, {"message": "no route", "source": "system"})

    return Handler


@pytest.fixture
def fake():
    target = FakeTarget()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(target))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    target.url = f"http://127.0.0.1:{server.server_address[1]}/system"
    yield target
    server.shutdown()
    server.server_close()


@pytest.fixture
def closed_url():
    # gives a URL on a port nothing listens on
    server = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    port = server.server_address[1]
    server.server_close()
    return f"http://127.0.0.1:{port}/system"

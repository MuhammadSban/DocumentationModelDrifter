# serves the tester under /tester: the course's POST /test/setup, POST /test/run and GET /test/report
# (pod-tester.openapi.yml), plus the /tester page, its test catalog, its live progress and the pytest group runner

from __future__ import annotations

import re
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from Tester import client, pod_tests, unit_tests
from Tester.client import NoReply

# fills in Team 16's system base URL once they share it, for example https://host/system; empty hides it on the page
TEAM16_SYSTEM_URL = ""

# matches a system base URL with no query, fragment or credentials (SetupRequest.target_url)
TARGET_URL = re.compile(r"^https?://[^\s?#@]+$")
SOURCES = ("tester", "system", "communication", "unknown")
PAGE = Path(__file__).resolve().parent / "page.html"

router = APIRouter(prefix="/tester", tags=["tester"])

# holds sessions in memory, cleared by a restart as the contract allows (§2)
SESSIONS: dict[str, dict] = {}
LOCK = threading.Lock()


def _error(status: int, message: str, source: str = "tester") -> JSONResponse:
    # answers with the course's test-route error body
    return JSONResponse(status_code=status, content={"message": message, "source": source})


async def _object(request: Request) -> dict:
    # reads a JSON object body, {} when the body is missing or not an object
    try:
        body = await request.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


@router.post("/test/setup", status_code=201)
async def test_setup(request: Request):
    # creates a session and waits for the target's system setup, passing a failure through unchanged
    target = (await _object(request)).get("target_url")
    if not isinstance(target, str) or not TARGET_URL.match(target):
        return _error(400, "target_url is required: a system base URL such as https://host/system")
    target = target.rstrip("/")
    session_id = str(uuid.uuid4())
    try:
        reply = await run_in_threadpool(client.call, "POST", target + "/test/setup",
                                        {"session_id": session_id, "setup": {}})
    except NoReply as exc:
        return _error(500, f"system setup gave no answer: {exc}", "communication")
    if not 200 <= reply.status < 300:
        body = reply.body if isinstance(reply.body, dict) else {}
        message = body.get("message") if isinstance(body.get("message"), str) and body.get("message") \
            else f"system setup answered {reply.status}"
        source = body.get("source") if body.get("source") in SOURCES else "system"
        return _error(reply.status, message, source)
    with LOCK:
        SESSIONS[session_id] = {"report": None, "results": [], "state": "ready", "target_url": target}
    return {"session_id": session_id}


@router.post("/test/run")
async def test_run(request: Request):
    # runs the test list once for a session and returns the complete report
    session_id = (await _object(request)).get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return _error(400, "session_id is required")
    with LOCK:
        session = SESSIONS.get(session_id)
        if session is None:
            return _error(404, f"session {session_id} is unknown")
        if session["state"] != "ready":
            return _error(409, f"session {session_id} already ran or is running")
        session["state"] = "running"
    try:
        # appends each result to the session as it is decided, so GET /tester/progress can show the run live
        report = await run_in_threadpool(pod_tests.run_suite, session["target_url"], session_id,
                                         on_result=session["results"].append)
    except Exception as exc:
        session["state"] = "done"
        return _error(500, f"tester aborted: {type(exc).__name__}: {exc}")
    session.update(report=report, state="done")
    return report


@router.get("/test/report")
def test_report(session_id: str | None = None):
    # returns a session's stored report without running tests
    if not session_id:
        return _error(400, "session_id query parameter is required")
    session = SESSIONS.get(session_id)
    if session is None:
        return _error(404, f"session {session_id} is unknown")
    if session["state"] != "done":
        return _error(409, f"the suite of session {session_id} has not ended, retry later")
    if session["report"] is None:
        return _error(500, "the tester aborted before storing any results")
    return session["report"]


@router.get("/progress", include_in_schema=False)
def progress(session_id: str | None = None):
    # returns a session's state and the results decided so far, polled by the page during a run
    if not session_id:
        return _error(400, "session_id query parameter is required")
    session = SESSIONS.get(session_id)
    if session is None:
        return _error(404, f"session {session_id} is unknown")
    return {"results": list(session["results"]), "session_id": session_id, "state": session["state"]}


@router.get("", include_in_schema=False)
def page() -> FileResponse:
    # serves the page that lists and runs the tests
    return FileResponse(PAGE, media_type="text/html")


@router.get("/catalog", include_in_schema=False)
def catalog() -> dict:
    # lists the pod tests, the pytest groups and the preset targets for the page
    return {
        "pod": pod_tests.catalog(),
        "team16_url": TEAM16_SYSTEM_URL,
        "unit_groups": [{"key": key, "title": title} for key, title in unit_tests.GROUPS.items()],
    }


@router.post("/unit/{group}", include_in_schema=False)
def unit(group: str):
    # runs one pytest group, 404 for a folder the page does not offer
    if group not in unit_tests.GROUPS:
        return _error(404, f"unknown test group {group}")
    return unit_tests.run_group(group)

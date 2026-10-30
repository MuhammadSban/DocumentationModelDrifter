# serves the course tester's /system/test routes: open a session, then report the line coverage since it opened

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

from coverage import Coverage
from coverage.python import PythonFileReporter
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PACKAGE = "GitHub_Connector"
PACKAGE_DIR = Path(__file__).resolve().parent
# leaves out this file, so a report never counts the lines that build it
UNCOUNTED = frozenset({"course.py"})

# words the report's basis, the reference service's sentence with our package and method
BASIS = (
    f"Executable source lines of the {PACKAGE} package's v1 modules, the course routes excepted, "
    "executed while handling requests since this session was set up (coverage.py statement lines, Python line events, line coverage)"
)


class TestSetupRequest(BaseModel):
    # copies the reference service's request model, name and limits included
    __test__ = False  # keeps pytest from collecting the class by its name

    session_id: str = Field(min_length=1, max_length=200)
    setup: dict[str, Any] = Field(default_factory=dict)


def course_error(status: int, message: str) -> JSONResponse:
    # answers with the course routes' own error body, never the analyze ErrorBody
    return JSONResponse(status_code=status, content={"message": message, "source": "system"})


def describe(error: dict) -> str:
    # words a validation error on POST /test/setup the way the reference service does
    loc = [part for part in error.get("loc", ()) if part != "body"]
    kind = error.get("type", "")
    if kind == "json_invalid":
        return "body has the wrong type"
    if not loc:
        return "body is required" if kind == "missing" else "body has the wrong type"
    field = str(loc[0])
    if kind == "missing":
        return f"{field} is required"
    if kind in ("string_too_short", "string_too_long"):
        return f"{field}: {error.get('msg', '')}"
    return f"{field} has the wrong type"


# --- coverage --------------------------------------------------------


class LineMonitor:
    # records which package lines ran, and in which epoch, through sys.monitoring line events
    # mutes each line after it fires, until the next setup starts a new epoch and re-arms it

    def __init__(self, root: Path) -> None:
        self._prefix = str(root) + os.sep
        self._latest: dict[tuple[str, int], int] = {}
        self._epoch = 0
        self._tool: int | None = None
        # serialises epoch changes with line records, reentrant because this file's own lines fire inside it
        self._lock = threading.RLock()

    def new_epoch(self) -> int:
        # starts counting again for a session opening now, turning monitoring on the first time
        with self._lock:
            if self._tool is None:
                self._tool = self._register()
            self._epoch += 1
            sys.monitoring.restart_events()
            return self._epoch

    def lines_since(self, epoch: int) -> dict[str, set[int]]:
        # groups the lines that ran in this epoch or later by file
        found: dict[str, set[int]] = {}
        with self._lock:
            latest = list(self._latest.items())
        for (path, line), seen in latest:
            if seen >= epoch:
                found.setdefault(path, set()).add(line)
        return found

    def _register(self) -> int:
        # takes the first free monitoring tool id, coverage tools may already hold one, 5 is CPython's optimizer
        mon = sys.monitoring
        for tool in (mon.COVERAGE_ID, 3, 4):
            try:
                mon.use_tool_id(tool, "drifter-course-coverage")
            except ValueError:
                continue
            mon.register_callback(tool, mon.events.LINE, self._on_line)
            mon.set_events(tool, mon.events.LINE)
            return tool
        raise RuntimeError("no free sys.monitoring tool id for course coverage")

    def _on_line(self, code, line: int):
        # notes a package line under the current epoch, then mutes that line until the next epoch
        if code.co_filename.startswith(self._prefix):
            with self._lock:
                self._latest[(code.co_filename, line)] = self._epoch
        return sys.monitoring.DISABLE


class Statements:
    # counts the package's executable lines the way coverage.py does, parsing each file once

    def __init__(self, root: Path) -> None:
        self._root = root
        # supplies coverage.py's default exclusions, never started, so it measures nothing itself
        self._coverage = Coverage(data_file=None, config_file=False)
        self._parsed: dict[str, tuple[PythonFileReporter, set[int]]] = {}

    def files(self) -> list[str]:
        # lists the counted files of the /system app, leaving out UNCOUNTED and bytecode caches
        found = self._root.rglob("*.py")
        return sorted(str(p) for p in found if "__pycache__" not in p.parts and p.name not in UNCOUNTED)

    def reporter(self, path: str) -> tuple[PythonFileReporter, set[int]]:
        # parses a file once, the deployed source never changes while the process runs
        if path not in self._parsed:
            reporter = PythonFileReporter(path, coverage=self._coverage)
            self._parsed[path] = (reporter, set(reporter.lines()))
        return self._parsed[path]

    def count(self, executed: dict[str, set[int]]) -> tuple[int, int]:
        # returns (covered, total), mapping each executed line to the statement it belongs to
        covered = total = 0
        for path in self.files():
            reporter, statements = self.reporter(path)
            total += len(statements)
            if path in executed:
                covered += len(reporter.translate_lines(executed[path]) & statements)
        return covered, total


class Sessions:
    # holds open sessions in memory, lost on restart like run files

    def __init__(self) -> None:
        self._monitor = LineMonitor(PACKAGE_DIR)
        self._statements = Statements(PACKAGE_DIR)
        self._opened: dict[str, int] = {}
        self._lock = threading.Lock()

    def open(self, session_id: str) -> bool:
        # opens a session, False when the id is already taken
        with self._lock:
            if session_id in self._opened:
                return False
            self._opened[session_id] = self._monitor.new_epoch()
            return True

    def report(self, session_id: str) -> dict | None:
        # builds the reference service's report shape, None for an unknown session
        epoch = self._opened.get(session_id)
        if epoch is None:
            return None
        covered, total = self._statements.count(self._monitor.lines_since(epoch))
        return {
            "session_id": session_id,
            "coverage": {"code": {"covered": covered, "total": total, "basis": BASIS}},
        }


SESSIONS = Sessions()
router = APIRouter(prefix="/test", tags=["testing"])


@router.post("/setup", status_code=201)
def test_setup(request: TestSetupRequest):
    # opens a session, 409 when the id was already set up
    if not SESSIONS.open(request.session_id):
        return course_error(409, f"session {request.session_id} already exists")
    return {"session_id": request.session_id}


@router.get("/report")
def test_report(session_id: str | None = None):
    # reports a session's coverage, 400 without an id and 404 for one never set up
    if not session_id:
        return course_error(400, "session_id query parameter is required")
    found = SESSIONS.report(session_id)
    if found is None:
        return course_error(404, f"session {session_id} is unknown")
    return found

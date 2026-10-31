# lists the pod's tests T-01 to T-33 (pod-contract.md §4) and runs them once against one target system

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from Tester import client
from Tester.client import NoReply, Reply

# caps one tester run, contract §6
RUN_LIMIT = 600.0

GOLDEN = json.loads(
    (Path(__file__).resolve().parents[2] / "docs" / "contract" / "golden-outputs.json").read_text(encoding="utf-8")
)
REPOSITORY = GOLDEN["fixture_repo"]
CASES = {case["case"]: case for case in GOLDEN["cases"]}

# names the fields T-01 to T-17 compare with the golden answer; issues are judged only in T-18 to T-21 (contract §3)
COMPARED = ("head_commit", "base_commit", "config_version", "status", "error", "changes", "skipped", "unmapped")

COMPONENTS = tuple(f"C{i}" for i in range(1, 8))
CRITERIA = tuple(f"AC-{i:02d}" for i in range(1, 11))

LIMIT_REACHED = "tester run limit reached"
PENDING = "expected answers not yet published"

# tells a missing field apart from a null one when comparing answers
MISSING = object()


class Fail(Exception):
    # ends a test whose answer could be evaluated and differs from what the contract expects
    pass


class TargetError(Exception):
    # ends a test whose target answered with a 5xx, which the course counts as error with source system
    pass


class LimitReached(Exception):
    # ends the test in progress once the run limit is reached (contract §6)
    pass


@dataclass(frozen=True)
class PodTest:
    # describes one row of contract §4: what it covers, what it needs, and how it is checked
    id: str
    title: str
    components: tuple[str, ...]
    criteria: tuple[str, ...]
    check: Callable[[Run], str] | None = None
    feature: str | None = None
    pending: bool = False
    skip: str | None = None


@dataclass
class Result:
    # holds one test's outcome, and whether the target answered the test's calls (contract §5 coverage)
    outcome: str
    message: str
    source: str | None = None
    answered: bool = True

    def entry(self, test_id: str) -> dict:
        # writes the result as a TestResult of the suite report
        out = {"test_id": test_id, "outcome": self.outcome, "message": self.message}
        if self.source:
            out["source"] = self.source
        return out


class Run:
    # sends one run's calls to the target, each capped by the call timeout and by the time left in the run
    def __init__(self, target_url: str, limit: float):
        self.target = target_url.rstrip("/")
        self.deadline = time.monotonic() + limit

    def left(self) -> float:
        return self.deadline - time.monotonic()

    def send(self, method: str, path: str, payload: object = None, raw: bytes | None = None) -> Reply:
        # sends one call; raises LimitReached past the run limit and TargetError on a 5xx
        if self.left() <= 0:
            raise LimitReached()
        try:
            reply = client.call(method, self.target + path, payload, raw,
                                timeout=min(client.CALL_TIMEOUT, self.left()))
        except NoReply:
            # counts a timeout that ends at the run limit as the limit, allowing for clock rounding
            if self.left() <= 0.05:
                raise LimitReached() from None
            raise
        if reply.status >= 500:
            raise TargetError(f"{method} {path} answered {reply.status}: {_short(reply)}")
        return reply

    def analyze(self, case: str) -> Reply:
        # posts a golden case's request on the fixture repository
        return self.send("POST", "/analyze", {"repository": REPOSITORY, **CASES[case]["request"]})

    def analysis(self, analysis_id: str) -> Reply:
        return self.send("GET", "/analysis/" + quote(analysis_id, safe=""))


def _short(reply: Reply) -> str:
    # shortens a body for a message
    text = " ".join(reply.text.split())
    return text[:200] + ("..." if len(text) > 200 else "") or "(empty body)"


def _body(reply: Reply, status: int = 200) -> dict:
    # returns the JSON object of an answer with the expected status, or fails the test
    if reply.status != status or not isinstance(reply.body, dict):
        raise Fail(f"expected {status} with a JSON object, got {reply.status}: {_short(reply)}")
    return reply.body


def _id(body: dict) -> str:
    analysis_id = body.get("analysis_id")
    if not isinstance(analysis_id, str) or not analysis_id:
        raise Fail("the answer has no analysis_id")
    return analysis_id


def _fields(body: dict) -> dict:
    return {name: body.get(name, MISSING) for name in COMPARED}


def _findings(issues: object) -> object:
    # drops each finding's explanation, which is never compared (contract §3)
    if not isinstance(issues, list):
        return issues
    return [{k: v for k, v in f.items() if k != "explanation"} if isinstance(f, dict) else f for f in issues]


def golden(case: str) -> Callable[[Run], str]:
    # checks a case's compared fields against golden-outputs.json
    def check(run: Run) -> str:
        got, want = _fields(_body(run.analyze(case))), _fields(CASES[case]["expected"])
        differ = [name for name in COMPARED if got[name] != want[name]]
        if differ:
            raise Fail(f"{case}: {', '.join(differ)} differ from the golden answer")
        return f"{case} matches the golden answer"
    return check


def rejected(status: int, code: str, send: Callable[[Run], Reply]) -> Callable[[Run], str]:
    # checks that a bad request gets the expected status and error code
    def check(run: Run) -> str:
        reply = send(run)
        got = reply.body.get("code") if isinstance(reply.body, dict) else None
        if reply.status != status or got != code:
            raise Fail(f"expected {status} {code}, got {reply.status} {got or _short(reply)}")
        return f"{status} {code}"
    return check


def issues(case: str) -> Callable[[Run], str]:
    # checks a case's findings against golden-outputs.json, explanations left out
    def check(run: Run) -> str:
        got = _findings(_body(run.analyze(case)).get("issues", MISSING))
        if got != _findings(CASES[case]["expected"]["issues"]):
            raise Fail(f"{case}: issues differ from the golden answer")
        return f"{case}: issues match the golden answer"
    return check


def retrieve_saved(run: Run) -> str:
    posted = _body(run.analyze("c1-impl-only"))
    if _body(run.analysis(_id(posted))) != posted:
        raise Fail("GET returned a different body than the POST")
    return "GET returns the saved c1 result unchanged"


def distinct_and_durable(run: Run) -> str:
    first, second = _body(run.analyze("c2-add-mod-del")), _body(run.analyze("c2-add-mod-del"))
    if _id(first) == _id(second):
        raise Fail("both c2 runs got the same analysis_id")
    for posted in (first, second):
        if _body(run.analysis(_id(posted))) != posted:
            raise Fail(f"GET {_id(posted)} differs from its POST")
    return "two c2 runs got distinct ids, and both read back unchanged"


def repeatable(run: Run) -> str:
    for case in ("c4-categories", "c1-impl-only"):
        first = _fields(_body(run.analyze(case)))
        for attempt in range(2, 6):
            fields = _fields(_body(run.analyze(case)))
            differ = [name for name in COMPARED if fields[name] != first[name]]
            if differ:
                raise Fail(f"{case}: run {attempt} differs from run 1 in {', '.join(differ)}")
    return "five runs each of c4 and c1 give identical compared fields"


def pending_review(run: Run) -> str:
    findings = []
    for case in ("c8-missing-doc", "c1-impl-only"):
        found = _body(run.analyze(case)).get("issues")
        if not isinstance(found, list):
            raise Fail(f"{case}: issues is not a list")
        findings += found
    if not findings:
        raise Fail("c8 and c1 gave no findings to check")
    late = [f for f in findings if not isinstance(f, dict) or f.get("verification_status") != "PENDING_REVIEW"]
    if late:
        raise Fail(f"{len(late)} of {len(findings)} findings do not start PENDING_REVIEW")
    return f"all {len(findings)} findings start PENDING_REVIEW"


def _row(test_id: str, title: str, components: str, criteria: str, check=None, **kw) -> PodTest:
    return PodTest(test_id, title, tuple(components.split()), tuple(criteria.split()), check, **kw)


C1_SHA = CASES["c1-impl-only"]["request"]["commit_id"]
DRIFT = dict(feature="model_drift", pending=True)
PROSE = dict(feature="prose_detector")

# lists contract §4 in order; titles and coverage lists are copied from it
TESTS = [
    _row("T-01", "Implementation-only change, default base", "C1 C2 C3 C5", "AC-01", golden("c1-impl-only")),
    _row("T-02", "Added, modified and deleted files", "C1 C2 C3 C5", "AC-01", golden("c2-add-mod-del")),
    _row("T-03", "Rename detection", "C1 C2 C3 C5", "AC-01", golden("c3-rename")),
    _row("T-04", "Requirement/specification/design/architecture categories", "C1 C2 C3 C5", "AC-01",
         golden("c4-categories")),
    _row("T-05", "Unsupported binary files are skipped", "C1 C2 C3 C5", "AC-01", golden("c6-binary")),
    _row("T-06", "Explicit base_commit across several commits", "C1 C2 C3 C5", "AC-01",
         golden("c0-to-c3-explicit-base")),
    _row("T-07", "Root commit boundary", "C1 C2 C3 C5", "AC-01", golden("c0-initial")),
    _row("T-08", "Missing commit_id", "C1", "AC-07", rejected(
        400, "INVALID_REQUEST", lambda run: run.send("POST", "/analyze", {"repository": REPOSITORY}))),
    _row("T-09", "Malformed JSON", "C1", "AC-07", rejected(
        400, "INVALID_REQUEST", lambda run: run.send("POST", "/analyze", raw=b'{"repository": '))),
    _row("T-10", "Invalid repository format", "C1", "AC-07", rejected(
        400, "INVALID_REQUEST",
        lambda run: run.send("POST", "/analyze", {"repository": "not-a-repository", "commit_id": C1_SHA}))),
    _row("T-11", "Incorrectly typed commit_id", "C1", "AC-07", rejected(
        400, "INVALID_REQUEST",
        lambda run: run.send("POST", "/analyze", {"repository": REPOSITORY, "commit_id": 12345}))),
    _row("T-12", "Nonexistent repository", "C1 C2", "AC-08", rejected(
        404, "REPOSITORY_NOT_FOUND",
        lambda run: run.send("POST", "/analyze",
                             {"repository": REPOSITORY + "-does-not-exist", "commit_id": C1_SHA}))),
    _row("T-13", "Nonexistent commit", "C1 C2", "AC-08", rejected(
        404, "COMMIT_NOT_FOUND",
        lambda run: run.send("POST", "/analyze", {"repository": REPOSITORY, "commit_id": "f" * 40}))),
    _row("T-14", "Retrieve saved analysis", "C1 C6", "AC-06", retrieve_saved),
    _row("T-15", "Unknown analysis_id", "C1 C6", "AC-06 AC-08", rejected(
        404, "ANALYSIS_NOT_FOUND", lambda run: run.analysis(f"unknown-{uuid.uuid4().hex}"))),
    _row("T-16", "Distinct, durable run files", "C1 C2 C3 C5 C6", "AC-06", distinct_and_durable),
    _row("T-17", "Five-run repeatability", "C1 C2 C3 C5", "AC-10", repeatable),
    _row("T-18", "Missing mapped documentation finding", "C4", "AC-02", issues("c8-missing-doc"), **PROSE),
    _row("T-19", "Unchanged mapped documentation finding", "C4", "AC-02", issues("c1-impl-only"), **PROSE),
    _row("T-20", "Code and documentation updated together", "C4", "AC-03", issues("c7-code-and-doc"), **PROSE),
    _row("T-21", "New findings start PENDING_REVIEW", "C4 C5", "AC-04", pending_review, **PROSE),
    _row("T-22", "Authorized and unauthorized review decisions", "C7", "AC-05", skip="Phase 5"),
    _row("T-23", "Read-only analysis, no repository code execution", "C2", "AC-09", skip="checked by inspection"),
    _row("T-24", "/analyze at L0: aligned: true, three empty lists", "C1 C2 C3 C4 C5", "AC-03", **DRIFT),
    _row("T-25", "/analyze at L1: aligned: true", "C1 C2 C3 C4 C5", "AC-03", **DRIFT),
    _row("T-26", "/analyze at L2: one structural ADDED", "C1 C2 C3 C4 C5", "AC-02", **DRIFT),
    _row("T-27", "/analyze at L3: one structural REMOVED", "C1 C2 C3 C4 C5", "AC-02", **DRIFT),
    _row("T-28", "/analyze at L4: behavioral ADDED state and transition", "C1 C2 C3 C4 C5", "AC-02", **DRIFT),
    _row("T-29", "/analyze at L5: aligned: true", "C1 C2 C3 C4 C5", "AC-03", **DRIFT),
    _row("T-30", "/analyze at L6: one ownership VIOLATION", "C1 C2 C3 C4 C5", "AC-02", **DRIFT),
    _row("T-31", "/analyze at L7: one structural ADDED", "C1 C2 C3 C4 C5", "AC-02", **DRIFT),
    _row("T-32", "/analyze at L-pre: drift: null, drift_error.code MODELS_NOT_FOUND", "C1 C2 C3 C4 C5", "AC-08",
         **DRIFT),
    _row("T-33", "/generate at L0: structural.json, behavioral.json and scope.json byte-equal to the committed "
         "/models", "C1 C2 C4", "AC-10", **DRIFT),
]


def run_suite(target_url: str, session_id: str, limit: float | None = None,
              on_result: Callable[[dict], None] | None = None) -> dict:
    # runs every test once, in order, and returns the suite report of pod-tester.openapi.yml;
    # on_result receives each TestResult entry as soon as it is decided, for a live view of the run
    run = Run(target_url, RUN_LIMIT if limit is None else limit)
    features, health_failure = _features(run)
    results, components, criteria = [], set(), set()
    for test in TESTS:
        result = _run_one(test, run, features, health_failure)
        results.append(result.entry(test.id))
        if on_result is not None:
            on_result(results[-1])
        if result.answered and (result.outcome in ("pass", "fail") or result.source == "system"):
            components.update(test.components)
            criteria.update(test.criteria)
    return {
        "coverage": {
            "code": _code_coverage(run, session_id),
            "component": _measure(components, COMPONENTS, "components C1 to C7 exercised by a test the target "
                                  "answered (pod-contract.md section 5)"),
            "system": _measure(criteria, CRITERIA, "criteria AC-01 to AC-10 exercised by a test the target "
                               "answered (pod-contract.md section 5)"),
        },
        "results": results,
        "session_id": session_id,
        "target_url": run.target,
    }


def _run_one(test: PodTest, run: Run, features: list, health_failure: tuple | None) -> Result:
    # decides a test's outcome: limit, fixed skip, pending, missing feature, then its check
    if run.left() <= 0:
        return Result("skip", LIMIT_REACHED, answered=False)
    if test.skip:
        return Result("skip", test.skip, answered=False)
    if test.pending:
        return Result("skip", PENDING, answered=False)
    if test.feature:
        if health_failure:
            source, message = health_failure
            return Result("error", f"features unknown, {message}", source, answered=False)
        if test.feature not in features:
            return Result("skip", f"target does not implement {test.feature}", answered=False)
    try:
        return Result("pass", test.check(run))
    except Fail as exc:
        return Result("fail", str(exc))
    except TargetError as exc:
        return Result("error", str(exc), "system")
    except LimitReached:
        return Result("error", LIMIT_REACHED, "tester", answered=False)
    except NoReply as exc:
        return Result("error", f"no answer from the target: {exc}", "communication", answered=False)
    except Exception as exc:
        return Result("error", f"tester failed: {type(exc).__name__}: {exc}", "tester", answered=False)


def _features(run: Run) -> tuple[list, tuple | None]:
    # reads GET /health once; absent features mean ["prose_detector"] (contract §1), a failure leaves them unknown
    try:
        reply = run.send("GET", "/health")
    except NoReply as exc:
        return [], ("communication", f"GET /health gave no answer: {exc}")
    except TargetError as exc:
        return [], ("system", str(exc))
    except LimitReached:
        return [], ("tester", LIMIT_REACHED)
    body = reply.body if isinstance(reply.body, dict) else {}
    if reply.status != 200 or body.get("status") != "ok":
        return [], ("system", f"GET /health answered {reply.status}: {_short(reply)}")
    features = body.get("features", ["prose_detector"])
    if not isinstance(features, list):
        return [], ("system", "GET /health: features is not a list")
    return features, None


def _code_coverage(run: Run, session_id: str) -> dict:
    # copies the code measure from the system's GET /test/report, or reports it unavailable with a reason
    try:
        reply = run.send("GET", "/test/report?session_id=" + quote(session_id, safe=""))
    except LimitReached:
        return _unavailable(LIMIT_REACHED)
    except (NoReply, TargetError) as exc:
        return _unavailable(f"system GET /test/report failed: {exc}")
    coverage = reply.body.get("coverage") if isinstance(reply.body, dict) else None
    code = coverage.get("code") if isinstance(coverage, dict) else None
    if reply.status != 200 or not _is_measure(code):
        return _unavailable(f"system GET /test/report answered {reply.status} without a code measure")
    return code


def _is_measure(value: object) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("basis"), str) or not value["basis"]:
        return False
    counts = value.get("covered", MISSING), value.get("total", MISSING)
    if all(c is None for c in counts):
        return True
    if not all(isinstance(c, int) and not isinstance(c, bool) and c >= 0 for c in counts):
        return False
    return counts[0] <= counts[1]


def _unavailable(reason: str) -> dict:
    return {"basis": f"code coverage unavailable: {reason}", "covered": None, "total": None}


def _measure(covered: set, every: tuple, basis: str) -> dict:
    return {"basis": basis, "covered": len(covered & set(every)), "total": len(every)}


def catalog() -> list[dict]:
    # lists the tests for the /tester page
    return [{"components": list(t.components), "criteria": list(t.criteria), "feature": t.feature, "id": t.id,
             "pending": t.pending, "skip": t.skip, "title": t.title} for t in TESTS]

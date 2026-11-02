# serves the v1 API under /system: analyze and the run store, plus the course routes from course.py, and the console at /

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response

from Frontend import model_drift
from Frontend.model_loader import OWNERSHIP_FILE, SCOPE_FILE, STRUCTURAL_FILE, models_from_dicts
from Frontend.model_viewer import render
from GitHub_Connector import course, rules, runs
from Tester import api as tester
from GitHub_Connector.analysis import analyze, validate
from GitHub_Connector.fetch import fetch
from GitHub_Connector.schemas import (
    AnalysisError,
    AnalysisRequest,
    AnalysisResult,
    ErrorBody,
    ErrorCode,
)
from GitHub_Connector.settings import build_label, get_settings

# maps every contract error code to its HTTP status, the one table all failures go through
STATUS_FOR = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.REPOSITORY_NOT_FOUND: 404,
    ErrorCode.COMMIT_NOT_FOUND: 404,
    ErrorCode.ANALYSIS_NOT_FOUND: 404,
    ErrorCode.ANALYSIS_FAILED: 500,
    ErrorCode.STORAGE_FAILED: 500,
}


_ERRORS = {400: {"model": ErrorBody}, 404: {"model": ErrorBody}, 500: {"model": ErrorBody}}

app = FastAPI(
    title="DocumentationDrifter",
    openapi_url="/system/openapi.json",
    docs_url=None,  # serves the contract's routes and the console, no docs pages
    redoc_url=None,
)
router = APIRouter(prefix="/system")

# finds the console beside the connector, Source/ ships whole in the image
FRONTEND = Path(__file__).resolve().parents[1] / "Frontend"
CONSOLE = FRONTEND / "index.html"


def _json(data: bytes, status: int = 200) -> Response:
    # returns bytes as they are, so GET serves the saved run unchanged
    return Response(content=data, status_code=status, media_type="application/json")


@app.exception_handler(AnalysisError)
def _analysis_error(_, exc: AnalysisError) -> JSONResponse:
    # turns a failed analysis into its status and an ErrorBody
    return JSONResponse(status_code=STATUS_FOR[exc.code], content=exc.body().model_dump(mode="json"))


@app.exception_handler(Exception)
def _crash(request: Request, exc: Exception) -> JSONResponse:
    # answers any unexpected failure as 500 in the error shape of the route's family, never a bare 500
    if request.url.path.startswith(router.prefix + course.router.prefix + "/"):
        return course.course_error(500, "The request failed unexpectedly")
    return _analysis_error(None, AnalysisError(ErrorCode.ANALYSIS_FAILED, "The analysis failed unexpectedly"))


@app.exception_handler(RequestValidationError)
def _bad_request(request: Request, exc: RequestValidationError) -> JSONResponse:
    # answers FastAPI's own validation failures as 400, never 422, in the error shape of the route's family
    if request.url.path.startswith(router.prefix + course.router.prefix + "/"):
        return course.course_error(400, course.describe(exc.errors()[0]))
    err = AnalysisError(ErrorCode.INVALID_REQUEST, _describe(exc.errors()[0]))
    return _analysis_error(None, err)


def _describe(error: dict) -> str:
    # words the first validation error the way a caller can act on
    loc = [part for part in error.get("loc", ()) if part != "body"]
    field = loc[0] if loc and isinstance(loc[0], str) else None
    if field is None or error.get("type") == "json_invalid":
        return "request body must be a JSON object"
    missing = error.get("type") == "missing" or error.get("input", ...) is None
    if missing and field in ("repository", "commit_id"):
        return f"{field} is required"
    return f"{field} has the wrong type"


@router.post("/analyze", response_model=AnalysisResult, responses=_ERRORS)
def post_analyze(request: AnalysisRequest) -> Response:
    # runs one analysis and returns the bytes that were saved
    return _json(runs.dump(analyze(request)))


@router.get("/analysis/{analysis_id:path}", response_model=AnalysisResult, responses={404: {}})
def get_analysis(analysis_id: str) -> Response:
    # serves a saved run byte for byte, any unknown or malformed id gets the same 404
    data = runs.load(analysis_id)
    if data is None:
        # matches the reference service's body for a run that doesn't exist (probed 2026-10-17)
        message = f"analysis {analysis_id} does not exist"
        return _analysis_error(None, AnalysisError(ErrorCode.ANALYSIS_NOT_FOUND, message))
    return _json(data)


@router.get("", include_in_schema=False)
def index() -> dict:
    # lists the routes for a person who opens plain /system, kept out of the OpenAPI document
    return {
        "service": "DocumentationDrifter",
        "routes": [
            "GET /system/health",
            "POST /system/analyze",
            "GET /system/analysis/{analysis_id}",
            "POST /system/test/setup",
            "GET /system/test/report?session_id=...",
        ],
    }


@router.get("/health")
def health() -> dict[str, object]:
    # answers the warm-up call, does no git work; model_drift lets testers skip the prose tests (contract §1)
    return {
        "status": "ok",
        "tool_version": build_label(),
        "config_version": rules.config_version(),
        "storage": "local",
        "features": ["model_drift"],
    }


@app.get("/", include_in_schema=False)
def console() -> FileResponse:
    # serves the console page, kept out of the OpenAPI document so the contract stays the same
    return FileResponse(CONSOLE, media_type="text/html")


@app.get("/app.css", include_in_schema=False)
def stylesheet() -> FileResponse:
    # serves the design the console and the model viewer share, the one file the page asks for
    return FileResponse(FRONTEND / "app.css", media_type="text/css")


@app.get("/models/view", include_in_schema=False)
def models_view(repository: str, commit_id: str) -> Response:
    # renders one commit's models as the page the console's Models view frames: the structural
    # model regenerated at that commit, the repository's own ownership rules beside it, and the
    # naive drift chip comparing the commit with the one before it. Kept out of the OpenAPI
    # document, being the console's own route and not part of the contract.
    #
    # A whole page, framed rather than injected: the console styles .dot, .row and .sub for its
    # watchlist, which are the classes the ownership map draws itself with.
    validate(AnalysisRequest(repository=repository, commit_id=commit_id))
    deadline = time.monotonic() + get_settings().analysis_deadline
    with fetch(repository, commit_id, None, deadline) as cmp:
        parsed = {
            name: model
            for name, model in model_drift.committed(cmp, cmp.head).items()
            if name in (OWNERSHIP_FILE, SCOPE_FILE)
        }
        changed: dict[str, bool] = {}
        note = None
        try:
            parsed[STRUCTURAL_FILE] = model_drift.snapshot(cmp, cmp.head)
            if cmp.base is not None:
                changed["structural"] = model_drift.drifted(
                    model_drift.snapshot(cmp, cmp.base), parsed[STRUCTURAL_FILE]
                )
        except model_drift.SnapshotFailed as exc:
            note = str(exc)
        models = models_from_dicts(parsed, f"{repository} @ {cmp.head[:7]}")
        verdict = model_drift.Verdict(head=cmp.head, base=cmp.base, changed=changed, note=note)
    return Response(render(models, verdict), media_type="text/html")


router.include_router(course.router)
app.include_router(router)
# serves the tester beside the system in one app (phase4.md Q7); course.py counts only this package's lines
app.include_router(tester.router)

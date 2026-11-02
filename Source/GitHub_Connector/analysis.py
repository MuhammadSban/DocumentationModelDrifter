# runs one analysis end to end, callable without HTTP by the API or a later Action

from __future__ import annotations

import re
import threading
import time
import uuid
from datetime import datetime, timezone

from drifter import check
from GitHub_Connector import rules, runs
from GitHub_Connector.fetch import fetch
from GitHub_Connector.schemas import (
    AnalysisError,
    AnalysisRequest,
    AnalysisResult,
    Category,
    Change,
    ChangeType,
    Drift,
    DriftErrorBody,
    ErrorBody,
    ErrorCode,
    GenerateResult,
    Skipped,
    Status,
)
from GitHub_Connector.settings import build_label, get_settings

# matches owner/name and 7-40 hex before any network call, \Z since $ would accept a trailing newline
REPOSITORY = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+\Z")
SHA = re.compile(r"^[0-9a-fA-F]{7,40}\Z")


def validate(request: AnalysisRequest) -> None:
    # rejects malformed input with INVALID_REQUEST, so garbage never reaches git
    def invalid(message: str) -> AnalysisError:
        return AnalysisError(ErrorCode.INVALID_REQUEST, message)

    if not REPOSITORY.match(request.repository):
        raise invalid("repository must use the format owner/name")
    if not SHA.match(request.commit_id):
        raise invalid("commit_id must be a 7-40 character hexadecimal commit SHA")
    if request.base_commit is not None and not SHA.match(request.base_commit):
        raise invalid("base_commit must be a 7-40 character hexadecimal commit SHA")


_slots_lock = threading.Lock()
_slots: tuple[int, threading.BoundedSemaphore] | None = None


def slot() -> threading.BoundedSemaphore:
    # hands out the shared semaphore that caps concurrent analyses at the configured limit
    global _slots
    limit = get_settings().max_concurrent
    with _slots_lock:
        if _slots is None or _slots[0] != limit:
            _slots = (limit, threading.BoundedSemaphore(limit))
        return _slots[1]


def analyze(request: AnalysisRequest) -> AnalysisResult:
    # runs one analysis in a slot, starting the deadline only once the slot is free
    validate(request)
    with slot():
        return _analyze(request, time.monotonic() + get_settings().analysis_deadline)


def _analyze(request: AnalysisRequest, deadline: float) -> AnalysisResult:
    # compares head against base, classifies each change, saves the run file once
    with fetch(request.repository, request.commit_id, request.base_commit, deadline) as cmp:
        changes = [
            Change(
                path=c.path,
                old_path=c.old_path,
                change_type=c.change_type,
                category=rules.classify(c.path),
            )
            for c in cmp.changes
        ]
        skipped = [Skipped(path=s.path, reason=s.reason) for s in cmp.skipped]
        drift, drift_error = _drift(cmp)
        # lists implementation paths with no mapping entry, a deletion excluded (v1.1 SPEC section 6.1)
        unmapped = [
            c.path for c in changes
            if c.category == Category.IMPLEMENTATION
            and c.change_type != ChangeType.DELETED
            and not rules.is_mapped(c.path)
        ]
        head, base = cmp.head, cmp.base
        status, error = Status.SUCCESS, None
        limit = rules.max_changed_files()
        if len(changes) > limit:
            # saves an ERROR result with empty lists, a 200 and not an HTTP error (v1.1 SPEC section 4, step 4)
            status = Status.ERROR
            error = ErrorBody(code="CHANGE_LIMIT_EXCEEDED", message=f"{len(changes)} changed files is over the limit of {limit}")
            changes, skipped, unmapped = [], [], []

    result = AnalysisResult(
        analysis_id="an-" + uuid.uuid4().hex,
        repository=request.repository,
        head_commit=head,
        base_commit=base,
        config_version=rules.config_version(),
        tool_version=build_label(),
        status=status,
        error=error,
        issues=[],  # stays empty, this system has no prose detector (contract deviation 1)
        drift=drift,
        drift_error=drift_error,
        changes=sorted(changes, key=lambda c: (c.path, c.old_path or "")),
        skipped=sorted(skipped, key=lambda s: s.path),
        unmapped=sorted(unmapped),
        created_at=_now(),
    )
    try:
        runs.save(result.analysis_id, runs.dump(result))
    except OSError as exc:
        raise AnalysisError(ErrorCode.STORAGE_FAILED, "The run file could not be saved") from exc
    return result


def generate(request: AnalysisRequest) -> GenerateResult:
    # builds the four /models files at the commit on a fresh clone, as drifter init would; a
    # no-verdict code such as PARSE_FAILED becomes ANALYSIS_FAILED, the route's only 500
    validate(request)
    with slot():
        deadline = time.monotonic() + get_settings().analysis_deadline
        with fetch(request.repository, request.commit_id, request.base_commit, deadline) as cmp:
            try:
                files = check.generate_models(cmp)
            except check.DriftError as exc:
                raise AnalysisError(ErrorCode.ANALYSIS_FAILED, f"{exc.code}: {exc.message}") from None
            return GenerateResult(repository=request.repository, head_commit=cmp.head,
                                  tool_version=build_label(), files=files)


def _drift(cmp) -> tuple[Drift | None, DriftErrorBody | None]:
    # checks the code against the committed models on the clone change detection already made.
    # It runs whatever status change detection reached, and a no-verdict code leaves status alone
    # and drift null, so a check that could not be completed is never read as aligned (spec 5.2)
    try:
        return Drift(**check.answer(check.read_sources(cmp))), None
    except check.DriftError as exc:
        return None, DriftErrorBody(**exc.body())


def _now() -> str:
    # formats the current time as ISO 8601 UTC with milliseconds and a Z
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

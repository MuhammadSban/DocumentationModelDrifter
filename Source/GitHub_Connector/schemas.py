# declares the v1 API contract, copied field for field from the reference service

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Category(str, Enum):
    # names the kind of file a change touches, as mapping-v1.1.yaml decides
    IMPLEMENTATION = "IMPLEMENTATION"
    DESIGN = "DESIGN"
    ARCHITECTURE = "ARCHITECTURE"
    SPECIFICATION = "SPECIFICATION"
    REQUIREMENT = "REQUIREMENT"
    DOCUMENTATION = "DOCUMENTATION"
    OTHER = "OTHER"


class ChangeType(str, Enum):
    # mirrors git's status letters, v1 never emits COPIED
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    RENAMED = "RENAMED"
    COPIED = "COPIED"
    TYPE_CHANGED = "TYPE_CHANGED"


class Status(str, Enum):
    # marks a run's outcome, ERROR only for CHANGE_LIMIT_EXCEEDED, saved like any result
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class IssueType(str, Enum):
    # names what a finding claims, the two the roadmap's file-level rule can reach
    OUTDATED_DOCUMENTATION = "OUTDATED_DOCUMENTATION"
    MISSING_DOCUMENTATION = "MISSING_DOCUMENTATION"


class ErrorCode(str, Enum):
    # lists the contract's failure codes (pod-contract.md section 7)
    INVALID_REQUEST = "INVALID_REQUEST"
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    COMMIT_NOT_FOUND = "COMMIT_NOT_FOUND"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    STORAGE_FAILED = "STORAGE_FAILED"


class AnalysisRequest(BaseModel):
    # carries one analysis ask, formats are checked by analyze() before any git work
    repository: str
    commit_id: str
    base_commit: str | None = None


class Change(BaseModel):
    # describes one changed path, old_path is set only for RENAMED
    path: str
    old_path: str | None = None
    change_type: ChangeType
    category: Category


class Skipped(BaseModel):
    # lists a changed path that could not be checked, with why
    path: str
    reason: str


class Finding(BaseModel):
    # flags one doc file for human review, never produced by this system (contract deviation 1)
    finding_id: str
    issue_type: str
    code_file: str
    documentation_file: str | None
    change_category: Category
    explanation: str
    verification_status: str


class DriftErrorCode(str, Enum):
    # lists the four reasons a check reaches no verdict (spec 5.2); none of them changes status
    MODELS_NOT_FOUND = "MODELS_NOT_FOUND"
    INVALID_MODELS = "INVALID_MODELS"
    PARSE_FAILED = "PARSE_FAILED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


class ModelDifference(BaseModel):
    # names one structural or behavioral difference, reported from the code's side
    change: str
    file: str
    id: str
    kind: str


class OwnershipViolation(BaseModel):
    # names one commit that changed a path whose owners do not include its author
    author: str
    change: str
    commit: str
    owners: list[str]
    path: str


class Drift(BaseModel):
    # carries the four-field answer, aligned only when all three lists are empty (spec 3.2)
    aligned: bool
    behavioral: list[ModelDifference]
    ownership: list[OwnershipViolation]
    structural: list[ModelDifference]


class DriftErrorBody(BaseModel):
    # says why there is no verdict, with drift null beside it
    code: DriftErrorCode
    message: str


class ErrorBody(BaseModel):
    # answers every failed request, nothing is saved alongside it; code is a plain string, as theirs is
    code: str
    message: str


class AnalysisResult(BaseModel):
    # holds one successful run, saved once and served back byte for byte
    analysis_id: str
    repository: str
    head_commit: str
    base_commit: str | None
    config_version: str
    tool_version: str
    status: Status
    error: ErrorBody | None
    issues: list[Finding]
    changes: list[Change]
    skipped: list[Skipped]
    unmapped: list[str]
    created_at: str
    # optional, this system only: the model check's answer, or null with a reason (deviation 2)
    drift: Drift | None = None
    drift_error: DriftErrorBody | None = None


class AnalysisError(Exception):
    # signals a failed analysis, the route maps code to an HTTP status

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def body(self) -> ErrorBody:
        # renders the error as the contract's ErrorBody
        return ErrorBody(code=self.code.value, message=self.message)

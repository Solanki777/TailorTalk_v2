"""
Pydantic models shared across the analysis pipeline:

    Upload -> Parse -> Rule Engine -> AI Analysis -> Report

Each stage reads/writes one of these shapes to a workspace folder
(storage/<workspace_id>/...) so every stage can be inspected, re-run,
or debugged independently.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# Stage 2: Parse
# ---------------------------------------------------------------------
class TestCase(BaseModel):
    """A single test case as found in an uploaded spec file."""

    id: str
    name: str
    method: Optional[str] = None
    endpoint: Optional[str] = None
    request_body: Optional[dict[str, Any]] = None
    headers: Optional[dict[str, Any]] = None
    expected_status: Optional[int] = None
    expected_response: Optional[dict[str, Any]] = None


class TestSpec(BaseModel):
    """The full parsed spec: metadata + every test case it contains."""

    test_suite: str = "Untitled Test Suite"
    version: str = "1.0"
    base_url: Optional[str] = None
    test_cases: list[TestCase] = Field(default_factory=list)


# ---------------------------------------------------------------------
# Stage 3: Rule Engine
# ---------------------------------------------------------------------
class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleFinding(BaseModel):
    test_case_id: Optional[str] = None
    rule: str
    severity: Severity
    message: str


class RuleEngineResult(BaseModel):
    total_test_cases: int
    findings: list[RuleFinding] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    source: str = "default"  # "default" (built-in checks) or "custom" (user-supplied rules)


# ---------------------------------------------------------------------
# Stage 3b: Custom (user-supplied) Rules
# ---------------------------------------------------------------------
class CustomRuleType(str, Enum):
    REQUIRED = "required"
    NOT_EMPTY = "not_empty"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    CONTAINS = "contains"
    REGEX = "regex"
    MIN = "min"
    MAX = "max"
    RANGE = "range"


class CustomRule(BaseModel):
    """
    One user-defined check, applied to every test case in the uploaded spec.

    `field` supports dot-notation into a test case's dict-valued fields,
    e.g. "headers.Authorization" or "request_body.user_id". Top-level
    fields are: id, name, method, endpoint, request_body, headers,
    expected_status, expected_response.
    """

    field: str
    type: CustomRuleType
    value: Any = None
    values: Optional[list[Any]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    severity: Severity = Severity.WARNING
    message: Optional[str] = None
    rule_id: Optional[str] = Field(default=None, alias="id")

    model_config = {"populate_by_name": True}


class CustomRuleSet(BaseModel):
    rules: list[CustomRule] = Field(default_factory=list)


# ---------------------------------------------------------------------
# Stage 4: AI Analysis
# ---------------------------------------------------------------------
class AIFinding(BaseModel):
    category: str
    severity: Severity
    message: str


class AIAnalysisResult(BaseModel):
    summary: str
    coverage_gaps: list[str] = Field(default_factory=list)
    findings: list[AIFinding] = Field(default_factory=list)
    model_used: Optional[str] = None
    skipped_reason: Optional[str] = None


# ---------------------------------------------------------------------
# Workspace-level response (what the API returns)
# ---------------------------------------------------------------------
class WorkspaceStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    RULES_CHECKED = "rules_checked"
    AI_ANALYZED = "ai_analyzed"
    REPORT_READY = "report_ready"
    FAILED = "failed"


class WorkspaceResponse(BaseModel):
    workspace_id: str
    status: WorkspaceStatus
    original_filename: str
    spec: Optional[TestSpec] = None
    rule_engine: Optional[RuleEngineResult] = None
    ai_analysis: Optional[AIAnalysisResult] = None
    report_pdf_url: Optional[str] = None
    report_xlsx_url: Optional[str] = None
    error: Optional[str] = None
"""
Rule Engine stage.

Deterministic, non-AI checks over a parsed TestSpec. These are fast,
free, and reproducible — they catch structural/quality issues before
anything gets sent to the (paid, slower) AI analysis stage.
"""

from __future__ import annotations

from app.models.workspace import RuleEngineResult, RuleFinding, Severity, TestCase, TestSpec

VALID_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
BODY_EXPECTED_METHODS = {"POST", "PUT", "PATCH"}


def run_rule_engine(spec: TestSpec) -> RuleEngineResult:
    findings: list[RuleFinding] = []

    findings.extend(_check_duplicate_ids(spec))
    findings.extend(_check_duplicate_names(spec))

    for case in spec.test_cases:
        findings.extend(_check_case(case))

    error_count = sum(1 for f in findings if f.severity == Severity.ERROR)
    warning_count = sum(1 for f in findings if f.severity == Severity.WARNING)
    info_count = sum(1 for f in findings if f.severity == Severity.INFO)

    return RuleEngineResult(
        total_test_cases=len(spec.test_cases),
        findings=findings,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
    )


def _check_duplicate_ids(spec: TestSpec) -> list[RuleFinding]:
    seen: dict[str, int] = {}
    for case in spec.test_cases:
        seen[case.id] = seen.get(case.id, 0) + 1

    return [
        RuleFinding(
            test_case_id=case_id,
            rule="duplicate_id",
            severity=Severity.ERROR,
            message=f"Test case id '{case_id}' is used {count} times. IDs must be unique.",
        )
        for case_id, count in seen.items()
        if count > 1
    ]


def _check_duplicate_names(spec: TestSpec) -> list[RuleFinding]:
    seen: dict[str, int] = {}
    for case in spec.test_cases:
        seen[case.name] = seen.get(case.name, 0) + 1

    return [
        RuleFinding(
            rule="duplicate_name",
            severity=Severity.WARNING,
            message=f"Test case name '{name}' is used {count} times. Consider making names unique for clearer reports.",
        )
        for name, count in seen.items()
        if count > 1
    ]


def _check_case(case: TestCase) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if not case.method:
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="missing_method",
                severity=Severity.ERROR,
                message="No HTTP method specified.",
            )
        )
    elif case.method.upper() not in VALID_HTTP_METHODS:
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="invalid_method",
                severity=Severity.ERROR,
                message=f"'{case.method}' is not a recognized HTTP method.",
            )
        )

    if not case.endpoint:
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="missing_endpoint",
                severity=Severity.ERROR,
                message="No endpoint specified.",
            )
        )
    elif not case.endpoint.startswith("/"):
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="malformed_endpoint",
                severity=Severity.WARNING,
                message=f"Endpoint '{case.endpoint}' should start with '/'.",
            )
        )

    if (
        case.method
        and case.method.upper() in BODY_EXPECTED_METHODS
        and not case.request_body
    ):
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="missing_request_body",
                severity=Severity.WARNING,
                message=f"{case.method.upper()} request has no request_body defined.",
            )
        )

    if case.expected_status is None:
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="missing_expected_status",
                severity=Severity.ERROR,
                message="No expected_status defined — this test case can't assert success or failure.",
            )
        )
    elif not (100 <= case.expected_status <= 599):
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="invalid_expected_status",
                severity=Severity.ERROR,
                message=f"expected_status {case.expected_status} is not a valid HTTP status code.",
            )
        )

    if not case.expected_response:
        findings.append(
            RuleFinding(
                test_case_id=case.id,
                rule="missing_expected_response",
                severity=Severity.INFO,
                message="No expected_response defined — consider adding one to assert response shape.",
            )
        )

    return findings
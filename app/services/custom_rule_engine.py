"""
Custom Rule Engine stage.

Same job as `rule_engine.py`, but instead of a fixed set of built-in
checks, it evaluates a user-supplied `CustomRuleSet` against the parsed
TestSpec. This is what runs when someone chooses "use my own test
cases" instead of the default predefined checks.

Each `CustomRule` is applied to every test case in the spec. A rule
addresses a field by dot-notation (e.g. "headers.Authorization" or
"request_body.user_id") so it can reach into the dict-valued parts of
a TestCase, not just its top-level attributes.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.models.workspace import (
    CustomRule,
    CustomRuleSet,
    CustomRuleType,
    RuleEngineResult,
    RuleFinding,
    Severity,
    TestCase,
    TestSpec,
)

_MISSING = object()  # sentinel: field path did not resolve to anything


class CustomRuleParseError(Exception):
    """Raised when user-supplied custom rules text can't be parsed/validated."""


def parse_custom_rules(raw_text: str) -> CustomRuleSet:
    """Parse and validate user-supplied custom-rules JSON text."""
    if not raw_text.strip():
        raise CustomRuleParseError("Custom rules text is empty.")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CustomRuleParseError(f"Invalid JSON: {exc.msg} (line {exc.lineno}).") from exc

    # Allow either {"rules": [...]} or a bare top-level array of rules.
    if isinstance(data, list):
        data = {"rules": data}

    if not isinstance(data, dict):
        raise CustomRuleParseError(
            "Top-level custom rules JSON must be an object with a 'rules' array "
            "(or a bare array of rule objects)."
        )

    if not isinstance(data.get("rules"), list) or len(data["rules"]) == 0:
        raise CustomRuleParseError("'rules' must be a non-empty array of rule objects.")

    try:
        return CustomRuleSet.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
        )
        raise CustomRuleParseError(f"Custom rules validation failed: {problems}") from exc


def run_custom_rule_engine(spec: TestSpec, rule_set: CustomRuleSet) -> RuleEngineResult:
    findings: list[RuleFinding] = []

    for case in spec.test_cases:
        for rule in rule_set.rules:
            finding = _evaluate_rule(case, rule)
            if finding is not None:
                findings.append(finding)

    error_count = sum(1 for f in findings if f.severity == Severity.ERROR)
    warning_count = sum(1 for f in findings if f.severity == Severity.WARNING)
    info_count = sum(1 for f in findings if f.severity == Severity.INFO)

    return RuleEngineResult(
        total_test_cases=len(spec.test_cases),
        findings=findings,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        source="custom",
    )


def _evaluate_rule(case: TestCase, rule: CustomRule) -> RuleFinding | None:
    value = _resolve_field(case, rule.field)
    ok, detail = _check(rule, value)
    if ok:
        return None

    rule_name = rule.rule_id or f"{rule.field}:{rule.type.value}"
    message = rule.message or _default_message(rule, value, detail)

    return RuleFinding(
        test_case_id=case.id,
        rule=rule_name,
        severity=rule.severity,
        message=message,
    )


def _resolve_field(case: TestCase, field_path: str) -> Any:
    """Resolve a dot-notation field path against a TestCase.

    First segment is a top-level TestCase attribute; remaining segments
    (if any) index into that attribute's dict value. Returns the
    `_MISSING` sentinel if any part of the path doesn't resolve.
    """
    parts = field_path.split(".")
    top = getattr(case, parts[0], _MISSING)
    if top is _MISSING:
        return _MISSING

    current: Any = top
    for part in parts[1:]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def _check(rule: CustomRule, value: Any) -> tuple[bool, str]:
    rule_type = rule.type

    if rule_type == CustomRuleType.REQUIRED:
        return value is not _MISSING and value is not None, "field is missing"

    if rule_type == CustomRuleType.NOT_EMPTY:
        if value is _MISSING or value is None:
            return False, "field is missing"
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False, "field is empty"
        return True, ""

    # Everything below treats a missing/None field as a failed check,
    # since there's nothing meaningful to compare.
    if value is _MISSING or value is None:
        return False, "field is missing"

    if rule_type == CustomRuleType.EQUALS:
        return value == rule.value, f"expected {rule.value!r}, got {value!r}"

    if rule_type == CustomRuleType.NOT_EQUALS:
        return value != rule.value, f"value should not equal {rule.value!r}"

    if rule_type == CustomRuleType.IN:
        allowed = rule.values or []
        return value in allowed, f"expected one of {allowed!r}, got {value!r}"

    if rule_type == CustomRuleType.NOT_IN:
        disallowed = rule.values or []
        return value not in disallowed, f"value should not be one of {disallowed!r}"

    if rule_type == CustomRuleType.STARTS_WITH:
        return isinstance(value, str) and value.startswith(str(rule.value)), (
            f"expected to start with {rule.value!r}"
        )

    if rule_type == CustomRuleType.ENDS_WITH:
        return isinstance(value, str) and value.endswith(str(rule.value)), (
            f"expected to end with {rule.value!r}"
        )

    if rule_type == CustomRuleType.CONTAINS:
        try:
            return rule.value in value, f"expected to contain {rule.value!r}"
        except TypeError:
            return False, "value is not a container that supports 'contains'"

    if rule_type == CustomRuleType.REGEX:
        pattern = str(rule.value or "")
        return bool(re.search(pattern, str(value))), f"expected to match pattern {pattern!r}"

    if rule_type == CustomRuleType.MIN:
        try:
            return float(value) >= float(rule.min), f"expected >= {rule.min}, got {value!r}"
        except (TypeError, ValueError):
            return False, "value is not numeric"

    if rule_type == CustomRuleType.MAX:
        try:
            return float(value) <= float(rule.max), f"expected <= {rule.max}, got {value!r}"
        except (TypeError, ValueError):
            return False, "value is not numeric"

    if rule_type == CustomRuleType.RANGE:
        try:
            num = float(value)
            lo = float(rule.min) if rule.min is not None else float("-inf")
            hi = float(rule.max) if rule.max is not None else float("inf")
            return lo <= num <= hi, f"expected between {rule.min} and {rule.max}, got {value!r}"
        except (TypeError, ValueError):
            return False, "value is not numeric"

    return True, ""  # unknown rule type: don't fail the pipeline over it


def _default_message(rule: CustomRule, value: Any, detail: str) -> str:
    shown = "<missing>" if value is _MISSING else value
    return f"Custom rule on '{rule.field}' ({rule.type.value}) failed: {detail} (actual: {shown!r})"

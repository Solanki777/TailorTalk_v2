"""
Parse stage.

Takes the raw uploaded file (JSON, matching the TestPilot test-spec
shape: {test_suite, version, base_url, test_cases: [...]}) and turns
it into a validated `TestSpec`. Anything that doesn't match raises a
`SpecParseError` with a human-readable reason, which the pipeline
service turns into a clean 400/422 response instead of a stack trace.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.models.workspace import TestSpec


class SpecParseError(Exception):
    """Raised when an uploaded file cannot be parsed into a TestSpec."""


def parse_spec_file(file_path: Path) -> TestSpec:
    """Read a JSON file from disk and validate it into a TestSpec."""
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SpecParseError("File is not valid UTF-8 text.") from exc

    return parse_spec_text(raw_text)


def parse_spec_text(raw_text: str) -> TestSpec:
    """Parse and validate a JSON string into a TestSpec."""
    if not raw_text.strip():
        raise SpecParseError("File is empty.")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SpecParseError(f"Invalid JSON: {exc.msg} (line {exc.lineno}).") from exc

    if not isinstance(data, dict):
        raise SpecParseError(
            "Top-level JSON must be an object with a 'test_cases' field."
        )

    if "test_cases" not in data:
        raise SpecParseError("Missing required field: 'test_cases'.")

    if not isinstance(data["test_cases"], list) or len(data["test_cases"]) == 0:
        raise SpecParseError("'test_cases' must be a non-empty array.")

    try:
        return TestSpec.model_validate(data)
    except ValidationError as exc:
        # Collapse pydantic's error list into one readable line per issue.
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        )
        raise SpecParseError(f"Spec validation failed: {problems}") from exc
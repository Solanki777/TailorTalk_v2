"""
AI Analysis stage.

Sends the parsed spec + rule engine findings to Google Gemini and asks
for a structured critique: coverage gaps and qualitative findings a
deterministic rule engine can't catch (e.g. "no test for expired
token", "status codes suggest missing negative-path coverage").

Designed to never take the pipeline down: if there's no API key, or
the call fails, or Gemini returns something that doesn't parse as
JSON, we return an `AIAnalysisResult` with `skipped_reason` set
instead of raising.
"""

from __future__ import annotations

import json
import logging

from app.config import settings
from app.models.workspace import AIAnalysisResult, AIFinding, RuleEngineResult, Severity, TestSpec

logger = logging.getLogger("testpilot.ai")

_SYSTEM_INSTRUCTION = (
    "You are a senior QA engineer reviewing an API test suite. You will be "
    "given the test suite (as JSON) and the output of a deterministic rule "
    "engine that already checked for structural problems. Do NOT repeat "
    "issues the rule engine already found. Instead, focus on judgment calls "
    "a human reviewer would make: missing negative-path tests, missing edge "
    "cases (empty input, boundary values, auth/expired tokens, rate limits), "
    "unclear or overlapping test intent, and overall coverage gaps.\n\n"
    "Respond with ONLY a JSON object matching this exact shape, no markdown "
    "fences, no extra commentary:\n"
    "{\n"
    '  "summary": "2-3 sentence overall assessment",\n'
    '  "coverage_gaps": ["short phrase", "short phrase"],\n'
    '  "findings": [\n'
    '    {"category": "short label", "severity": "error|warning|info", "message": "1-2 sentences"}\n'
    "  ]\n"
    "}"
)


def analyze_with_gemini(spec: TestSpec, rule_result: RuleEngineResult) -> AIAnalysisResult:
    if not settings.GEMINI_API_KEY:
        return AIAnalysisResult(
            summary="AI analysis was skipped because no Gemini API key is configured.",
            skipped_reason="missing_api_key",
        )

    try:
        # Imported lazily so the app can still start/run without the
        # google-genai package fully wired if a key is never set.
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = (
            f"Test suite JSON:\n{spec.model_dump_json(indent=2)}\n\n"
            f"Rule engine findings JSON:\n{rule_result.model_dump_json(indent=2)}"
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[_SYSTEM_INSTRUCTION, prompt],
        )

        raw_text = (response.text or "").strip()
        raw_text = _strip_markdown_fences(raw_text)
        data = json.loads(raw_text)

        findings = [
            AIFinding(
                category=item.get("category", "general"),
                severity=Severity(item.get("severity", "info")),
                message=item.get("message", ""),
            )
            for item in data.get("findings", [])
        ]

        return AIAnalysisResult(
            summary=data.get("summary", ""),
            coverage_gaps=data.get("coverage_gaps", []),
            findings=findings,
            model_used=settings.GEMINI_MODEL,
        )

    except Exception as exc:  # noqa: BLE001 - deliberately broad, pipeline must not crash
        logger.exception("Gemini AI analysis failed")
        return AIAnalysisResult(
            summary="AI analysis could not be completed due to an error.",
            skipped_reason=_summarize_error(exc),
        )


def _summarize_error(exc: Exception) -> str:
    """Turn a raw Gemini/SDK exception into one short, human-readable line.

    The google-genai SDK raises errors whose str() is a giant Python dict
    dump (great for logs, unreadable in a report). This picks out just the
    HTTP status + message when available and falls back to a trimmed
    generic message otherwise.
    """
    text = str(exc)

    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        if "limit: 0" in text or "'limit': 0" in text:
            return (
                "Gemini API quota is locked at 0 for this key's project. "
                "This usually means the Google Cloud project needs a billing "
                "account linked to unlock the free usage tier — see "
                "https://ai.google.dev/gemini-api/docs/rate-limits."
            )
        return (
            "Gemini API rate limit reached for this key. Wait a bit and "
            "retry, or check your usage at https://ai.dev/rate-limit."
        )

    if "API_KEY_INVALID" in text or "401" in text or "PERMISSION_DENIED" in text:
        return "Gemini API key was rejected (invalid or missing permissions)."

    # Generic fallback: first line only, capped so it can't blow up a report.
    first_line = text.strip().splitlines()[0] if text.strip() else type(exc).__name__
    return first_line[:200]


def _strip_markdown_fences(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json ... ``` even when told not to."""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()
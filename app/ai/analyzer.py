"""
AI Analysis stage.

Sends the parsed spec + rule engine findings to an LLM and asks for a
structured critique: coverage gaps and qualitative findings a
deterministic rule engine can't catch (e.g. "no test for expired
token", "status codes suggest missing negative-path coverage").

Two providers are supported:

  * Groq (default/preferred) - free tier, no billing card required,
    very fast inference. Get a free key at https://console.groq.com/keys
  * Gemini (fallback) - used only if no Groq key is set but a Gemini
    key is. Google's free tier commonly returns a locked-at-0 quota
    until a billing account is linked, which is the "quota exceeded"
    error this project used to hit.

Designed to never take the pipeline down: if there's no API key, or
the call fails, or the model returns something that doesn't parse as
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
    """
    Entry point kept under its historical name for backward compatibility
    with the rest of the pipeline (`from app.ai.analyzer import
    analyze_with_gemini`). Internally it now picks whichever provider is
    configured, preferring Groq.
    """
    prompt = (
        f"Test suite JSON:\n{spec.model_dump_json(indent=2)}\n\n"
        f"Rule engine findings JSON:\n{rule_result.model_dump_json(indent=2)}"
    )

    if settings.GROQ_API_KEY:
        return _analyze_with_groq(prompt)

    if settings.GEMINI_API_KEY:
        return _analyze_with_gemini_provider(prompt)

    return AIAnalysisResult(
        summary=(
            "AI analysis was skipped because no AI provider API key is "
            "configured. Set GROQ_API_KEY (recommended, free, no card "
            "required - https://console.groq.com/keys) or GEMINI_API_KEY."
        ),
        skipped_reason="missing_api_key",
    )


def _analyze_with_groq(prompt: str) -> AIAnalysisResult:
    try:
        import httpx

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        raw_text = payload["choices"][0]["message"]["content"] or ""
        raw_text = _strip_markdown_fences(raw_text.strip())
        data = json.loads(raw_text)

        return AIAnalysisResult(
            summary=data.get("summary", ""),
            coverage_gaps=data.get("coverage_gaps", []),
            findings=_parse_findings(data),
            model_used=settings.GROQ_MODEL,
        )

    except Exception as exc:  # noqa: BLE001 - deliberately broad, pipeline must not crash
        logger.exception("Groq AI analysis failed")
        return AIAnalysisResult(
            summary="AI analysis could not be completed due to an error.",
            skipped_reason=_summarize_groq_error(exc),
        )


def _analyze_with_gemini_provider(prompt: str) -> AIAnalysisResult:
    try:
        # Imported lazily so the app can still start/run without the
        # google-genai package fully wired if a key is never set.
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[_SYSTEM_INSTRUCTION, prompt],
        )

        raw_text = (response.text or "").strip()
        raw_text = _strip_markdown_fences(raw_text)
        data = json.loads(raw_text)

        return AIAnalysisResult(
            summary=data.get("summary", ""),
            coverage_gaps=data.get("coverage_gaps", []),
            findings=_parse_findings(data),
            model_used=settings.GEMINI_MODEL,
        )

    except Exception as exc:  # noqa: BLE001 - deliberately broad, pipeline must not crash
        logger.exception("Gemini AI analysis failed")
        return AIAnalysisResult(
            summary="AI analysis could not be completed due to an error.",
            skipped_reason=_summarize_gemini_error(exc),
        )


def _parse_findings(data: dict) -> list[AIFinding]:
    return [
        AIFinding(
            category=item.get("category", "general"),
            severity=Severity(item.get("severity", "info")),
            message=item.get("message", ""),
        )
        for item in data.get("findings", [])
    ]


def _summarize_groq_error(exc: Exception) -> str:
    """Turn a raw Groq/httpx exception into one short, human-readable line."""
    text = str(exc)

    if "429" in text or "rate_limit" in text.lower():
        return (
            "Groq API rate limit reached for this key. Groq's free tier "
            "resets quickly - wait a bit and retry, or check your usage at "
            "https://console.groq.com/settings/limits."
        )

    if "401" in text or "invalid_api_key" in text.lower():
        return "Groq API key was rejected (invalid or missing). Get a free key at https://console.groq.com/keys."

    if "decommissioned" in text.lower() or "model_not_found" in text.lower():
        return (
            f"Groq model '{settings.GROQ_MODEL}' is unavailable. Check "
            "https://console.groq.com/docs/models for current model names "
            "and update GROQ_MODEL."
        )

    first_line = text.strip().splitlines()[0] if text.strip() else type(exc).__name__
    return first_line[:200]


def _summarize_gemini_error(exc: Exception) -> str:
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
                "https://ai.google.dev/gemini-api/docs/rate-limits. "
                "Consider switching to GROQ_API_KEY instead, which is free "
                "with no billing account required."
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
    """Some models wrap JSON in ```json ... ``` even when told not to."""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()

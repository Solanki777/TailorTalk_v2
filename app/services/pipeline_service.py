"""
Pipeline orchestrator.

Runs a freshly-uploaded spec file through every stage and persists
each stage's output into its workspace folder:

    storage/<workspace_id>/
        spec.json           the raw uploaded file, as-is
        parsed.json          TestSpec, validated
        rule_engine.json     RuleEngineResult
        ai_analysis.json     AIAnalysisResult
        report.pdf
        report.xlsx

Every stage after Parse is best-effort: if AI analysis fails, the
pipeline still finishes and produces a report noting the AI stage was
skipped, rather than losing the work already done.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.ai.analyzer import analyze_with_gemini
from app.config import settings
from app.models.workspace import (
    AIAnalysisResult,
    RuleEngineResult,
    TestSpec,
    WorkspaceResponse,
    WorkspaceStatus,
)
from app.parser.spec_parser import SpecParseError, parse_spec_text
from app.services.custom_rule_engine import CustomRuleParseError, parse_custom_rules, run_custom_rule_engine
from app.services.report_service import generate_pdf_report, generate_xlsx_report
from app.services.rule_engine import run_rule_engine

logger = logging.getLogger("testpilot.pipeline")

MAX_READ_BYTES = 1024 * 1024  # 1MB chunks, matches existing upload pattern


async def run_pipeline(upload_file: UploadFile, custom_rules_text: str | None = None) -> WorkspaceResponse:
    """Run the full pipeline for a freshly uploaded file and return the result.

    If `custom_rules_text` is provided (non-empty), it's parsed as a
    user-defined `CustomRuleSet` and used *instead of* the built-in rule
    engine for the Rule Engine stage. If it's absent/blank, the default
    predefined checks in `rule_engine.py` are used, same as before.
    """
    workspace_id = uuid.uuid4().hex
    workspace_dir = settings.ensure_workspace(workspace_id)
    original_filename = Path(upload_file.filename or "spec.json").name

    # --- Read the upload into memory (spec files are small JSON docs) ---
    raw_bytes = bytearray()
    while chunk := await upload_file.read(MAX_READ_BYTES):
        raw_bytes.extend(chunk)
        if len(raw_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            return WorkspaceResponse(
                workspace_id=workspace_id,
                status=WorkspaceStatus.FAILED,
                original_filename=original_filename,
                error=f"File exceeds the {settings.MAX_FILE_SIZE_MB}MB limit.",
            )

    if len(raw_bytes) == 0:
        return WorkspaceResponse(
            workspace_id=workspace_id,
            status=WorkspaceStatus.FAILED,
            original_filename=original_filename,
            error="File cannot be empty.",
        )

    raw_text = raw_bytes.decode("utf-8", errors="replace")
    (workspace_dir / "spec.json").write_text(raw_text, encoding="utf-8")

    # --- Stage: Parse ----------------------------------------------------
    try:
        spec: TestSpec = parse_spec_text(raw_text)
    except SpecParseError as exc:
        logger.info("Parse failed for workspace %s: %s", workspace_id, exc)
        return WorkspaceResponse(
            workspace_id=workspace_id,
            status=WorkspaceStatus.FAILED,
            original_filename=original_filename,
            error=str(exc),
        )

    (workspace_dir / "parsed.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    # --- Stage: Rule Engine (custom, if supplied, else default predefined) --
    if custom_rules_text and custom_rules_text.strip():
        try:
            rule_set = parse_custom_rules(custom_rules_text)
        except CustomRuleParseError as exc:
            logger.info("Custom rules failed to parse for workspace %s: %s", workspace_id, exc)
            return WorkspaceResponse(
                workspace_id=workspace_id,
                status=WorkspaceStatus.FAILED,
                original_filename=original_filename,
                spec=spec,
                error=f"Custom rules error: {exc}",
            )
        rule_result: RuleEngineResult = run_custom_rule_engine(spec, rule_set)
    else:
        rule_result = run_rule_engine(spec)

    (workspace_dir / "rule_engine.json").write_text(
        rule_result.model_dump_json(indent=2), encoding="utf-8"
    )

    # --- Stage: AI Analysis (best-effort, never fatal) ----------------------
    ai_result: AIAnalysisResult = analyze_with_gemini(spec, rule_result)
    (workspace_dir / "ai_analysis.json").write_text(
        ai_result.model_dump_json(indent=2), encoding="utf-8"
    )

    # --- Stage: Report -------------------------------------------------------
    pdf_path = workspace_dir / "report.pdf"
    xlsx_path = workspace_dir / "report.xlsx"
    try:
        generate_pdf_report(pdf_path, workspace_id, spec, rule_result, ai_result)
        generate_xlsx_report(xlsx_path, workspace_id, spec, rule_result, ai_result)
        status = WorkspaceStatus.REPORT_READY
    except Exception:  # noqa: BLE001 - report generation must not crash the whole pipeline
        logger.exception("Report generation failed for workspace %s", workspace_id)
        status = WorkspaceStatus.AI_ANALYZED

    return WorkspaceResponse(
        workspace_id=workspace_id,
        status=status,
        original_filename=original_filename,
        spec=spec,
        rule_engine=rule_result,
        ai_analysis=ai_result,
        report_pdf_url=f"{settings.API_PREFIX}/workspaces/{workspace_id}/report.pdf"
        if pdf_path.exists()
        else None,
        report_xlsx_url=f"{settings.API_PREFIX}/workspaces/{workspace_id}/report.xlsx"
        if xlsx_path.exists()
        else None,
    )


def load_workspace(workspace_id: str) -> WorkspaceResponse | None:
    """Reload a previously-run workspace's results from disk, if it exists."""
    workspace_dir = settings.workspace_path(workspace_id)
    spec_file = workspace_dir / "spec.json"
    if not workspace_dir.exists() or not spec_file.exists():
        return None

    parsed_file = workspace_dir / "parsed.json"
    if not parsed_file.exists():
        return WorkspaceResponse(
            workspace_id=workspace_id,
            status=WorkspaceStatus.UPLOADED,
            original_filename="spec.json",
        )

    spec = TestSpec.model_validate_json(parsed_file.read_text(encoding="utf-8"))

    rule_result = None
    rule_file = workspace_dir / "rule_engine.json"
    if rule_file.exists():
        rule_result = RuleEngineResult.model_validate_json(rule_file.read_text(encoding="utf-8"))

    ai_result = None
    ai_file = workspace_dir / "ai_analysis.json"
    if ai_file.exists():
        ai_result = AIAnalysisResult.model_validate_json(ai_file.read_text(encoding="utf-8"))

    pdf_exists = (workspace_dir / "report.pdf").exists()
    xlsx_exists = (workspace_dir / "report.xlsx").exists()

    if pdf_exists:
        status = WorkspaceStatus.REPORT_READY
    elif ai_result:
        status = WorkspaceStatus.AI_ANALYZED
    elif rule_result:
        status = WorkspaceStatus.RULES_CHECKED
    else:
        status = WorkspaceStatus.PARSED

    return WorkspaceResponse(
        workspace_id=workspace_id,
        status=status,
        original_filename="spec.json",
        spec=spec,
        rule_engine=rule_result,
        ai_analysis=ai_result,
        report_pdf_url=f"{settings.API_PREFIX}/workspaces/{workspace_id}/report.pdf" if pdf_exists else None,
        report_xlsx_url=f"{settings.API_PREFIX}/workspaces/{workspace_id}/report.xlsx" if xlsx_exists else None,
    )
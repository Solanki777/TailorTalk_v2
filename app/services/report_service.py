"""
Report stage.

Turns the results of the earlier stages (parsed spec, rule engine
findings, AI analysis) into two downloadable artifacts per workspace:

    report.pdf    a readable summary for humans
    report.xlsx   a structured spreadsheet for further filtering/sorting
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.workspace import AIAnalysisResult, RuleEngineResult, TestSpec

_SEVERITY_COLORS = {
    "error": colors.HexColor("#DC2626"),
    "warning": colors.HexColor("#D97706"),
    "info": colors.HexColor("#2563EB"),
}


def generate_pdf_report(
    out_path: Path,
    workspace_id: str,
    spec: TestSpec,
    rule_result: RuleEngineResult,
    ai_result: AIAnalysisResult,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=LETTER, title="TestPilot AI Report")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TPTitle", parent=styles["Title"], textColor=colors.HexColor("#312E81")
    )
    h2_style = ParagraphStyle(
        "TPHeading2", parent=styles["Heading2"], textColor=colors.HexColor("#4338CA")
    )

    story = []
    story.append(Paragraph("TestPilot AI — Analysis Report", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Workspace: {workspace_id}", styles["Normal"]))
    story.append(Paragraph(f"Test Suite: {spec.test_suite} (v{spec.version})", styles["Normal"]))
    if spec.base_url:
        story.append(Paragraph(f"Base URL: {spec.base_url}", styles["Normal"]))
    story.append(Spacer(1, 16))

    # --- Summary -------------------------------------------------------
    story.append(Paragraph("Summary", h2_style))
    summary_data = [
        ["Total test cases", str(len(spec.test_cases))],
        ["Rule engine errors", str(rule_result.error_count)],
        ["Rule engine warnings", str(rule_result.warning_count)],
        ["Rule engine info notes", str(rule_result.info_count)],
    ]
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D2FE")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # --- Rule engine findings -------------------------------------------
    story.append(Paragraph("Rule Engine Findings", h2_style))
    if rule_result.findings:
        rows = [["Test Case", "Rule", "Severity", "Message"]]
        for f in rule_result.findings:
            rows.append(
                [f.test_case_id or "-", f.rule, f.severity.value.upper(), f.message]
            )
        findings_table = Table(
            rows, colWidths=[0.9 * inch, 1.3 * inch, 0.7 * inch, 3.1 * inch], repeatRows=1
        )
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(findings_table)
    else:
        story.append(Paragraph("No issues found by the rule engine.", styles["Normal"]))
    story.append(Spacer(1, 16))

    # --- AI analysis -----------------------------------------------------
    story.append(Paragraph("AI Analysis", h2_style))
    if ai_result.skipped_reason:
        story.append(
            Paragraph(f"<i>AI analysis skipped: {ai_result.skipped_reason}</i>", styles["Normal"])
        )
    else:
        story.append(Paragraph(ai_result.summary, styles["Normal"]))
        story.append(Spacer(1, 8))
        if ai_result.coverage_gaps:
            story.append(Paragraph("Coverage gaps:", styles["Heading4"]))
            for gap in ai_result.coverage_gaps:
                story.append(Paragraph(f"• {gap}", styles["Normal"]))
            story.append(Spacer(1, 8))
        if ai_result.findings:
            rows = [["Category", "Severity", "Message"]]
            for f in ai_result.findings:
                rows.append([f.category, f.severity.value.upper(), f.message])
            ai_table = Table(rows, colWidths=[1.3 * inch, 0.9 * inch, 3.8 * inch], repeatRows=1)
            ai_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(ai_table)

    doc.build(story)


def generate_xlsx_report(
    out_path: Path,
    workspace_id: str,
    spec: TestSpec,
    rule_result: RuleEngineResult,
    ai_result: AIAnalysisResult,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    header_fill = PatternFill(start_color="4338CA", end_color="4338CA", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    wrap = Alignment(wrap_text=True, vertical="top")

    # --- Sheet 1: Test Cases ---------------------------------------------
    ws1 = wb.active
    ws1.title = "Test Cases"
    headers = ["ID", "Name", "Method", "Endpoint", "Expected Status", "Has Request Body", "Has Expected Response"]
    ws1.append(headers)
    for cell in ws1[1]:
        cell.fill = header_fill
        cell.font = header_font
    for case in spec.test_cases:
        ws1.append(
            [
                case.id,
                case.name,
                case.method or "",
                case.endpoint or "",
                case.expected_status if case.expected_status is not None else "",
                "Yes" if case.request_body else "No",
                "Yes" if case.expected_response else "No",
            ]
        )
    _autosize(ws1, headers)

    # --- Sheet 2: Rule Engine Findings ------------------------------------
    ws2 = wb.create_sheet("Rule Engine Findings")
    headers2 = ["Test Case", "Rule", "Severity", "Message"]
    ws2.append(headers2)
    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = header_font
    for f in rule_result.findings:
        ws2.append([f.test_case_id or "-", f.rule, f.severity.value.upper(), f.message])
        ws2.cell(ws2.max_row, 4).alignment = wrap
    _autosize(ws2, headers2)

    # --- Sheet 3: AI Analysis ---------------------------------------------
    ws3 = wb.create_sheet("AI Analysis")
    ws3.append(["Summary"])
    ws3["A1"].font = Font(bold=True)
    ws3.append([ai_result.skipped_reason and f"Skipped: {ai_result.skipped_reason}" or ai_result.summary])
    ws3.append([])
    if ai_result.coverage_gaps:
        ws3.append(["Coverage Gaps"])
        ws3.cell(ws3.max_row, 1).font = Font(bold=True)
        for gap in ai_result.coverage_gaps:
            ws3.append([gap])
        ws3.append([])
    if ai_result.findings:
        headers3 = ["Category", "Severity", "Message"]
        ws3.append(headers3)
        for cell in ws3[ws3.max_row]:
            cell.fill = header_fill
            cell.font = header_font
        for f in ai_result.findings:
            ws3.append([f.category, f.severity.value.upper(), f.message])
            ws3.cell(ws3.max_row, 3).alignment = wrap
    ws3.column_dimensions["A"].width = 90

    wb.save(out_path)


def _autosize(ws, headers: list[str], min_width: int = 12, max_width: int = 50) -> None:
    for i, header in enumerate(headers, start=1):
        col_letter = get_column_letter(i)
        longest = max(
            [len(header)]
            + [len(str(cell.value)) for cell in ws[col_letter] if cell.value is not None]
        )
        ws.column_dimensions[col_letter].width = min(max(longest + 2, min_width), max_width)
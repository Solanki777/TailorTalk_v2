from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.config import settings
from app.models.workspace import WorkspaceResponse, WorkspaceStatus
from app.services.pipeline_service import load_workspace, run_pipeline

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    file: UploadFile = File(...),
    custom_rules: str | None = Form(None),
    rules_file: UploadFile | None = File(None),
):
    """
    Upload a test spec and run it through the full pipeline:
    Parse -> Rule Engine -> AI Analysis -> Report.

    The Rule Engine stage uses the built-in predefined checks by
    default. To use your own test cases/rules instead, send either:
      - `rules_file`: a JSON file of custom rules, or
      - `custom_rules`: the same JSON pasted directly as form text
    If both are sent, `rules_file` wins. If neither is sent, the
    default predefined rule engine runs, same as before.

    Always returns 200 with a WorkspaceResponse — if a stage fails,
    `status` will be "failed" and `error` will explain why, rather
    than a generic 500.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a non-empty name.",
        )

    custom_rules_text: str | None = None
    if rules_file is not None and rules_file.filename:
        rules_bytes = await rules_file.read()
        custom_rules_text = rules_bytes.decode("utf-8", errors="replace")
    elif custom_rules and custom_rules.strip():
        custom_rules_text = custom_rules

    result = await run_pipeline(file, custom_rules_text)
    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str):
    """Fetch the current results for a previously-created workspace."""
    result = load_workspace(workspace_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return result


@router.get("/{workspace_id}/report.pdf")
async def download_pdf_report(workspace_id: str):
    path = settings.workspace_path(workspace_id) / "report.pdf"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return FileResponse(path, media_type="application/pdf", filename=f"testpilot-report-{workspace_id[:8]}.pdf")


@router.get("/{workspace_id}/report.xlsx")
async def download_xlsx_report(workspace_id: str):
    path = settings.workspace_path(workspace_id) / "report.xlsx"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"testpilot-report-{workspace_id[:8]}.xlsx",
    )
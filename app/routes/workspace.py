from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.config import settings
from app.models.workspace import WorkspaceResponse, WorkspaceStatus
from app.services.pipeline_service import load_workspace, run_pipeline

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(file: UploadFile = File(...)):
    """
    Upload a test spec and run it through the full pipeline:
    Parse -> Rule Engine -> AI Analysis -> Report.

    Always returns 200 with a WorkspaceResponse — if a stage fails,
    `status` will be "failed" and `error` will explain why, rather
    than a generic 500.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a non-empty name.",
        )

    result = await run_pipeline(file)
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
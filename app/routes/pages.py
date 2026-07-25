from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import settings

router = APIRouter(tags=["pages"])

# Setup template routing relative to this file
templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "TestPilot AI - Home"}
    )


@router.get("/features")
async def features(request: Request):
    """Render the product pipeline / capabilities page."""
    return templates.TemplateResponse(
        request=request,
        name="features.html",
        context={"title": "TestPilot AI - Features"}
    )


@router.get("/settings")
async def settings_page(request: Request):
    """
    Render a read-only view of the active configuration.

    There's no database or user accounts in this project, so "settings"
    reflects the real values the server is currently running with
    (from environment variables / .env) rather than editable, persisted
    preferences.
    """
    masked_key = (
        f"{settings.GEMINI_API_KEY[:4]}{'•' * 10}"
        if settings.GEMINI_API_KEY
        else "Not configured"
    )

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "title": "TestPilot AI - Settings",
            "environment": settings.ENVIRONMENT.value,
            "debug": settings.DEBUG,
            "app_version": settings.APP_VERSION,
            "api_prefix": settings.API_PREFIX,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": sorted(settings.ALLOWED_EXTENSIONS),
            "gemini_model": settings.GEMINI_MODEL,
            "gemini_key_display": masked_key,
            "storage_path": str(settings.storage_path),
            "workspace_retention_days": settings.WORKSPACE_RETENTION_DAYS,
        }
    )
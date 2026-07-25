"""
Application entry point for TestPilot AI.

Responsible for:
- Building the FastAPI app instance and its metadata
- Wiring up middleware (CORS)
- Mounting static files and Jinja2 templates
- Registering versioned API routers
- Running startup/shutdown logic via a lifespan context manager
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import pages, upload

logger = logging.getLogger("testpilot")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage startup and shutdown events.

    Replaces the deprecated `@app.on_event("startup")` pattern. Anything
    that needs to run once before the app starts serving requests (or
    once as it shuts down) belongs here.
    """
    # --- Startup -----------------------------------------------------
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Create every directory the app relies on (storage, reports, logs,
    # legacy uploads folder) so services never hit a "missing dir" error.
    settings.ensure_directories()

    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT.value,
    )
    logger.info("Storage root: %s", settings.storage_path)

    yield  # ---- app is now serving requests -------------------------

    # --- Shutdown ------------------------------------------------------
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """
    Application factory.

    Building the app in a function (rather than at import time only)
    keeps things testable — a test suite can call `create_app()` to get
    a fresh instance if ever needed — while `app` below remains the
    single instance uvicorn actually serves.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    _configure_middleware(app)
    _mount_static_files(app)
    _register_routers(app)
    _register_health_check(app)

    return app


def _configure_middleware(app: FastAPI) -> None:
    """Attach CORS middleware. Kept permissive for hackathon use."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _mount_static_files(app: FastAPI) -> None:
    """Mount the /static directory used for CSS, JS, and images."""
    static_dir: Path = Path(__file__).resolve().parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _register_routers(app: FastAPI) -> None:
    """
    Register all routers.

    Page routes (server-rendered HTML) are mounted at the root, while
    API routes are versioned under `settings.API_PREFIX` (/api/v1) so
    future breaking changes can live alongside v1 as /api/v2.
    """
    app.include_router(pages.router)
    app.include_router(upload.router, prefix=settings.API_PREFIX)


def _register_health_check(app: FastAPI) -> None:
    """Expose GET /health for uptime checks and smoke tests."""

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Report basic service liveness and build info."""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
        }


# Single app instance served by uvicorn (e.g. `uvicorn app.main:app --reload`)
app = create_app()
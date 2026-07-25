"""
Application configuration for TestPilot AI.

Centralizes all runtime settings using Pydantic Settings v2. Values are
loaded from environment variables / a local `.env` file and fall back to
sensible defaults so the app runs out of the box in a hackathon setting.

Storage model
-------------
Instead of a single flat "uploads" folder, storage is organized as
per-run *workspaces*:

    storage/
        <workspace_id>/
            spec.json
            parsed.json
            rule_engine.json
            ai_analysis.json
            report.pdf
            report.xlsx

Each workspace is an isolated folder (typically named after a UUID) that
holds every artifact produced for a single analysis run. This keeps the
pipeline (parse -> rule engine -> AI analysis -> report) traceable and
makes cleanup / inspection trivial.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root, resolved once. app/config.py -> app/ -> <project root>
BASE_DIR: Path = Path(__file__).resolve().parent.parent


class Environment(str, Enum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Central application settings.

    All values can be overridden via environment variables or a `.env`
    file in the project root (e.g. GEMINI_API_KEY=xxx).
    """

    # ------------------------------------------------------------------
    # App metadata
    # ------------------------------------------------------------------
    APP_NAME: str = "TestPilot AI"
    APP_DESCRIPTION: str = (
        "AI-powered test analysis platform with a Tailwind CSS "
        "and glassmorphism interface."
    )
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------
    # Environment / server
    # ------------------------------------------------------------------
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # ------------------------------------------------------------------
    # Security & external API keys
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ------------------------------------------------------------------
    # CORS (kept permissive for hackathon use; tighten for real prod)
    # ------------------------------------------------------------------
    CORS_ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # ------------------------------------------------------------------
    # Storage / workspace configuration
    # ------------------------------------------------------------------
    STORAGE_DIR: str = "storage"
    REPORTS_SUBDIR: str = "reports"
    LOGS_DIR: str = "logs"

    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set[str] = Field(
        default_factory=lambda: {".json", ".yaml", ".yml", ".csv", ".xlsx", ".xml"}
    )

    # ------------------------------------------------------------------
    # Future-ready settings (safe defaults, not wired up yet)
    # ------------------------------------------------------------------
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    REQUEST_TIMEOUT_SECONDS: int = 60
    WORKSPACE_RETENTION_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Derived filesystem paths
    # ------------------------------------------------------------------
    @computed_field  # type: ignore[misc]
    @property
    def storage_path(self) -> Path:
        """Root directory that holds every workspace."""
        return self._resolve(self.STORAGE_DIR)

    @computed_field  # type: ignore[misc]
    @property
    def reports_path(self) -> Path:
        """Shared/global reports directory (for anything not tied to a workspace)."""
        return self.storage_path / self.REPORTS_SUBDIR

    @computed_field  # type: ignore[misc]
    @property
    def logs_path(self) -> Path:
        """Directory used for application log files."""
        return self._resolve(self.LOGS_DIR)

    @property
    def upload_path(self) -> Path:
        """
        Backward-compatible alias for legacy code (e.g. StorageService,
        FileValidator) that still expects a single "uploads" directory.

        New code should prefer `workspace_path(workspace_id)` instead.
        """
        return self.storage_path / "uploads"

    def _resolve(self, raw_path: str) -> Path:
        """Resolve a configured path relative to the project root, if needed."""
        path = Path(raw_path)
        return path if path.is_absolute() else BASE_DIR / path

    # ------------------------------------------------------------------
    # Workspace helpers
    # ------------------------------------------------------------------
    def workspace_path(self, workspace_id: str) -> Path:
        """Return the folder for a specific workspace (does not create it)."""
        return self.storage_path / workspace_id

    def ensure_workspace(self, workspace_id: str) -> Path:
        """Create (if needed) and return the folder for a specific workspace."""
        path = self.workspace_path(workspace_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_directories(self) -> None:
        """
        Create all top-level directories the app depends on.

        Called once at startup (see `main.py` lifespan) so routes/services
        never need to worry about missing folders.
        """
        for path in (self.storage_path, self.reports_path, self.logs_path, self.upload_path):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Convenience flag for environment-specific behavior."""
        return self.ENVIRONMENT is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using a cached factory (instead of only a module-level singleton)
    makes it easy to override settings in tests via
    `get_settings.cache_clear()` + dependency overrides.
    """
    return Settings()


# Module-level singleton kept for backward compatibility with existing
# imports (`from app.config import settings`) used throughout the app.
settings = get_settings()
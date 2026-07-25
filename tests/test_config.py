"""Tests for app.config.Settings — paths, workspace helpers, and env parsing."""

from pathlib import Path

from app.config import Environment, Settings


def test_default_environment_is_development():
    settings = Settings(_env_file=None)
    assert settings.ENVIRONMENT is Environment.DEVELOPMENT
    assert settings.is_production is False


def test_storage_paths_are_resolved_under_project_root():
    settings = Settings(_env_file=None)
    assert settings.storage_path.is_absolute()
    assert settings.reports_path == settings.storage_path / settings.REPORTS_SUBDIR
    assert settings.upload_path == settings.storage_path / "uploads"


def test_absolute_storage_dir_is_used_as_is(tmp_path):
    settings = Settings(_env_file=None, STORAGE_DIR=str(tmp_path))
    assert settings.storage_path == tmp_path


def test_workspace_path_is_scoped_under_storage_root():
    settings = Settings(_env_file=None)
    workspace = settings.workspace_path("abc-123")
    assert workspace == settings.storage_path / "abc-123"


def test_ensure_workspace_creates_the_directory(tmp_path):
    settings = Settings(_env_file=None, STORAGE_DIR=str(tmp_path))
    workspace = settings.ensure_workspace("run-1")

    assert workspace.exists()
    assert workspace.is_dir()


def test_ensure_directories_creates_all_top_level_folders(tmp_path):
    settings = Settings(_env_file=None, STORAGE_DIR=str(tmp_path / "storage"), LOGS_DIR=str(tmp_path / "logs"))
    settings.ensure_directories()

    assert settings.storage_path.exists()
    assert settings.reports_path.exists()
    assert settings.logs_path.exists()
    assert settings.upload_path.exists()


def test_allowed_extensions_defaults_are_lowercase_with_dot():
    settings = Settings(_env_file=None)
    for ext in settings.ALLOWED_EXTENSIONS:
        assert ext.startswith(".")
        assert ext == ext.lower()


def test_production_flag_reflects_environment():
    settings = Settings(_env_file=None, ENVIRONMENT="production")
    assert settings.is_production is True
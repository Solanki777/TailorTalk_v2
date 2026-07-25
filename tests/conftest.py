"""
Shared pytest fixtures for the TestPilot AI test suite.

Running `pytest` from the project root automatically picks this file up
for every test module in `tests/`.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage_service import storage_service
from app.utilities.file_validation import file_validator


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """
    A TestClient wired to a temporary upload directory.

    Uploads made during a test are written to `tmp_path` instead of the
    real `storage/uploads` folder, so tests never leave files behind or
    depend on what's already on disk.
    """
    monkeypatch.setattr(storage_service, "upload_dir", tmp_path)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def restore_file_validator() -> Iterator[None]:
    """Restore the shared FileValidator's size limit after a test changes it."""
    original_limit = file_validator.max_size_bytes
    yield
    file_validator.max_size_bytes = original_limit


@pytest.fixture()
def make_upload_file():
    """
    Return a factory for building `files=` tuples for TestClient uploads.

    Exposed as a fixture (rather than a plain importable function) so test
    modules never need `from tests.conftest import ...` — pytest discovers
    conftest.py automatically. This avoids collisions with any other
    package named "tests" that might already be installed globally.
    """

    def _make(name: str, content: bytes, content_type: str = "application/json"):
        return "file", (name, io.BytesIO(content), content_type)

    return _make
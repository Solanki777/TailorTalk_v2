"""Tests for POST /api/v1/upload — file validation and storage."""

import io
from pathlib import Path

from tests.conftest import make_upload_file

UPLOAD_URL = "/api/v1/upload"


def test_upload_valid_file_succeeds(client):
    content = b'{"scenario": "valid upload"}'
    response = client.post(UPLOAD_URL, files=[make_upload_file("spec.json", content)])

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["filename"] == "spec.json"
    assert body["file_size"] == len(content)


def test_upload_writes_file_to_disk(client, tmp_path):
    content = b"hello workspace"
    response = client.post(UPLOAD_URL, files=[make_upload_file("note.txt", content, "text/plain")])

    saved_path = Path(response.json()["saved_path"])
    assert saved_path.exists()
    assert saved_path.read_bytes() == content
    assert saved_path.parent == tmp_path


def test_upload_generates_unique_filename_on_disk(client):
    """The original name is preserved for display, but the file on disk is prefixed with a UUID."""
    response = client.post(UPLOAD_URL, files=[make_upload_file("report.json", b"{}")])

    body = response.json()
    saved_name = Path(body["saved_path"]).name
    assert saved_name != "report.json"
    assert saved_name.endswith("_report.json")


def test_upload_without_a_file_is_rejected(client):
    response = client.post(UPLOAD_URL)
    assert response.status_code == 422  # FastAPI request-validation error


def test_upload_empty_file_is_rejected(client):
    response = client.post(UPLOAD_URL, files=[make_upload_file("empty.json", b"")])

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_oversized_file_is_rejected(client, restore_file_validator):
    from app.utilities.file_validation import file_validator

    file_validator.max_size_bytes = 10  # shrink the limit for this test only

    response = client.post(UPLOAD_URL, files=[make_upload_file("big.json", b"x" * 1000)])

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_upload_two_files_get_two_distinct_storage_paths(client):
    first = client.post(UPLOAD_URL, files=[make_upload_file("same-name.json", b"one")])
    second = client.post(UPLOAD_URL, files=[make_upload_file("same-name.json", b"two")])

    assert first.json()["saved_path"] != second.json()["saved_path"]


def test_upload_reports_correct_content_length(client):
    content = b"x" * 2048
    response = client.post(UPLOAD_URL, files=[make_upload_file("mid.json", content)])

    assert response.json()["file_size"] == 2048
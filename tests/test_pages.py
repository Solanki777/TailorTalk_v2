"""Tests for server-rendered HTML pages (/, /features, /settings)."""

import pytest


@pytest.mark.parametrize("path", ["/", "/features", "/settings"])
def test_page_returns_200_html(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_home_page_has_upload_dropzone(client):
    response = client.get("/")
    assert 'id="dropzone"' in response.text
    assert 'id="fileInput"' in response.text


def test_home_page_loads_upload_script(client):
    response = client.get("/")
    assert "/static/js/upload.js" in response.text


def test_features_page_lists_all_pipeline_stages(client):
    response = client.get("/features")
    for stage in ["Upload", "Parse", "Rule Engine", "AI Analysis", "Report"]:
        assert stage in response.text


def test_settings_page_shows_missing_key_warning_when_unset(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    response = client.get("/settings")

    assert "Not configured" in response.text
    assert "No Gemini API key detected" in response.text


def test_settings_page_masks_key_when_set(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "sk-real-secret-value")
    response = client.get("/settings")

    assert "sk-real-secret-value" not in response.text  # never leak the full key
    assert "sk-r" in response.text  # first 4 chars shown as a hint


def test_settings_page_reflects_max_file_size(client):
    from app.config import settings

    response = client.get("/settings")
    assert f"{settings.MAX_FILE_SIZE_MB} MB" in response.text


def test_nav_links_point_to_real_routes(client):
    """Guards against nav links silently regressing back to '#' placeholders."""
    response = client.get("/")
    assert 'href="/features"' in response.text
    assert 'href="/settings"' in response.text
    assert 'href="/docs"' in response.text


def test_docs_ui_is_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_is_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "TestPilot AI"


def test_unknown_route_returns_404(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
"""Tests for GET /health — the uptime / smoke-test endpoint."""

from app.config import settings


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_reports_expected_shape(client):
    response = client.get("/health")
    body = response.json()

    assert body["status"] == "healthy"
    assert body["version"] == settings.APP_VERSION
    assert body["environment"] == settings.ENVIRONMENT.value


def test_health_response_has_no_extra_noise(client):
    """The health payload should stay minimal — exactly the 3 documented keys."""
    body = client.get("/health").json()
    assert set(body.keys()) == {"status", "version", "environment"}
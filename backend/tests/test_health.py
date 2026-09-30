"""GET /api/health/ — real service checks, credential-free, safe to probe."""
import pytest
from django.conf import settings


def _secret_values():
    values = []
    for name in ("SECRET_KEY", "ENCRYPTION_KEY", "FERNET_KEY", "GITHUB_CLIENT_SECRET",
                 "GOOGLE_CLIENT_SECRET", "GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"):
        value = getattr(settings, name, "") or ""
        if len(value) >= 8:
            values.append(value)
    return values


@pytest.mark.django_db
def test_health_is_anonymous_and_usable(client):
    resp = client.get("/api/health/")
    # 503 is reserved for "database down" — the DB is up in tests.
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert set(body["services"]) >= {"database", "redis", "celery", "ai_provider", "github", "google"}
    # Per-user integration state is omitted for anonymous probes.
    assert "integrations" not in body


@pytest.mark.django_db
def test_health_reports_only_real_checks(client):
    body = client.get("/api/health/").json()
    for name, check in body["services"].items():
        assert "status" in check, name
        assert isinstance(check["status"], str) and check["status"], name


@pytest.mark.django_db
def test_database_check_is_connected(client):
    body = client.get("/api/health/").json()
    assert body["services"]["database"]["status"] == "connected"


@pytest.mark.django_db
def test_health_contains_no_secrets(client):
    content = client.get("/api/health/").content.decode()
    for secret in _secret_values():
        assert secret not in content, "health endpoint leaked a credential"


@pytest.mark.django_db
def test_health_includes_integrations_for_authenticated_users(auth_client):
    body = auth_client.get("/api/health/").json()
    integrations = body["integrations"]
    assert set(integrations) >= {"github", "linkedin"}
    for entry in integrations.values():
        assert "status" in entry


@pytest.mark.django_db
def test_health_integration_state_reflects_the_database(auth_client, owner):
    from intelligence.models import IntegrationConnection

    IntegrationConnection.objects.create(
        owner=owner, platform="github", status="connected", connected_account="octocat"
    )
    body = auth_client.get("/api/health/").json()
    assert body["integrations"]["github"]["status"] == "connected"
    assert body["integrations"]["linkedin"]["status"] == "not_configured"

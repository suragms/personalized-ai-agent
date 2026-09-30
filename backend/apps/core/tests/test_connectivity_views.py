"""Tests for the per-user data-health endpoint (core.connectivity_views)."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from intelligence.models import IntegrationConnection
from rest_framework.test import APIClient

from ai.models import ProviderConnection, ProviderDefinition

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", email="test@example.com", password="password")


@pytest.mark.django_db
def test_data_health_view(api_client, user):
    api_client.force_authenticate(user=user)

    IntegrationConnection.objects.create(
        owner=user,
        platform="github",
        status="connected",
        retryable=False,
    )

    provider_def = ProviderDefinition.objects.create(
        id="openai",
        display_name="OpenAI",
    )
    ProviderConnection.objects.create(
        owner=user,
        provider=provider_def,
        status="api_error",
        retryable=True,
        last_error_message="Rate limit exceeded",
    )

    url = reverse("data-health")
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.data["results"]

    github_health = next(r for r in results if r["provider"] == "github")
    assert github_health["status"] == "connected"
    assert github_health["retryable"] is False

    openai_health = next(r for r in results if r["provider"] == "openai")
    assert openai_health["status"] == "api_error"
    assert openai_health["retryable"] is True
    assert openai_health["error_message"] == "Rate limit exceeded"

    # Platforms without a connection row must be reported (never hidden).
    linkedin_health = next(r for r in results if r["provider"] == "linkedin")
    assert linkedin_health["status"] == "not_configured"
    assert linkedin_health["data_freshness"] == "no_data"


@pytest.mark.django_db
def test_data_health_requires_authentication(api_client):
    response = api_client.get(reverse("data-health"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_data_health_normalizes_legacy_status_values(api_client, user):
    """Rows written before the unified vocabulary must not break the endpoint."""
    api_client.force_authenticate(user=user)

    # Legacy uppercase + legacy alias values are both accepted on read.
    IntegrationConnection.objects.create(owner=user, platform="github", status="CONNECTED")
    IntegrationConnection.objects.create(owner=user, platform="linkedin", status="error")

    response = api_client.get(reverse("data-health"))
    assert response.status_code == 200

    results = {r["provider"]: r for r in response.data["results"]}
    assert results["github"]["status"] == "connected"
    assert results["linkedin"]["status"] == "api_error"

import pytest
from django.urls import reverse

from ai.models import ProviderConnection, ProviderDefinition


@pytest.fixture
def provider_def(db):
    return ProviderDefinition.objects.create(
        id="openai-compat",
        display_name="OpenAI Compatible",
        category="custom",
        protocol="openai_chat"
    )

@pytest.fixture
def api_client(auth_client, owner):
    return auth_client

@pytest.mark.django_db
def test_provider_connection_owned_by_user(owner, viewer, provider_def):
    # Only owner should access their connection
    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="test1")
    ProviderConnection.objects.create(owner=viewer, provider=provider_def, api_key="test2")

@pytest.mark.django_db
def test_encrypted_credential_not_in_api_response(api_client, owner, provider_def):
    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="secret-api-key")
    resp = api_client.get(reverse("ai-providers-list"))

    # We shouldn't see "secret-api-key" anywhere in the response
    assert resp.status_code == 200
    assert "secret-api-key" not in str(resp.content)

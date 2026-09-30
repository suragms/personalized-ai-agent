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
def test_provider_connection_owned_by_user_via_api(api_client, owner, viewer, provider_def, client):
    # Only owner should access their connection
    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="test1")
    ProviderConnection.objects.create(owner=viewer, provider=provider_def, api_key="test2")

    # 1. Test Unauthenticated
    resp = client.get(reverse("ai-providers-list"))
    assert resp.status_code == 401

    # 2. Test Isolation (owner should only see their own keys)
    resp = api_client.get(reverse("ai-providers-list"))
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1

    # 3. Test Masking Strategy
    obj = resp.data["results"][0]
    assert "api_key" not in obj
    assert obj["api_key_masked"] == "***" or obj["api_key_masked"] == ""

    assert "test1" not in str(resp.content)
    assert "test2" not in str(resp.content)

@pytest.mark.django_db
def test_provider_connection_creation(api_client, owner, provider_def):
    resp = api_client.post(reverse("ai-providers-list"), {
        "provider_id": "openai-compat",
        "display_name": "My Custom OpenAI",
        "api_key": "my_super_secret_key_12345678",
        "base_url": "https://api.openai.local"
    }, format="json")

    assert resp.status_code == 201
    # Check that plaintext doesn't come back on spawn
    assert "my_super_secret_key" not in str(resp.content)

    # Verify DB presence
    conn = ProviderConnection.objects.get()
    assert conn.owner == owner
    assert conn.api_key == "my_super_secret_key_12345678"
    assert conn.display_name == "My Custom OpenAI"

@pytest.mark.django_db
def test_provider_connection_update_rotation(api_client, owner, provider_def):
    conn = ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="old_key")

    resp = api_client.patch(reverse("ai-providers-detail", args=[conn.id]), {
        "api_key": "new_key_rot"
    }, format="json")

    assert resp.status_code == 200
    conn.refresh_from_db()
    assert conn.api_key == "new_key_rot"

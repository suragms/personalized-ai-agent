from unittest.mock import patch

import pytest

from ai.exceptions import AIProviderError
from ai.models import ProviderConnection, ProviderDefinition
from ai.routing import AIRoutingService


@pytest.fixture
def provider_def(db):
    return ProviderDefinition.objects.create(
        id="openai-compat",
        display_name="OpenAI Compatible",
        category="custom",
        protocol="openai_chat"
    )

@pytest.mark.django_db
@patch('ai.providers.openai_provider.OpenAIProvider.complete')
@patch('ai.providers.openai_provider.OpenAIProvider.is_available')
def test_routing_successful_call(mock_avail, mock_comp, owner, provider_def):
    mock_avail.return_value = True
    mock_comp.return_value = "Success"

    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-1")

    svc = AIRoutingService(owner)
    res = svc.complete("system", "user")

    assert res == "Success"
    mock_comp.assert_called_once()


@pytest.mark.django_db
@patch('ai.providers.openai_provider.OpenAIProvider.complete')
@patch('ai.providers.openai_provider.OpenAIProvider.is_available')
def test_routing_fallback_on_timeout(mock_avail, mock_comp, owner, provider_def):
    mock_avail.return_value = True
    mock_comp.side_effect = [Exception("timeout error!"), "Fallback Success"]

    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-primary", is_default=True)
    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-fallback")

    svc = AIRoutingService(owner)
    res = svc.complete("system", "user")

    assert res == "Fallback Success"
    assert mock_comp.call_count == 2

@pytest.mark.django_db
@patch('ai.providers.openai_provider.OpenAIProvider.complete')
@patch('ai.providers.openai_provider.OpenAIProvider.is_available')
def test_routing_halts_on_auth_error(mock_avail, mock_comp, owner, provider_def):
    mock_avail.return_value = True
    mock_comp.side_effect = [Exception("401 Unauthorized"), "Fallback Success"]

    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-primary", is_default=True)
    ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-fallback")

    svc = AIRoutingService(owner)
    with pytest.raises(AIProviderError) as e:
        svc.complete("sys", "usr")

    assert "AI_PROVIDER_AUTH_FAILED" in str(e.value.code)
    assert mock_comp.call_count == 1

@pytest.mark.django_db
@patch('ai.providers.openai_provider.OpenAIProvider.complete')
@patch('ai.providers.openai_provider.OpenAIProvider.is_available')
def test_test_connection_endpoint_success(mock_avail, mock_comp, owner, provider_def):
    mock_avail.return_value = True
    mock_comp.return_value = "ok"

    conn = ProviderConnection.objects.create(owner=owner, provider=provider_def, api_key="sk-primary")

    svc = AIRoutingService(owner)
    res = svc.test_connection(conn)

    assert res["status"] == "ok"
    assert "latency_ms" in res

    conn.refresh_from_db()
    assert conn.latency_ms is not None
    assert conn.last_tested_at is not None
    assert conn.last_error_code == ""

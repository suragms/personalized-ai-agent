"""WebSocket JWT auth: token extraction and validation (config/ws_auth.py)."""
import pytest
from django.contrib.auth.models import AnonymousUser

from config.ws_auth import _extract_token, authenticate_token


def _scope(query=b"", headers=(), user=None):
    return {
        "type": "websocket",
        "query_string": query,
        "headers": list(headers),
        "user": user or AnonymousUser(),
    }


def test_extract_token_from_query_string():
    assert _extract_token(_scope(query=b"token=abc123")) == "abc123"


def test_extract_token_from_access_alias():
    assert _extract_token(_scope(query=b"access=xyz")) == "xyz"


def test_extract_token_from_authorization_header():
    scope = _scope(headers=[(b"authorization", b"Bearer header-token")])
    assert _extract_token(scope) == "header-token"


def test_extract_token_prefers_query_over_header():
    scope = _scope(
        query=b"token=from-query",
        headers=[(b"authorization", b"Bearer from-header")],
    )
    assert _extract_token(scope) == "from-query"


def test_extract_token_missing_returns_none():
    assert _extract_token(_scope()) is None


def test_extract_token_ignores_empty_values():
    assert _extract_token(_scope(query=b"token=")) is None


def test_non_bearer_header_is_ignored():
    scope = _scope(headers=[(b"authorization", b"Basic dXNlcjpwYXNz")])
    assert _extract_token(scope) is None


@pytest.mark.django_db
def test_authenticate_token_accepts_valid_jwt(owner):
    from rest_framework_simplejwt.tokens import AccessToken

    user = authenticate_token(str(AccessToken.for_user(owner)))
    assert user is not None
    assert user.pk == owner.pk


@pytest.mark.django_db
def test_authenticate_token_rejects_garbage(owner):
    assert authenticate_token("not.a.jwt") is None
    assert authenticate_token("") is None
    assert authenticate_token("eyJhbGciOiJIUzI1NiJ9.bogus.sig") is None

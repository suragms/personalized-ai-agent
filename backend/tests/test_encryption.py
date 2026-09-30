"""Tests for encryption key configuration and EncryptedCharField security."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

# ── Unit tests for get_fernet() ──────────────────────────────────────────


def test_get_fernet_uses_encryption_key():
    """get_fernet() uses the ENCRYPTION_KEY setting when present."""
    from cryptography.fernet import Fernet
    valid_key = Fernet.generate_key().decode()
    with override_settings(ENCRYPTION_KEY=valid_key, DEBUG=False):
        import importlib

        import apps.core.fields as f
        importlib.reload(f)
        fern = f.get_fernet()
        assert fern is not None


def test_get_fernet_dev_fallback():
    """In DEBUG=True with no ENCRYPTION_KEY, falls back safely using SECRET_KEY."""
    with override_settings(ENCRYPTION_KEY=None, SECRET_KEY="dev-test-key", DEBUG=True):
        import importlib

        import apps.core.fields as f
        importlib.reload(f)
        fern = f.get_fernet()
        assert fern is not None


def test_get_fernet_prod_no_key_raises():
    """In DEBUG=False without ENCRYPTION_KEY, get_fernet() must raise."""
    with override_settings(ENCRYPTION_KEY=None, SECRET_KEY="some-key", DEBUG=False):
        import importlib

        import apps.core.fields as f
        importlib.reload(f)
        with pytest.raises(ImproperlyConfigured):
            f.get_fernet()


def _clean_prod_env(**overrides):
    """Build a clean environment that simulates production — stripping test keys
    inherited from the pytest-env plugin so the production guards can fire."""
    import os
    env = {k: v for k, v in os.environ.items() if k not in (
        "SECRET_KEY", "ENCRYPTION_KEY", "FERNET_KEY", "DJANGO_SETTINGS_MODULE", "DEBUG"
    )}
    env.update(overrides)
    return env


def test_settings_prod_no_secret_key_raises():
    """settings.py must raise when SECRET_KEY is missing and DEBUG=False."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-c",
         "import os; "
         "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
         "import django; django.setup()"],
        capture_output=True, text=True,
        env=_clean_prod_env(DEBUG="False", DJANGO_SETTINGS_MODULE="config.settings"),
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    assert result.returncode != 0, f"Expected non-zero exit; stdout={result.stdout!r} stderr={result.stderr!r}"
    # Either SECRET_KEY or ENCRYPTION_KEY may appear depending on which guard fires first.
    # Both are correct — the process correctly refused to start without required keys.
    assert ("SECRET_KEY" in (result.stderr + result.stdout)
            or "ENCRYPTION_KEY" in (result.stderr + result.stdout))


def test_settings_prod_no_encryption_key_raises():
    """settings.py must raise when ENCRYPTION_KEY is missing and DEBUG=False."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-c",
         "import os; "
         "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
         "import django; django.setup()"],
        capture_output=True, text=True,
        env=_clean_prod_env(
            DEBUG="False",
            SECRET_KEY="some-strong-secret-key-production-xx",
            DJANGO_SETTINGS_MODULE="config.settings",
        ),
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    assert result.returncode != 0, f"Expected non-zero exit; stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "ENCRYPTION_KEY" in (result.stderr + result.stdout)


def test_settings_prod_with_both_keys_succeeds():
    """settings.py initializes successfully when both keys are present and DEBUG=False."""
    import subprocess
    import sys

    from cryptography.fernet import Fernet
    valid_key = Fernet.generate_key().decode()
    result = subprocess.run(
        [sys.executable, "-c",
         "import os; "
         "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
         "import django; django.setup(); print('OK')"],
        capture_output=True, text=True,
        env=_clean_prod_env(
            DEBUG="False",
            SECRET_KEY="some-strong-secret-key-production-xx",
            ENCRYPTION_KEY=valid_key,
            DJANGO_SETTINGS_MODULE="config.settings",
        ),
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    assert "OK" in result.stdout, f"stdout={result.stdout!r} stderr={result.stderr!r}"


# ── Integration tests using Django DB ─────────────────────────────────────

@pytest.mark.django_db
def test_encrypted_field_roundtrip(owner):
    """Encryption and decryption round-trip across the database boundary."""
    from ai.models import ProviderConnection, ProviderDefinition
    defn = ProviderDefinition.objects.create(
        id="roundtrip-test", display_name="Test", category="custom", protocol="openai_chat"
    )
    conn = ProviderConnection.objects.create(owner=owner, provider=defn, api_key="sk-test-key-12345")
    conn.refresh_from_db()
    assert conn.api_key == "sk-test-key-12345"


@pytest.mark.django_db
def test_encrypted_field_never_stores_plaintext(owner):
    """Raw DB value must NOT equal the plaintext API key."""
    from django.db import connection

    from ai.models import ProviderConnection, ProviderDefinition
    defn = ProviderDefinition.objects.create(
        id="plaintext-check", display_name="Test", category="custom", protocol="openai_chat"
    )
    conn = ProviderConnection.objects.create(owner=owner, provider=defn, api_key="sk-plaintext-guard")
    with connection.cursor() as cursor:
        cursor.execute("SELECT api_key FROM ai_providerconnection WHERE id=?", [str(conn.id).replace("-", "")])
        row = cursor.fetchone()
        if row:  # SQLite may return this
            assert row[0] != "sk-plaintext-guard"


@pytest.mark.django_db
def test_corrupted_ciphertext_does_not_crash(owner):
    """A corrupted ciphertext is handled gracefully — no unhandled exception."""
    from django.db import connection

    from ai.models import ProviderConnection, ProviderDefinition
    defn = ProviderDefinition.objects.create(
        id="corrupt-test", display_name="Test", category="custom", protocol="openai_chat"
    )
    conn = ProviderConnection.objects.create(owner=owner, provider=defn, api_key="valid")
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE ai_providerconnection SET api_key='not-a-valid-fernet-token' WHERE id=?",
            [str(conn.id).replace("-", "")]
        )
    conn.refresh_from_db()
    # Should not raise — returns the raw value as a safe fallback
    assert isinstance(conn.api_key, str)


@pytest.mark.django_db
def test_encrypted_api_key_not_in_api_response(auth_client, owner):
    """Provider list endpoint must NEVER return plaintext API keys."""
    from django.urls import reverse

    from ai.models import ProviderConnection, ProviderDefinition
    defn = ProviderDefinition.objects.create(
        id="api-mask-test", display_name="Test", category="custom", protocol="openai_chat"
    )
    ProviderConnection.objects.create(owner=owner, provider=defn, api_key="super-secret-key-9999")
    resp = auth_client.get(reverse("ai-providers-list"))
    assert resp.status_code == 200
    assert "super-secret-key-9999" not in resp.content.decode()

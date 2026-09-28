"""Root-level conftest.py — runs before Django settings are loaded.

The pytest_configure hook sets environment variables that Django settings
need at load time. This is the correct place to inject test-only secrets
because pytest_configure fires before pytest-django initialises Django.

The FERNET_KEY here is a dedicated, deterministic test key.
It is NEVER a production credential:
  - not valid for production data
  - not present in .env.example as a recommended production value
  - committed in plain sight to signal it has no secret value

If a test run's DB ever holds real production credentials, the data itself
was misconfigured — not this key.
"""
import os


# A valid Fernet key for testing only — zero secret value.
# Regenerate at any time; it will only break tests that need re-seeding.
_TEST_FERNET_KEY = "test-only-fernet-key-not-secret-00000000000="


def pytest_configure(config):
    """Set environment variables before Django settings are imported."""
    os.environ.setdefault("SECRET_KEY", "test-only-django-secret-key-change-in-prod")
    # Provide a valid Fernet key so EncryptedCharField works in tests
    # without falling through to the SECRET_KEY derivation path.
    if not os.environ.get("FERNET_KEY"):
        # Derive a proper Fernet key from the test string so it's a valid
        # 32-byte base64url value rather than an arbitrary ASCII string.
        import base64
        padded = (_TEST_FERNET_KEY.encode("utf-8").ljust(32, b"0"))[:32]
        os.environ["FERNET_KEY"] = base64.urlsafe_b64encode(padded).decode()

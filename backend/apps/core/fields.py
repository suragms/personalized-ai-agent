import base64
import logging
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def get_fernet():
    """Get the Fernet cipher using the dedicated FERNET_KEY (preferred) or
    derive from SECRET_KEY (dev-only, never do this in production).

    Production environments must set FERNET_KEY explicitly. Changing SECRET_KEY
    without migrating FERNET_KEY will make all encrypted credentials undecryptable.
    """
    # Prefer an explicit FERNET_KEY / ENCRYPTION_KEY env var over SECRET_KEY
    key = getattr(settings, "ENCRYPTION_KEY", None) or getattr(settings, "FERNET_KEY", None)
    if not key:
        sk = getattr(settings, "SECRET_KEY", "").encode("utf-8")
        if not sk:
            raise ImproperlyConfigured("SECRET_KEY must not be empty.")
        # Derive a 32-byte base64 key from SECRET_KEY (dev fallback only).
        # In production, set FERNET_KEY to an independent key so SECRET_KEY
        # can be rotated without re-encrypting all credentials.
        padded_key = (sk.ljust(32, b"0"))[:32]
        key = base64.urlsafe_b64encode(padded_key)
        if getattr(settings, "DEBUG", True) is False:
            # Guard: in production, failing open here is a security risk.
            raise ImproperlyConfigured(
                "FERNET_KEY must be set explicitly in production. "
                "Do NOT rely on SECRET_KEY derivation for credential encryption."
            )
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)

class EncryptedCharField(models.CharField):
    """
    A simple Django CharField that transparently encrypts content at rest
    using Fernet AES-128-CBC encryption.
    """
    
    def get_prep_value(self, value):
        db_val = super().get_prep_value(value)
        if db_val is None or db_val == "":
            return db_val
            
        # Encrypt the string
        fernet = get_fernet()
        # Convert string to bytes
        val_bytes = str(db_val).encode('utf-8')
        # Encrypt and convert back to string for storage
        return fernet.encrypt(val_bytes).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
            
        fernet = get_fernet()
        try:
            val_bytes = str(value).encode('utf-8')
            return fernet.decrypt(val_bytes).decode('utf-8')
        except (InvalidToken, TypeError, ValueError):
            # In case the database holds unencrypted legacy data or the key changed
            return value

    def to_python(self, value):
        # Called during deserialization and clean()
        if value is None or value == "":
            return value
            
        if isinstance(value, str):
            # Attempt to decrypt if it looks like a fernet token (starts with gAAAA)
            if value.startswith("gAAAA"):
                try:
                    fernet = get_fernet()
                    return fernet.decrypt(value.encode('utf-8')).decode('utf-8')
                except (InvalidToken, TypeError, ValueError):
                    pass
        return value

class SafeArrayField(models.JSONField):
    """
    Cross-backend array field: uses PostgreSQL ArrayField on PostgreSQL,
    and JSONField (supporting list values) on SQLite/other backends for test compatibility.
    """
    def __init__(self, base_field=None, size=None, **kwargs):
        self.base_field = base_field
        self.size = size
        kwargs.setdefault('default', list)
        super().__init__(**kwargs)

    def db_type(self, connection):
        if connection.vendor == 'postgresql':
            try:
                from django.contrib.postgres.fields import ArrayField
                return ArrayField(self.base_field, size=self.size).db_type(connection)
            except Exception:
                pass
        return super().db_type(connection)

    def formfield(self, **kwargs):
        return super().formfield(**kwargs)

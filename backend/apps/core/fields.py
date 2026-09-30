import base64
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

logger = logging.getLogger(__name__)

def get_fernet():
    key = getattr(settings, "ENCRYPTION_KEY", None) or getattr(settings, "FERNET_KEY", None)
    if not key:
        sk = getattr(settings, "SECRET_KEY", "").encode("utf-8")
        if not sk:
            raise ImproperlyConfigured("SECRET_KEY must not be empty.")
        padded_key = (sk.ljust(32, b"0"))[:32]
        key = base64.urlsafe_b64encode(padded_key)
        if getattr(settings, "DEBUG", True) is False:
            raise ImproperlyConfigured(
                "FERNET_KEY must be set explicitly in production. "
                "Do NOT rely on SECRET_KEY derivation for credential encryption."
            )
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)

class EncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        db_val = super().get_prep_value(value)
        if db_val is None or db_val == "":
            return db_val
        fernet = get_fernet()
        val_bytes = str(db_val).encode('utf-8')
        return fernet.encrypt(val_bytes).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        fernet = get_fernet()
        try:
            val_bytes = str(value).encode('utf-8')
            return fernet.decrypt(val_bytes).decode('utf-8')
        except (InvalidToken, TypeError, ValueError):
            return value

    def to_python(self, value):
        if value is None or value == "":
            return value
        if isinstance(value, str):
            if value.startswith("gAAAA"):
                try:
                    fernet = get_fernet()
                    return fernet.decrypt(value.encode('utf-8')).decode('utf-8')
                except (InvalidToken, TypeError, ValueError):
                    pass
        return value


# Dynamic Base class resolution for SafeArrayField
# Production ALWAYS uses PostgreSQL ArrayField. Tests on SQLite use JSONField.
_USE_SQLITE = getattr(settings, 'USE_SQLITE', False) or 'sqlite3' in settings.DATABASES.get('default', {}).get('ENGINE', '')

if _USE_SQLITE:
    _ArrayFieldBase = models.JSONField
else:
    from django.contrib.postgres.fields import ArrayField
    _ArrayFieldBase = ArrayField

class SafeArrayField(_ArrayFieldBase):
    """
    Cross-backend array field:
    - Production (PostgreSQL): Inherits from django.contrib.postgres.fields.ArrayField.
      Preserves all native PG array behaviors, operators (@>), and binary transport.
    - Testing (SQLite): Inherits from django.db.models.JSONField.
      Permits the test suite to store lists on SQLite where 'text[]' is invalid.
    """
    def __init__(self, base_field=None, size=None, **kwargs):
        self.base_field = base_field
        self.size = size
        kwargs.setdefault('default', list)

        if _USE_SQLITE:
            # JSONField does not accept base_field or size
            super().__init__(**kwargs)
        else:
            # PostgreSQL ArrayField REQUIRES base_field
            super().__init__(base_field=base_field, size=size, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Always output the path to our proxy class, not the base class
        if path.startswith('django.db.models') or path.startswith('django.contrib.postgres'):
            path = 'core.fields.SafeArrayField'

        # Ensure base_field and size are always preserved in the migration,
        # even if generated from a SQLite environment.
        if self.base_field is not None:
            kwargs['base_field'] = self.base_field
        if self.size is not None:
            kwargs['size'] = self.size

        return name, path, args, kwargs

import pytest
from core.fields import EncryptedCharField
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

# We need a dummy model to test the field
class DummySecureModel(models.Model):
    secret = EncryptedCharField(max_length=255, blank=True)
    
    class Meta:
        app_label = 'core'

@pytest.mark.django_db
def test_encrypted_char_field_roundtrip():
    # 1. encrypt/decrypt round trip
    # 2. database persistence
    instance = DummySecureModel.objects.create(secret="my_super_secret_api_key")
    
    # Reload from DB
    instance.refresh_from_db()
    assert instance.secret == "my_super_secret_api_key"

    # Check raw DB value to ensure it's encrypted
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT secret FROM core_dummysecuremodel WHERE id=%s", [instance.id])
        row = cursor.fetchone()
        raw_val = row[0]
        assert raw_val != "my_super_secret_api_key"
        assert raw_val.startswith("gAAAA")  # Fernet token format

@pytest.mark.django_db
def test_encrypted_char_field_invalid_ciphertext():
    # 4. invalid/corrupted ciphertext
    # Should fall back to just returning the raw value (legacy support)
    from django.db import connection
    instance = DummySecureModel.objects.create(secret="valid_first")
    with connection.cursor() as cursor:
        cursor.execute("UPDATE core_dummysecuremodel SET secret='invalid_fake_ciphertext' WHERE id=%s", [instance.id])
    
    instance.refresh_from_db()
    assert instance.secret == "invalid_fake_ciphertext"

@pytest.mark.django_db
def test_encrypted_char_field_empty():
    instance = DummySecureModel.objects.create(secret="")
    instance.refresh_from_db()
    assert instance.secret == ""

@pytest.mark.django_db
def test_encrypted_char_field_missing_key():
    # 5. missing encryption key
    with override_settings(SECRET_KEY="", ENCRYPTION_KEY=None, FERNET_KEY=None):
        with pytest.raises(ImproperlyConfigured):
            instance = DummySecureModel.objects.create(secret="test")


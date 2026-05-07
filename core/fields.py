from django.db import models
from .encryption import get_keyring


class EncryptedTextField(models.TextField):
    """
    TextField that encrypts data at application level using Fernet.
    Supports key rotation via Keyring.
    """

    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None:
            return None
        keyring = get_keyring()
        return keyring.encrypt(value)

    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None:
            return None
        keyring = get_keyring()
        return keyring.decrypt(value)

    def to_python(self, value):
        """Convert database value to Python type."""
        if value is None or isinstance(value, str):
            return value
        return str(value)


class EncryptedCharField(models.CharField):
    """
    CharField that encrypts data at application level using Fernet.
    """

    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None:
            return None
        keyring = get_keyring()
        return keyring.encrypt(value)

    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None:
            return None
        keyring = get_keyring()
        return keyring.decrypt(value)

    def to_python(self, value):
        """Convert database value to Python type."""
        if value is None or isinstance(value, str):
            return value
        return str(value)

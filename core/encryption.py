from cryptography.fernet import Fernet, MultiFernet
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class Keyring:
    """
    Manage encryption keys with key rotation support (kid - Key ID).
    """

    _instance: Optional['Keyring'] = None
    _keys: list[bytes] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize keyring from environment or generate new keys."""
        key_env = os.getenv('ENCRYPTION_KEYS')
        if key_env:
            keys_list = key_env.split(',')
            self._keys = [k.strip().encode() if isinstance(k, str) else k for k in keys_list]
        else:
            primary_key = os.getenv('PRIMARY_ENCRYPTION_KEY', Fernet.generate_key().decode())
            self._keys = [primary_key.encode() if isinstance(primary_key, str) else primary_key]
        logger.info(f"Keyring initialized with {len(self._keys)} key(s)")

    def get_cipher(self) -> MultiFernet:
        """Get MultiFernet cipher for encryption/decryption with multiple keys."""
        return MultiFernet([Fernet(key) for key in self._keys])

    def add_key(self, key: bytes):
        """Add a new key for rotation purposes."""
        if key not in self._keys:
            self._keys.insert(0, key)
            logger.info("New encryption key added for rotation")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string."""
        cipher = self.get_cipher()
        encrypted = cipher.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string."""
        cipher = self.get_cipher()
        decrypted = cipher.decrypt(ciphertext.encode())
        return decrypted.decode()


def get_keyring() -> Keyring:
    """Get singleton Keyring instance."""
    return Keyring()

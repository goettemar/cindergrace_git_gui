import pytest

from openrouter import CRYPTO_AVAILABLE, decrypt_api_key, encrypt_api_key


pytestmark = pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")


def test_encrypt_decrypt_roundtrip():
    payload = encrypt_api_key("secret-key", "password")
    assert decrypt_api_key(payload, "password") == "secret-key"

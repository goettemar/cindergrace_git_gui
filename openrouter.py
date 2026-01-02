"""OpenRouter helpers for commit message suggestions."""
import base64
import os
from typing import Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception
    PBKDF2HMAC = None
    hashes = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _derive_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_api_key(api_key: str, password: str) -> dict:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography is required for encryption")
    salt = os.urandom(16)
    key = _derive_fernet_key(password, salt)
    token = Fernet(key).encrypt(api_key.encode("utf-8"))
    return {
        "salt": base64.b64encode(salt).decode("ascii"),
        "token": token.decode("ascii"),
    }


def decrypt_api_key(payload: dict, password: str) -> str:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography is required for encryption")
    salt = base64.b64decode(payload.get("salt", ""))
    token = payload.get("token", "").encode("ascii")
    key = _derive_fernet_key(password, salt)
    return Fernet(key).decrypt(token).decode("utf-8")


def openrouter_request(api_key: str, model: str, prompt: str, api_url: Optional[str] = None) -> str:
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("requests is required for OpenRouter calls")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://git-gui.local",
        "X-Title": "Git GUI",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You generate concise git commit messages."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 120,
    }
    target = api_url or OPENROUTER_API_URL
    response = requests.post(target, headers=headers, json=payload, timeout=60)
    if response.status_code == 401:
        raise RuntimeError("OpenRouter auth failed (401)")
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter error: {response.status_code} {response.text}")
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    return content


__all__ = [
    "CRYPTO_AVAILABLE",
    "REQUESTS_AVAILABLE",
    "InvalidToken",
    "OPENROUTER_API_URL",
    "encrypt_api_key",
    "decrypt_api_key",
    "openrouter_request",
]

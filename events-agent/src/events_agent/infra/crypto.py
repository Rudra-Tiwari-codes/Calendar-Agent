from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .settings import settings


def get_fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError("FERNET_KEY not configured")
    return Fernet(settings.fernet_key)


def encrypt_text(plaintext: str) -> str:
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str) -> str:
    f = get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")



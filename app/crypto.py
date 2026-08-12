"""Encrypt GitHub access tokens before they hit the database.

A GitHub access token is effectively a password to the user's account
(scoped to whatever the OAuth app requested). We never store it in
plaintext — it's encrypted with a symmetric Fernet key that lives only
in the server's environment (TOKEN_ENCRYPTION_KEY), never in the repo
or the database itself.
"""
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet() -> Fernet:
    key = current_app.config.get("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\" and add it to your .env"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext_token: str) -> str:
    return _fernet().encrypt(plaintext_token.encode()).decode()


def decrypt_token(ciphertext_token: str) -> str:
    try:
        return _fernet().decrypt(ciphertext_token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored access token could not be decrypted") from exc

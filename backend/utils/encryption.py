
import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()


def _get_fernet() -> Fernet:
    """Create the encryption handler using the backend master key."""
    master_key = os.getenv("TAILORTALK_MASTER_KEY")

    if not master_key:
        raise RuntimeError(
            "TAILORTALK_MASTER_KEY is missing from backend/.env"
        )

    try:
        return Fernet(master_key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "TAILORTALK_MASTER_KEY is invalid. Generate a valid Fernet key."
        ) from exc


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key before storing it."""
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty.")

    return _get_fernet().encrypt(
        api_key.strip().encode("utf-8")
    ).decode("utf-8")


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a previously encrypted API key."""
    try:
        return _get_fernet().decrypt(
            encrypted_key.encode("utf-8")
        ).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise RuntimeError(
            "Could not decrypt the API key. Check the master key and stored data."
        ) from exc

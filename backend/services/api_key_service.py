
import json
from pathlib import Path

from backend.utils.encryption import encrypt_api_key, decrypt_api_key

# Store application data outside the public frontend directory.
STORAGE_DIR = Path(__file__).resolve().parents[2] / "data"
STORAGE_FILE = STORAGE_DIR / "api_keys.json"

SUPPORTED_PROVIDERS = {"groq", "gemini"}


def save_api_key(provider: str, api_key: str) -> None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    encrypted_key = encrypt_api_key(api_key)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    data = {}
    if STORAGE_FILE.exists():
        try:
            data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError("Could not read API key storage.") from exc

    data[provider] = encrypted_key

    temp_file = STORAGE_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(STORAGE_FILE)


def get_api_key(provider: str) -> str | None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    if not STORAGE_FILE.exists():
        return None

    try:
        data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Could not read API key storage.") from exc

    encrypted_key = data.get(provider)
    if not encrypted_key:
        return None

    return decrypt_api_key(encrypted_key)


def get_key_status() -> dict:
    """Report which providers have saved keys without exposing them."""
    if not STORAGE_FILE.exists():
        return {"groq": False, "gemini": False}

    try:
        data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Could not read API key storage.") from exc

    return {
        provider: bool(data.get(provider))
        for provider in SUPPORTED_PROVIDERS
    }


def delete_api_key(provider: str) -> None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    if not STORAGE_FILE.exists():
        return

    try:
        data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Could not read API key storage.") from exc

    data.pop(provider, None)

    if data:
        STORAGE_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
    else:
        STORAGE_FILE.unlink(missing_ok=True)

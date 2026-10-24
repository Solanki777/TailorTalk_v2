import json
from pathlib import Path

from backend.utils.encryption import encrypt_api_key, decrypt_api_key

# Store encrypted application keys outside the frontend directory.
STORAGE_DIR = Path(__file__).resolve().parents[2] / "data"
STORAGE_FILE = STORAGE_DIR / "api_keys.json"

SUPPORTED_PROVIDERS = {"groq"}


def _read_keys() -> dict:
    if not STORAGE_FILE.exists():
        return {}

    try:
        data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("API key storage has an invalid format.")
        return data
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Could not read API key storage.") from exc


def save_api_key(provider: str, api_key: str) -> None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    encrypted_key = encrypt_api_key(api_key)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    data = _read_keys()

    # Remove any legacy Gemini key during migration.
    data.pop("gemini", None)
    data[provider] = encrypted_key

    temp_file = STORAGE_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp_file.replace(STORAGE_FILE)


def get_api_key(provider: str) -> str | None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    encrypted_key = _read_keys().get(provider)

    if not encrypted_key:
        return None

    return decrypt_api_key(encrypted_key)


def get_key_status() -> dict:
    """Return saved-key status without exposing API keys."""
    data = _read_keys()
    return {"groq": bool(data.get("groq"))}


def delete_api_key(provider: str) -> None:
    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported API key provider.")

    data = _read_keys()

    # Remove the legacy Gemini entry as well.
    data.pop("gemini", None)
    data.pop(provider, None)

    if data:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
    else:
        STORAGE_FILE.unlink(missing_ok=True)



def get_masked_api_key(provider: str) -> str | None:
    api_key = get_api_key(provider)

    if not api_key:
        return None

    if len(api_key) <= 8:
        return "*" * len(api_key)

    return f"{api_key[:4]}{'*' * 8}{api_key[-4:]}"
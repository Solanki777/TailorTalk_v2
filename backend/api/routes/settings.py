
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from groq import Groq

from backend.services.api_key_service import (
    save_api_key,
    get_key_status,
    get_masked_api_key,
    delete_api_key,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


class APIKeyRequest(BaseModel):
    provider: str
    api_key: str = Field(min_length=1, max_length=500)


def validate_api_key(provider: str, api_key: str) -> bool:
    """Validate a Groq API key without storing or returning it."""
    if provider != "groq":
        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq.",
        )

    try:
        client = Groq(api_key=api_key)
        client.models.list()
        return True
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)

        if status_code in (400, 401, 403):
            return False

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not validate the Groq API key. "
                "Check your connection and try again."
            ),
        ) from exc


def build_key_response():
    """Return key status and a masked key, never the full secret."""
    return {
        "providers": get_key_status(),
        "masked_keys": {
            "groq": get_masked_api_key("groq"),
        },
    }


@router.get("/keys")
def key_status():
    """Return configuration status and masked key."""
    return build_key_response()


@router.post("/keys")
def add_key(payload: APIKeyRequest):
    provider = payload.provider.strip().lower()
    api_key = payload.api_key.strip()

    if provider != "groq":
        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq.",
        )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Please enter a Groq API key.",
        )

    if not validate_api_key(provider, api_key):
        raise HTTPException(
            status_code=400,
            detail="The Groq API key is invalid.",
        )

    try:
        save_api_key(provider, api_key)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not securely save the API key.",
        ) from exc

    return {
        "success": True,
        "message": "Groq API key validated and saved.",
        **build_key_response(),
    }


@router.delete("/keys/{provider}")
def remove_key(provider: str):
    provider = provider.strip().lower()

    if provider != "groq":
        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq.",
        )

    try:
        delete_api_key(provider)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not delete the saved API key.",
        ) from exc

    return {
        "success": True,
        "message": "Groq API key removed.",
        **build_key_response(),
    }

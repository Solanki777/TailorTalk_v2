
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from groq import Groq

from backend.services.api_key_service import (
    save_api_key,
    get_api_key,
    get_key_status,
    delete_api_key,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


class APIKeyRequest(BaseModel):
    provider: str
    api_key: str = Field(min_length=1, max_length=500)


def validate_api_key(provider: str, api_key: str) -> bool:
    """Check a provider's API key without storing or returning it."""
    try:
        if provider == "groq":
            client = Groq(api_key=api_key)
            client.models.list()
            return True

        if provider == "gemini":
            request = Request(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": api_key},
                method="GET",
            )

            with urlopen(request, timeout=15) as response:
                return response.status == 200

        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq or gemini.",
        )

    except HTTPException:
        raise
    except HTTPError as exc:
        if exc.code in (400, 401, 403):
            return False
        raise HTTPException(
            status_code=502,
            detail="The provider could not validate the key right now.",
        ) from exc
    except (URLError, TimeoutError):
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the provider. Try again.",
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Key validation failed unexpectedly. Try again.",
        )


@router.get("/keys")
def key_status():
    """Return configuration status only; never return API keys."""
    return {"providers": get_key_status()}


@router.post("/keys")
def add_key(payload: APIKeyRequest):
    provider = payload.provider.strip().lower()
    api_key = payload.api_key.strip()

    if provider not in {"groq", "gemini"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq or gemini.",
        )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Please enter an API key.",
        )

    if not validate_api_key(provider, api_key):
        raise HTTPException(
            status_code=400,
            detail=f"The {provider.capitalize()} API key is invalid.",
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
        "message": f"{provider.capitalize()} API key validated and saved.",
        "providers": get_key_status(),
    }


@router.delete("/keys/{provider}")
def remove_key(provider: str):
    provider = provider.strip().lower()

    if provider not in {"groq", "gemini"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported provider. Use groq or gemini.",
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
        "message": f"{provider.capitalize()} API key removed.",
        "providers": get_key_status(),
    }

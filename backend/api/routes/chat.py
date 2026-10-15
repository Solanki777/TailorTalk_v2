
import uuid

from fastapi import APIRouter, HTTPException

from backend.schemas.chat import ChatRequest
from backend.services.chat_service import Chatservice
from backend.session.session_store import SessionStore

router = APIRouter()

serv = Chatservice()
session_store = SessionStore()


@router.post("/chat")
def chat(request: ChatRequest):
    session_id = request.session_id

    if not session_id:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)

    session = session_store.get_session(session_id)

    # Start a new session if the requested one expired or does not exist.
    if session is None:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)
        session = session_store.get_session(session_id)

    # Capture history before adding the current user message.
    history = session["messages"].copy()
    last_intent = session.get("last_intent")

    try:
        response = serv.process_message(
            request.message,
            history=history,
            last_intent=last_intent,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to process your search request.",
        ) from exc

    # Save the user message only after successful processing.
    session_store.add_message(
        session_id,
        "user",
        request.message,
    )

    # Persist the latest structured search intent.
    new_intent = response["intent"]

    if hasattr(new_intent, "model_dump"):
        new_intent = new_intent.model_dump()

    session_store.update_last_intent(session_id, new_intent)

    # Store a concise assistant message, not the complete result dictionary.
    file_count = len(response.get("files", []))

    assistant_message = (
        f"Found {file_count} matching file(s)."
        if file_count
        else "No matching files found."
    )

    session_store.add_message(
        session_id,
        "assistant",
        assistant_message,
    )

    return {
        "session_id": session_id,
        "message": response,
    }

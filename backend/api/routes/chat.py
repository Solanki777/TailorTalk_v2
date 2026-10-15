
from fastapi import APIRouter, HTTPException
import uuid

from backend.schemas.chat import ChatRequest
from backend.services.chat_service import Chatservice
from backend.session.session_store import SessionStore

router = APIRouter()

serv = Chatservice()
session_store = SessionStore()


@router.post("/chat")
def chat(request: ChatRequest):
    session_id = request.session_id

    # Create a new session when no ID is provided.
    if not session_id:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)

    # Load the requested session.
    session = session_store.get_session(session_id)

    # An expired or unknown session starts fresh.
    # An expired or unknown session starts with a fresh ID.
    if session is None:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)
        session = session_store.get_session(session_id)

    # Save the current user message.
    session_store.add_message(
        session_id,
        "user",
        request.message
    )

    # Process using the previous conversation and search intent.
    try:
        response = serv.process_message(
            request.message,
            history=session["messages"][:-1],
            last_intent=session.get("last_intent")
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to process your search request."
        ) from exc

    # Store the updated structured search intent.
    new_intent = response["intent"]

    if hasattr(new_intent, "model_dump"):
        new_intent = new_intent.model_dump()

    session_store.update_last_intent(
        session_id,
        new_intent
    )

    # Save the assistant response.
    session_store.add_message(
        session_id,
        "assistant",
        str(response)
    )

    return {
        "session_id": session_id,
        "message": response
    }

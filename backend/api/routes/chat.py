
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
    # Get the existing session ID or create a new session.
    session_id = request.session_id

    if not session_id:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)

    session = session_store.get_session(session_id)

    # Create a new session if the requested session expired or does not exist.
    if session is None:
        session_id = str(uuid.uuid4())
        session_store.create_session(session_id)
        session = session_store.get_session(session_id)

    # Capture conversation history before adding the current user message.
    history = session["messages"].copy()
    last_intent = session.get("last_intent")

    # Process the user's message.
    try:
        response = serv.process_message(
            request.message,
            history=history,
            last_intent=last_intent,
        )
    except ValueError as exc:
        # Provide a clear response for configuration errors, such as a missing key.
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to process your message. Please try again.",
        ) from exc

    # Save the user message after successful processing.
    session_store.add_message(
        session_id,
        "user",
        request.message,
    )

    # Persist the latest structured search intent.
    new_intent = response.get("intent")

    if hasattr(new_intent, "model_dump"):
        new_intent = new_intent.model_dump()

    session_store.update_last_intent(session_id, new_intent)

    # Save the actual assistant reply instead of always saving a search summary.
    assistant_message = response.get("reply") or ""

    session_store.add_message(
        session_id,
        "assistant",
        assistant_message,
    )

    # Return the complete response, including its type and matching files.
    return {
        "session_id": session_id,
        "message": {
            "type": response.get("type", "conversation"),
            "reply": assistant_message,
            "intent": new_intent,
            "query": response.get("query"),
            "files": response.get("files", []),
        },
    }


@router.get("/conversations")
def list_conversations():
    return {"conversations": session_store.list_sessions()}


@router.post("/conversations", status_code=201)
def create_conversation():
    session_id = str(uuid.uuid4())
    session_store.create_session(session_id)

    session = session_store.get_session(session_id)

    return {
        "id": session_id,
        "title": "New chat",
        "messages": session["messages"] if session else [],
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    session = session_store.get_session(conversation_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "id": conversation_id,
        "title": next(
            (
                message["content"][:60]
                for message in session["messages"]
                if message["role"] == "user"
            ),
            "New chat",
        ),
        "messages": session["messages"],
        "last_intent": session.get("last_intent"),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str):
    if not session_store.session_exists(conversation_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    session_store.delete_session(conversation_id)

from fastapi import APIRouter
from backend.schemas.chat import ChatRequest
from backend.services.chat_service import Chatservice
from backend.session.session_store import SessionStore
import uuid

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

    if session is None:
        session_store.create_session(session_id)

    session_store.add_message(
        session_id,
        "user",
        request.message
    )

    response = serv.process_message(
    request.message,
    history=session["messages"][:-1]
)

    session_store.add_message(
        session_id,
        "assistant",
        str(response)
    )

    return {
        "session_id": session_id,
        "message": response
    }
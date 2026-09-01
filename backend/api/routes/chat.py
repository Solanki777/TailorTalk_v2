from fastapi import APIRouter
from backend.schemas.chat import ChatRequest
from backend.services.chat_service import Chatservice

router = APIRouter()
serv = Chatservice()

@router.post("/chat")
def chat(request: ChatRequest):
    res = serv.process_message(request.message)

    return {
        "files": res
    }
    
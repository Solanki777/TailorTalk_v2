from fastapi import APIRouter
from backend.schemas.chat import ChatRequest
from backend.services.chat_service import Chatservice

router = APIRouter()

# @router.post("/chat")
# def chat(request :ChatRequest):
#     return {
#     "message" : f"you said:{request.message} "
#     }

@router.post("/chat")
def chat(request : ChatRequest):
    res = Chatservice.process_message(request.message)

    return {
        "message" : res
    }
    
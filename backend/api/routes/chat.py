from fastapi import APIRouter
from backend.schemas.chat import ChatRequest

router = APIRouter()

@router.post("/chat")
def chat(request : ChatRequest):
    return {
    "message" : f"you said: {request.message}"
    }
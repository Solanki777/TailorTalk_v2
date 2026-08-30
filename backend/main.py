from fastapi import FastAPI
from backend.services import greeting
from backend.api.routes.chat import router as chat_router
from backend.config import *

app = FastAPI(title=APP_NAME)

@app.get("/")
def home():
    return {"message":f"Welcome to {APP_NAME} 2.0"}

# @app.post("/api/v1/chat")
# def chat(request:ChatRequest):
#     return {
#         "message" : f"You said : {request.message}"
#     }

app.include_router(
    chat_router,
    prefix ="/api/v1"

)
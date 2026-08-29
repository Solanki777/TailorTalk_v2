from fastapi import FastAPI
from backend.services import greeting
from backend.schemas.chat import ChatRequest

app = FastAPI()

@app.get("/")
def home():
    return {"message":greeting.get_gretting()}

@app.post("/api/v1/chat")
def chat(request:ChatRequest):
    return {
        "message" : f"You said : {request.message}"
    }
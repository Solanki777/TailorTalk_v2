from fastapi import FastAPI
from backend.services import greeting
from backend.api.routes.chat import router as chat_router

app = FastAPI()

@app.get("/")
def home():
    return {"message":greeting.get_gretting()}

# @app.post("/api/v1/chat")
# def chat(request:ChatRequest):
#     return {
#         "message" : f"You said : {request.message}"
#     }

app.include_router(
    chat_router,
    prefix ="api/v1"

)
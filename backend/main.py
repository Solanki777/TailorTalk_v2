from fastapi import FastAPI
from backend.services import greeting
from backend.api.routes.chat import router as chat_router
from backend.config import *
from backend.api.routes.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message":f"Welcome to {APP_NAME} 2.0"}


#     }

app.include_router(
    chat_router,
    prefix ="/api/v1"

)

app.include_router(health_router)
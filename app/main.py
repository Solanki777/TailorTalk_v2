from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.routes import pages, upload

app = FastAPI(
    title="TestPilot AI",
    description="FastAPI application with a Tailwind CSS and glassmorphism interface",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount routes
app.include_router(pages.router)
app.include_router(upload.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # Make sure upload path exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)

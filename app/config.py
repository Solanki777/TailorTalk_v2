from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI Config
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # Security & Keys
    GEMINI_API_KEY: str = ""

    # Storage Config
    UPLOAD_DIR: str = "storage/uploads"
    MAX_FILE_SIZE_MB: int = 50

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        if not path.is_absolute():
            # If relative, make it relative to the workspace root directory
            path = Path(__file__).resolve().parent.parent / path
        return path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

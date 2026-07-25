import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import settings

class StorageService:
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir

    def ensure_dir(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, upload_file: UploadFile) -> dict:
        self.ensure_dir()
        
        # Standardize and secure filename
        original_name = Path(upload_file.filename).name
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        dest_path = self.upload_dir / unique_name
        
        # Read and write in chunks to minimize memory consumption
        size = 0
        with open(dest_path, "wb") as buffer:
            while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                buffer.write(chunk)
                size += len(chunk)
                
        return {
            "filename": original_name,
            "saved_name": unique_name,
            "path": str(dest_path.resolve()),
            "size": size
        }

storage_service = StorageService(settings.upload_path)

from fastapi import UploadFile
from app.config import settings

class FileValidator:
    def __init__(self, max_size_mb: int):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def validate(self, upload_file: UploadFile):
        if not upload_file.filename:
            raise ValueError("File must have a non-empty name.")

        # Check file size (if available in Starlette metadata, otherwise we'll fail gracefully or on read)
        file_size = getattr(upload_file, "size", None)
        if file_size is not None:
            if file_size <= 0:
                raise ValueError("File cannot be empty.")
            if file_size > self.max_size_bytes:
                max_mb = self.max_size_bytes / (1024 * 1024)
                raise ValueError(f"File size exceeds the limit of {max_mb:.0f} MB.")

file_validator = FileValidator(settings.MAX_FILE_SIZE_MB)

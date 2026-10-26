
from backend.services.drive_service import DriveService
from backend.services.document_cache import DocumentCache
from backend.services.document_text_service import DocumentTextService


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.presentation",
}


class DocumentContentService:
    """Retrieve document text using temporary downloads and a SQLite cache."""

    def __init__(self):
        self.drive = DriveService()
        self.cache = DocumentCache()
        self.extractor = DocumentTextService()

    def get_text(self, file_id: str) -> dict:
        # 1. Get current metadata to validate the cached version.
        metadata = self.drive.get_file_metadata(file_id)

        if metadata.get("trashed"):
            return {
                "status": "failed",
                "text": "",
                "error": "File is in the Google Drive trash.",
            }

        mime_type = metadata.get("mimeType", "")
        file_version = metadata.get("version")
        version = str(file_version) if file_version is not None else None
        modified_time = metadata.get("modifiedTime")

        # 2. Reuse cached text only when the version still matches.
        cached = self.cache.get(
            file_id=file_id,
            version=version,
            modified_time=modified_time,
        )

        if cached:
            return {
                "status": cached["extraction_status"],
                "method": cached["extraction_method"],
                "text": cached["extracted_text"],
                "cached": True,
                "file": metadata,
            }

        # 3. Reject unsupported file types before downloading.
        if mime_type not in SUPPORTED_MIME_TYPES:
            return {
                "status": "failed",
                "text": "",
                "cached": False,
                "file": metadata,
                "error": f"Unsupported file type: {mime_type}",
            }

        # 4. Download temporarily, extract, cache, and always clean up.
        temp_path = None

        try:
            temp_path = self.drive.download_to_temp(
                file_id=file_id,
                mime_type=mime_type,
            )

            result = self.extractor.extract_text(temp_path)

            self.cache.upsert(
                file_id=file_id,
                file_name=metadata.get("name", "Unknown"),
                mime_type=mime_type,
                version=version,
                modified_time=modified_time,
                extracted_text=result.get("text", ""),
                extraction_status=result.get("status", "failed"),
                extraction_method=result.get("method"),
            )

            return {
                **result,
                "cached": False,
                "file": metadata,
            }

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

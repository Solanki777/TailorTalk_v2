
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import Mock
import uuid

from backend.services.document_content_service import DocumentContentService


def run_test():
    service = DocumentContentService()
    file_id = "test-" + str(uuid.uuid4())
    temp_paths = []

    metadata = {
        "id": file_id,
        "name": "test-document.pdf",
        "mimeType": "application/pdf",
        "version": "1",
        "modifiedTime": "2026-10-26T10:00:00.000Z",
        "webViewLink": "https://drive.google.com/",
        "trashed": False,
    }

    service.drive.get_file_metadata = Mock(return_value=metadata)

    def fake_download(file_id, mime_type):
        with NamedTemporaryFile(suffix=".pdf", delete=False) as file:
            file.write(b"test PDF placeholder")
            path = Path(file.name)
        temp_paths.append(path)
        return path

    service.drive.download_to_temp = Mock(side_effect=fake_download)

    service.extractor.extract_text = Mock(return_value={
        "text": "Invoice from ABC Company. Total amount 5000.",
        "status": "success",
        "method": "embedded_pdf_text",
    })

    try:
        # First request: download, extract, and cache.
        first = service.get_text(file_id)

        assert first["status"] == "success"
        assert first["cached"] is False
        assert "ABC Company" in first["text"]
        assert temp_paths and not temp_paths[0].exists()

        # Second request: reuse the cache.
        second = service.get_text(file_id)

        assert second["cached"] is True
        assert second["text"] == first["text"]
        service.drive.download_to_temp.assert_called_once()
        service.extractor.extract_text.assert_called_once()

        print("PASS: First request extracts and caches text.")
        print("PASS: Temporary download is deleted.")
        print("PASS: Second request reuses cached text.")
        print("PASS: Second request does not download or extract again.")

    finally:
        service.cache.delete(file_id)
        for path in temp_paths:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    run_test()

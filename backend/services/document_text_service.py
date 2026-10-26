
from pathlib import Path
from threading import Lock

import easyocr
import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader


class DocumentTextService:
    """Extract embedded PDF text and OCR scanned PDFs or images."""

    OCR_LANGUAGES = ["en"]
    MIN_EMBEDDED_TEXT_CHARS = 40
    MAX_PDF_PAGES = 30
    MAX_IMAGE_PIXELS = 20_000_000
    PDF_RENDER_SCALE = 1.5

    def __init__(self):
        self._reader = None
        self._ocr_lock = Lock()

    def _get_ocr_reader(self):
        """Initialize EasyOCR only when OCR is required."""
        if self._reader is None:
            with self._ocr_lock:
                if self._reader is None:
                    self._reader = easyocr.Reader(
                        self.OCR_LANGUAGES,
                        gpu=False,
                    )
        return self._reader

    @staticmethod
    def _normalize_text(text: str) -> str:
        return "\n".join(
            line.strip()
            for line in text.splitlines()
            if line.strip()
        )

    def extract_pdf_text(self, file_path: str | Path) -> dict:
        """Extract embedded text first, then OCR pages when needed."""
        path = Path(file_path)

        try:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                return self._result(
                    "", "failed", "encrypted_pdf"
                )

            total_pages = len(reader.pages)
            page_limit = min(total_pages, self.MAX_PDF_PAGES)
            page_texts = []

            for page_number in range(page_limit):
                try:
                    text = reader.pages[page_number].extract_text() or ""
                except Exception:
                    text = ""

                page_texts.append(self._normalize_text(text))

            embedded_text = "\n\n".join(
                text for text in page_texts if text
            )

            # If the PDF contains enough embedded text, avoid OCR.
            if len(embedded_text.strip()) >= self.MIN_EMBEDDED_TEXT_CHARS:
                status = (
                    "partial"
                    if total_pages > page_limit
                    else "success"
                )
                return self._result(
                    embedded_text,
                    status,
                    "embedded_pdf_text",
                )

            # OCR only pages with little or no embedded text.
            pdf = pdfium.PdfDocument(str(path))
            ocr_page_texts = []

            try:
                for page_number in range(page_limit):
                    if len(page_texts[page_number]) >= (
                        self.MIN_EMBEDDED_TEXT_CHARS
                    ):
                        ocr_page_texts.append(page_texts[page_number])
                        continue

                    page = pdf[page_number]
                    bitmap = page.render(
                        scale=self.PDF_RENDER_SCALE
                    )
                    image = bitmap.to_pil()

                    try:
                        ocr_text = self._read_image(image)
                    finally:
                        image.close()
                        del bitmap
                        del page

                    ocr_page_texts.append(
                        self._normalize_text(ocr_text)
                    )
            finally:
                pdf.close()

            combined_text = "\n\n".join(
                text for text in ocr_page_texts if text
            )

            status = (
                "partial"
                if total_pages > page_limit
                else "success"
            )

            return self._result(
                combined_text,
                status,
                "pdf_text_and_ocr",
            )

        except Exception as exc:
            return self._result(
                "",
                "failed",
                "pdf_extraction",
                error=str(exc),
            )

    def extract_image_text(self, file_path: str | Path) -> dict:
        """Extract text from a supported image using EasyOCR."""
        path = Path(file_path)

        try:
            with Image.open(path) as source_image:
                image = source_image.convert("RGB")

            try:
                if image.width * image.height > self.MAX_IMAGE_PIXELS:
                    return self._result(
                        "", "failed", "image_too_large"
                    )

                text = self._read_image(image)
            finally:
                image.close()

            return self._result(
                self._normalize_text(text),
                "success",
                "easyocr",
            )

        except Exception as exc:
            return self._result(
                "",
                "failed",
                "image_ocr",
                error=str(exc),
            )

    def _read_image(self, image: Image.Image) -> str:
        """Run OCR and combine detected text lines."""
        with self._ocr_lock:
            results = self._get_ocr_reader().readtext(
                image,
                detail=0,
                paragraph=True,
            )

        return "\n".join(
            str(item) for item in results if str(item).strip()
        )

    @staticmethod
    def _result(
        text: str,
        status: str,
        method: str,
        error: str | None = None,
    ) -> dict:
        result = {
            "text": text,
            "status": status,
            "method": method,
        }

        if error:
            result["error"] = error

        return result

    def extract_text(self, file_path: str | Path) -> dict:
        """Choose an extraction method based on the file extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self.extract_pdf_text(path)

        if extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".tif",
            ".tiff",
            ".webp",
        }:
            return self.extract_image_text(path)

        return self._result(
            "",
            "failed",
            "unsupported_file_type",
        )

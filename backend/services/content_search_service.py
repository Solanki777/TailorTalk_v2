
import re

from backend.services.drive_service import DriveService
from backend.services.document_content_service import DocumentContentService


class ContentSearchService:
    """Search document contents and rank candidates using text evidence."""

    def __init__(self):
        self.drive = DriveService()
        self.document_content = DocumentContentService()

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    @staticmethod
    def _snippet(text: str, terms: list[str], window: int = 180) -> str:
        """Return a short excerpt around the first matching term."""
        lower_text = text.lower()
        positions = [
            lower_text.find(term.lower())
            for term in terms
            if len(term) >= 3 and lower_text.find(term.lower()) >= 0
        ]

        if not positions:
            return text[:window].strip()

        start = max(0, min(positions) - window // 3)
        end = min(len(text), start + window)
        return text[start:end].strip()

    def search(self, query: str, max_candidates: int = 100) -> dict:
        """
        Search Drive metadata first, then rank supported candidates by content.
        This initial version does not yet implement clarification or pagination.
        """
        query_terms = list(dict.fromkeys(self._tokens(query)))

        # First pass: search likely filenames using Drive metadata.
        metadata_query = "trashed = false"
        candidates = self.drive.search_files(metadata_query)

        # Avoid processing the same Drive file more than once.
        unique_candidates = []
        seen_ids = set()

        for file in candidates:
            file_id = file.get("id")
            if not file_id or file_id in seen_ids:
                continue

            seen_ids.add(file_id)
            unique_candidates.append(file)

        ranked_results = []
        errors = []

        for file in unique_candidates[:max_candidates]:
            try:
                result = self.document_content.get_text(file["id"])

                if result.get("status") not in {"success", "partial"}:
                    errors.append({
                        "file_id": file["id"],
                        "file_name": file.get("name"),
                        "error": result.get("error", "Text extraction failed"),
                    })
                    continue

                text = result.get("text", "")
                if not text.strip():
                    continue

                text_tokens = set(self._tokens(text))
                matched_terms = [
                    term for term in query_terms
                    if len(term) >= 2 and term in text_tokens
                ]

                # Simple explainable baseline: count distinct matching terms.
                score = len(matched_terms)

                if score == 0:
                    continue

                metadata = result.get("file", file)
                ranked_results.append({
                    "id": file["id"],
                    "name": metadata.get("name", file.get("name", "Unknown")),
                    "mimeType": metadata.get("mimeType", file.get("mimeType")),
                    "webViewLink": metadata.get(
                        "webViewLink", file.get("webViewLink")
                    ),
                    "score": score,
                    "matched_terms": matched_terms,
                    "snippet": self._snippet(text, matched_terms),
                    "cached": result.get("cached", False),
                })

            except Exception as exc:
                errors.append({
                    "file_id": file.get("id"),
                    "file_name": file.get("name"),
                    "error": str(exc),
                })

        ranked_results.sort(
            key=lambda item: (item["score"], item["name"].lower()),
            reverse=True,
        )

        return {
            "query": query,
            "candidate_count": len(unique_candidates[:max_candidates]),
            "result_count": len(ranked_results),
            "results": ranked_results,
            "errors": errors,
        }

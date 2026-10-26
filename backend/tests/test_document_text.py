
from pathlib import Path

from backend.services.document_text_service import DocumentTextService

service = DocumentTextService()

file_path = Path(input("Enter the full path to a PDF or image: ").strip().strip('"'))

if not file_path.is_file():
    raise SystemExit("File not found.")

result = service.extract_text(file_path)

print("\nStatus:", result["status"])
print("Method:", result["method"])

if result.get("error"):
    print("Error:", result["error"])

print("\nExtracted text:\n")
print(result["text"][:5000] or "(No text extracted)")

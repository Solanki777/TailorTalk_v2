
from backend.services.drive_service import DriveService
from backend.services.document_content_service import DocumentContentService


SUPPORTED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.presentation",
}


def main():
    drive = DriveService()
    api = drive.authenticate()

    response = api.files().list(
        q="trashed = false",
        pageSize=100,
        orderBy="modifiedTime desc",
        fields=(
            "files(id,name,mimeType,modifiedTime,webViewLink)"
        ),
    ).execute()

    files = [
        item for item in response.get("files", [])
        if item.get("mimeType") in SUPPORTED_TYPES
    ]

    if not files:
        print("No supported PDF, image, Google Doc, or Slide found.")
        return

    print("\nSupported files in your Drive:\n")
    for index, item in enumerate(files):
        print(
            f"[{index}] {item['name']} "
            f"({item.get('mimeType', 'unknown')})"
        )

    choice = input("\nEnter the number of a test file: ").strip()

    try:
        selected = files[int(choice)]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"\nProcessing: {selected['name']}")

    content_service = DocumentContentService()
    result = content_service.get_text(selected["id"])

    print("\nStatus:", result.get("status"))
    print("Method:", result.get("method"))
    print("Cache hit:", result.get("cached", False))

    if result.get("error"):
        print("Error:", result["error"])

    text = result.get("text", "")
    print("\nExtracted text preview:\n")
    print(text[:800] if text else "(No text extracted)")

    if result.get("file", {}).get("webViewLink"):
        print("\nOriginal Drive link:")
        print(result["file"]["webViewLink"])


if __name__ == "__main__":
    main()

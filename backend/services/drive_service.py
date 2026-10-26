
from pathlib import Path

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


import mimetypes
import tempfile

from googleapiclient.http import MediaIoBaseDownload



SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = BASE_DIR / "credentials" / "client_secret.json"
TOKEN_FILE = BASE_DIR / "credentials" / "token.json"


class DriveService:

    def authenticate(self):
        credentials = None

        if TOKEN_FILE.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(TOKEN_FILE),
                    SCOPES,
                )
            except (ValueError, OSError):
                credentials = None

        if credentials and not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except RefreshError:
                    credentials = None

        if not credentials or not credentials.valid:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Google OAuth credentials not found: {CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

        return build(
            "drive",
            "v3",
            credentials=credentials,
        )

    def list_files(self):
        service = self.authenticate()

        results = service.files().list(
            pageSize=10,
            fields="files(id,name,mimeType,createdTime,webViewLink)",
        ).execute()

        return results.get("files", [])

   
    
    def search_files(self, query, max_results=100):
        """Search Google Drive files across pages, up to max_results."""
        service = self.authenticate()

        all_files = []
        page_token = None

        while len(all_files) < max_results:
            page_size = min(100, max_results - len(all_files))

            results = service.files().list(
                q=query,
                pageSize=page_size,
                pageToken=page_token,
                orderBy="createdTime desc",
                fields=(
                    "nextPageToken,"
                    "files(id,name,mimeType,createdTime,webViewLink)"
                ),
            ).execute()

            all_files.extend(results.get("files", []))

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return all_files

    
    def get_file_metadata(self, file_id: str):
        """Fetch the metadata needed to validate cached document text."""
        service = self.authenticate()

        return service.files().get(
            fileId=file_id,
            fields=(
                "id,name,mimeType,version,modifiedTime,size,"
                "webViewLink,md5Checksum,trashed"
            ),
        ).execute()
    

    def download_to_temp(self, file_id: str, mime_type: str):
        """
        Download a supported Drive file into a temporary file.
        The caller must delete the returned path after extraction.
        """
        service = self.authenticate()

        google_doc_exports = {
            "application/vnd.google-apps.document": (
                "application/pdf", ".pdf"
            ),
            "application/vnd.google-apps.presentation": (
                "application/pdf", ".pdf"
            ),
            "application/vnd.google-apps.spreadsheet": (
                "text/csv", ".csv"
            ),
        }

        export_info = google_doc_exports.get(mime_type)

        if mime_type.startswith("application/vnd.google-apps.") and not export_info:
            raise ValueError(
                f"Unsupported Google Workspace file type: {mime_type}"
            )

        if export_info:
            export_mime, suffix = export_info
            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_mime,
            )
        else:
            suffix = mimetypes.guess_extension(mime_type) or ".bin"
            request = service.files().get_media(fileId=file_id)

        temp_file = tempfile.NamedTemporaryFile(
            prefix="tailortalk_",
            suffix=suffix,
            delete=False,
        )
        temp_path = Path(temp_file.name)

        try:
            with temp_file:
                downloader = MediaIoBaseDownload(temp_file, request)
                done = False

                while not done:
                    _, done = downloader.next_chunk()

            return temp_path

        except Exception:
            temp_path.unlink(missing_ok=True)
            raise



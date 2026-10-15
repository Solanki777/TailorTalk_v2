
from pathlib import Path

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


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

   
    def search_files(self, query):
        service = self.authenticate()

        results = service.files().list(
            q=query,
            pageSize=10,
            orderBy="createdTime desc",
            fields="files(id,name,mimeType,createdTime,webViewLink)",
        ).execute()

        return results.get("files", [])


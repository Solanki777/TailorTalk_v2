from pathlib import Path

from google.auth.transport.requests import Request
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
            credentials = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES,
            )

        if not credentials or not credentials.valid:

            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES,
                )

                credentials = flow.run_local_server(port=0)

            TOKEN_FILE.write_text(credentials.to_json())

        return build(
            "drive",
            "v3",
            credentials=credentials,
        )

    def list_files(self):
        service = self.authenticate()

        results = service.files().list(
            pageSize=10,
            fields="files(id, name, mimeType)",
        ).execute()

        return results.get("files", [])

    def search_files(self,query):
        service = self.authenticate()

        results = service.files().list(
            q = query,
            pageSize = 10 ,
            fields = "files(id,name,mimeType)"
        ).execute()

        return results.get("files",[])
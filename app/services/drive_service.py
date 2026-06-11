import io
from pathlib import Path
from typing import List, Dict

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import CREDENTIALS_PATH, TOKEN_PATH, SUPPORTED_EXTENSIONS
from app.db.database import Database

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveService:
    def __init__(self, db: Database):
        self.db = db
        self.service = None

    def authenticate(self) -> None:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                "Missing credentials.json. Create OAuth Desktop credentials in Google Cloud and place credentials.json in the project root."
            )

        creds = None
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        self.service = build("drive", "v3", credentials=creds)

    def list_images(self, folder_id: str, page_size: int = 50) -> List[Dict]:
        if self.service is None:
            self.authenticate()

        query = f"'{folder_id}' in parents and trashed = false"
        response = self.service.files().list(
            q=query,
            fields="files(id, name, mimeType, size)",
            pageSize=page_size,
        ).execute()

        files = response.get("files", [])
        return [
            item for item in files
            if Path(item["name"]).suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    def download_images(self, folder_id: str, cache_dir: Path, batch_size: int) -> int:
        if self.service is None:
            self.authenticate()

        cache_dir.mkdir(parents=True, exist_ok=True)
        files = self.list_images(folder_id, page_size=100)
        downloaded = 0

        for file in files:
            if downloaded >= batch_size:
                break

            drive_id = file["id"]
            name = file["name"]
            target = cache_dir / name

            if target.exists():
                continue

            request = self.service.files().get_media(fileId=drive_id)
            with io.FileIO(target, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            self.db.add_wallpaper(
                drive_file_id=drive_id,
                file_name=target.name,
                local_path=str(target),
                file_size_bytes=target.stat().st_size,
            )
            downloaded += 1

        return downloaded


import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "data" / "document_cache.db"


class DocumentCache:
    """Persist extracted document text in a local SQLite database."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS document_text_cache (
                    file_id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    mime_type TEXT,
                    version TEXT,
                    modified_time TEXT,
                    extracted_text TEXT NOT NULL DEFAULT '',
                    extraction_status TEXT NOT NULL,
                    extraction_method TEXT,
                    cached_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    )
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_document_text_cache_modified
                ON document_text_cache(modified_time)
            """)

    def get(self, file_id: str, version: str | None,
            modified_time: str | None):
        with self._connect() as connection:
            row = connection.execute("""
                SELECT * FROM document_text_cache
                WHERE file_id = ?
                  AND version IS ?
                  AND modified_time IS ?
                  AND extraction_status IN ('success', 'partial')
            """, (file_id, version, modified_time)).fetchone()

        return dict(row) if row else None

    def upsert(self, file_id: str, file_name: str, mime_type: str | None,
               version: str | None, modified_time: str | None,
               extracted_text: str, extraction_status: str,
               extraction_method: str | None):
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO document_text_cache (
                    file_id, file_name, mime_type, version,
                    modified_time, extracted_text,
                    extraction_status, extraction_method, cached_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                ON CONFLICT(file_id) DO UPDATE SET
                    file_name = excluded.file_name,
                    mime_type = excluded.mime_type,
                    version = excluded.version,
                    modified_time = excluded.modified_time,
                    extracted_text = excluded.extracted_text,
                    extraction_status = excluded.extraction_status,
                    extraction_method = excluded.extraction_method,
                    cached_at = excluded.cached_at
            """, (
                file_id, file_name, mime_type, version,
                modified_time, extracted_text,
                extraction_status, extraction_method,
            ))

    def delete(self, file_id: str):
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM document_text_cache WHERE file_id = ?",
                (file_id,),
            )

    def clear(self):
        with self._connect() as connection:
            connection.execute("DELETE FROM document_text_cache")

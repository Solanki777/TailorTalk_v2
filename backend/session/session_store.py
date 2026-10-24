
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DATABASE_PATH = DATA_DIR / "conversations.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    """Persistent SQLite storage for TailorTalk conversations."""

    def __init__(self, ttl_minutes=None):
        # ttl_minutes is retained for compatibility with older callers.
        # Conversations no longer expire automatically.
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    last_intent TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL
                        CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_messages_conversation_id
                ON messages(conversation_id, id)
                """
            )

    def create_session(self, session_id: str) -> None:
        now = _now()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations
                    (id, last_intent, created_at, updated_at)
                VALUES (?, NULL, ?, ?)
                """,
                (session_id, now, now),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            conversation = connection.execute(
                """
                SELECT id, last_intent, created_at, updated_at
                FROM conversations
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()

            if conversation is None:
                return None

            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        last_intent = (
            json.loads(conversation["last_intent"])
            if conversation["last_intent"]
            else None
        )

        return {
            "id": conversation["id"],
            "messages": [
                {"role": row["role"], "content": row["content"]}
                for row in rows
            ],
            "last_intent": last_intent,
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
        }

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Unsupported message role.")

        now = _now()

        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?",
                (session_id,),
            ).fetchone()

            if exists is None:
                connection.execute(
                    """
                    INSERT INTO conversations
                        (id, last_intent, created_at, updated_at)
                    VALUES (?, NULL, ?, ?)
                    """,
                    (session_id, now, now),
                )

            connection.execute(
                """
                INSERT INTO messages
                    (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, now),
            )

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (now, session_id),
            )

    def update_last_intent(
        self,
        session_id: str,
        intent: dict | None,
    ) -> None:
        serialized_intent = (
            json.dumps(intent, ensure_ascii=False)
            if intent is not None
            else None
        )

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET last_intent = ?, updated_at = ?
                WHERE id = ?
                """,
                (serialized_intent, _now(), session_id),
            )

    def delete_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM conversations WHERE id = ?",
                (session_id,),
            )

    def list_sessions(self):
        """Return saved conversations, newest first."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT
                    c.id,
                    c.created_at,
                    c.updated_at,
                    (
                        SELECT m.content
                        FROM messages m
                        WHERE m.conversation_id = c.id
                          AND m.role = 'user'
                        ORDER BY m.id ASC
                        LIMIT 1
                    ) AS first_message
                FROM conversations c
                ORDER BY c.updated_at DESC
            """).fetchall()

        return [
            {
                "id": row["id"],
                "title": (row["first_message"] or "New chat")[:60],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def session_exists(self, session_id: str) -> bool:
        """Check whether a conversation exists in SQLite."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM conversations WHERE id = ?",
                (session_id,),
            ).fetchone()

        return row is not None

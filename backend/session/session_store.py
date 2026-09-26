from datetime import datetime, timezone, timedelta


class SessionStore:
    def __init__(self, ttl_minutes=30):
        self.sessions = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    def create_session(self, session_id: str):
        now = datetime.now(timezone.utc)

        self.sessions[session_id] = {
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }

    def get_session(self, session_id: str):
        session = self.sessions.get(session_id)

        if session is None:
            return None

        now = datetime.now(timezone.utc)

        if now - session["updated_at"] > self.ttl:
            self.delete_session(session_id)
            return None

        return session

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)

        if session is None:
            self.create_session(session_id)
            session = self.sessions[session_id]

        session["messages"].append({
            "role": role,
            "content": content,
        })

        session["updated_at"] = datetime.now(timezone.utc)

    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)
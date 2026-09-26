from datetime import datetime, timezone


class SessionStore:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id: str):
        self.sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)

        if session is None:
            self.create_session(session_id)
            session = self.get_session(session_id)

        session["messages"].append({
            "role": role,
            "content": content,
        })

        session["updated_at"] = datetime.now(timezone.utc)

    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)
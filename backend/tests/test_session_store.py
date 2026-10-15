
from backend.session.session_store import SessionStore


def test_session_stores_last_intent():
    store = SessionStore()

    store.create_session("session-1")

    intent = {
        "name": "project",
        "file_type": "pdf",
        "owner": "me",
        "created_after": None,
        "created_before": None,
    }

    store.update_last_intent("session-1", intent)

    session = store.get_session("session-1")

    assert session["last_intent"] == intent


def test_sessions_keep_intents_separate():
    store = SessionStore()

    store.create_session("session-1")
    store.create_session("session-2")

    intent = {
        "name": "project",
        "file_type": "pdf",
    }

    store.update_last_intent("session-1", intent)

    assert store.get_session("session-1")["last_intent"] == intent
    assert store.get_session("session-2")["last_intent"] is None

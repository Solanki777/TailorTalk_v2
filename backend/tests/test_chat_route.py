
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import chat as chat_route
from backend.main import app


client = TestClient(app)


def test_chat_route_saves_and_reuses_intent():
    chat_route.session_store.sessions.clear()

    fake_response = {
        "intent": {
            "name": "project",
            "file_type": "pdf",
            "owner": "me",
            "created_after": None,
            "created_before": None,
        },
        "query": "test-query",
        "files": [],
    }

    with patch.object(
        chat_route.serv,
        "process_message",
        return_value=fake_response,
    ) as mock_process:

        first_response = client.post(
            "/api/v1/chat",
            json={"message": "Find my project PDFs"},
        )

        assert first_response.status_code == 200

        session_id = first_response.json()["session_id"]

        second_response = client.post(
            "/api/v1/chat",
            json={
                "message": "Only show recent ones",
                "session_id": session_id,
            },
        )

        assert second_response.status_code == 200

    assert mock_process.call_count == 2

    second_call = mock_process.call_args_list[1]

    assert second_call.kwargs["last_intent"] == fake_response["intent"]

    session = chat_route.session_store.get_session(session_id)

    assert session["last_intent"] == fake_response["intent"]
    assert len(session["messages"]) == 4


def test_unknown_session_gets_new_session_id():
    chat_route.session_store.sessions.clear()

    unknown_session_id = "expired-session-123"

    fake_response = {
        "intent": {
            "name": "resume",
            "file_type": "pdf",
            "owner": None,
            "created_after": None,
            "created_before": None,
        },
        "query": "test-query",
        "files": [],
    }

    with patch.object(
        chat_route.serv,
        "process_message",
        return_value=fake_response,
    ):
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Find my resumes",
                "session_id": unknown_session_id,
            },
        )

    assert response.status_code == 200

    new_session_id = response.json()["session_id"]

    assert new_session_id != unknown_session_id
    assert new_session_id in chat_route.session_store.sessions

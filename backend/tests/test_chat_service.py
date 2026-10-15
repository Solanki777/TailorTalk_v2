
from unittest.mock import Mock
from backend.services.chat_service import Chatservice


def test_process_message_trims_history():
    service = Chatservice.__new__(Chatservice)

    service.llm = Mock()
    service.query_builder = Mock()
    service.drive_service = Mock()

    service.llm.extract_search_intent.return_value = "test-intent"
    service.query_builder.build.return_value = "test-query"
    service.drive_service.search_files.return_value = []

    result = service.process_message(
        "Find my PDFs",
        history=[
            {"role": "user", "content": "Find my documents"}
        ]
    )

    service.llm.extract_search_intent.assert_called_once()
    service.query_builder.build.assert_called_once_with("test-intent")
    service.drive_service.search_files.assert_called_once_with("test-query")
    passed_history = service.llm.extract_search_intent.call_args.args[1]

    assert passed_history == [
        {"role": "user", "content": "Find my documents"}
    ]

    assert result["files"] == []

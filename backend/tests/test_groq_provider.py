
import json
from unittest.mock import Mock, patch

from backend.services.llm.groq import GroqProvider


def test_extract_search_intent_passes_conversation_history():
    provider = GroqProvider.__new__(GroqProvider)
    provider.client = Mock()

    provider.client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content=json.dumps({
                        "name": "project",
                        "file_type": "pdf",
                        "owner": "me",
                        "created_after": "2026-09-01",
                        "created_before": "2026-09-30"
                    })
                )
            )
        ]
    )

    history = [
        {"role": "user", "content": "Find my project PDFs"},
        {
            "role": "assistant",
            "content": "Searching for project PDFs."
        }
    ]

    with patch.object(
        provider.client.chat.completions,
        "create",
        wraps=provider.client.chat.completions.create
    ):
        intent = provider.extract_search_intent(
            "Only show files from September 2026",
            history
        )

    assert intent.name == "project"
    assert intent.file_type == "pdf"
    assert intent.created_after == "2026-09-01"
    assert intent.created_before == "2026-09-30"

    call_args = provider.client.chat.completions.create.call_args
    sent_messages = call_args.kwargs["messages"]

    assert sent_messages[-2] == history[-1]
    assert sent_messages[-1]["content"] == "Only show files from September 2026"

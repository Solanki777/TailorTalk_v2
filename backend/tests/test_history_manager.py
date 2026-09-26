from backend.utils.history_manager import trim_history


def test_trim_history_keeps_small_history():
    messages = [
        {"role": "user", "content": "Find my PDFs"},
        {"role": "assistant", "content": "Here are your PDFs"},
    ]

    result = trim_history(messages)

    assert result == messages
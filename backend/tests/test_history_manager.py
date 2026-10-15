from backend.utils.history_manager import trim_history


def test_trim_history_keeps_small_history():
    messages = [
        {"role": "user", "content": "Find my PDFs"},
        {"role": "assistant", "content": "Here are your PDFs"},
    ]

    result = trim_history(messages)

    assert result == messages

def test_trim_history_removes_old_messages(monkeypatch):
    import backend.utils.history_manager as history_manager

    monkeypatch.setattr(history_manager, "MAX_HISTORY_TOKENS", 100)

    messages = [
        {"role": "user", "content": "old message " * 100},
        {"role": "assistant", "content": "old response " * 100},
        {"role": "user", "content": "Find recent PDFs"},
        {"role": "assistant", "content": "Here are recent PDFs"},
    ]

    result = history_manager.trim_history(messages)

    assert len(result) < len(messages)
    assert result[-1] == messages[-1]
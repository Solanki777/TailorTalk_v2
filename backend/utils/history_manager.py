from backend.utils.token_counter import count_tokens
from backend.config import MAX_HISTORY_TOKENS


def trim_history(messages):
    history = messages.copy()

    while history and count_tokens(history) > MAX_HISTORY_TOKENS:
        # Remove the oldest user-assistant exchange
        if len(history) >= 2:
            history = history[2:]
        else:
            history.pop(0)

    return history
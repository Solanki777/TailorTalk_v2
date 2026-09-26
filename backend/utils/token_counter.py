import tiktoken


def count_tokens(messages):
    encoding = tiktoken.get_encoding("cl100k_base")

    total_tokens = 0

    for message in messages:
        total_tokens += 4

        for value in message.values():
            if isinstance(value, str):
                total_tokens += len(encoding.encode(value))

    return total_tokens
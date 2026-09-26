import json

from groq import Groq

from backend.config import GROQ_API_KEY
from backend.schemas.search import SearchIntent
from backend.services.llm.base import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def extract_search_intent(
    self,
    message: str,
    history: list = None
) -> SearchIntent:

        history = history or []

        system_prompt = """
        You are a Google Drive search intent extractor.

        Convert the user's latest message into a complete search intent.

        Use the conversation history to understand follow-up requests.
        Preserve previous search filters unless the user changes or removes them.

        Return only valid JSON with these fields:
        - name
        - file_type
        - owner
        - created_after
        - created_before

        Use null when a field is not specified.
        Dates must use YYYY-MM-DD format.
        """

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        messages.extend(history)

        messages.append({
            "role": "user",
            "content": message
        })

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return SearchIntent(**data)
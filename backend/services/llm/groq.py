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

Rules:
1. Use conversation history to understand follow-up requests.
2. Preserve previous search filters unless the user changes or removes them.
3. Apply new filters requested in the latest message.
4. If the user explicitly removes a filter, set that field to null.
5. Do not invent filters that are not supported by the conversation.
6. Return only valid JSON with exactly these fields:
   - name
   - file_type
   - owner
   - created_after
   - created_before
7. Use null when a field is not applicable.
8. Dates must use YYYY-MM-DD format.
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

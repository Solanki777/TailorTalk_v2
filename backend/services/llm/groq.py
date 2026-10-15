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
    history: list = None,
    last_intent: dict = None
) -> SearchIntent:
        
        history = history or []
        last_intent = last_intent or {}

        system_prompt = """

You are a Google Drive search intent extractor.

Convert the user's latest message into a complete search intent.

Rules:
1. Use conversation history and the previous structured search intent
   to understand follow-up requests.
2. If the user modifies the current search, preserve existing filters
   that still apply and apply the requested changes.
3. If the user starts a different search, replace filters that do not
   apply to the new request.
4. Do not carry over old name, file type, or date filters into a new,
   unrelated search unless the user explicitly refers to them.
5. If the user explicitly removes a filter, set that field to null.
6. Do not invent filters that are not supported by the conversation.
7. Always return the complete intent for the current search.
8. Return only valid JSON with exactly these fields:
   - name
   - file_type
   - owner
   - created_after
   - created_before
9. Use null when a field is not applicable.
10. Dates must use YYYY-MM-DD format.
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

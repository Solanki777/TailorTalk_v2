
import json

from groq import Groq

from backend.services.api_key_service import get_api_key

from backend.schemas.search import SearchIntent
from backend.services.llm.base import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(self):
        self.client = self._create_client()

    def _create_client(self):
        api_key = get_api_key("groq")

        if not api_key:
            raise ValueError(
                "Groq API key is missing. Please add it in TailorTalk Settings."
            )

        return Groq(api_key=api_key)

    
    def classify_message(self, message: str, history: list = None) -> dict:
        
        """Determine whether the user wants a Google Drive search."""
        history = history or []

        system_prompt = """
You classify messages for TailorTalk, a Google Drive assistant.

Return only valid JSON with one field:
{"is_search": true} or {"is_search": false}

Set is_search to true when:
- The user asks to find, search, locate, list, or retrieve files in Google Drive.
- The user asks a follow-up about previously searched files, such as
  changing file types, dates, names, or filters.
- The user clearly refers to files or documents from a previous search.

Set is_search to false for:
- Greetings and casual conversation.
- General questions about TailorTalk or its capabilities.
- Questions that do not require searching Google Drive.

When ambiguous, set is_search to false.
Use conversation history to understand follow-up messages.
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return {"is_search": bool(data.get("is_search", False))}





    def chat(self, message: str, history: list = None) -> str:
        """Generate a natural response for ordinary conversation."""
        history = history or []

        messages = [
            {
                "role": "system",
                "content": (
                    "You are TailorTalk, a friendly Google Drive assistant. "
                    "Reply naturally and concisely to greetings, general "
                    "conversation, and questions about your capabilities. "
                    "You can help users search their connected Google Drive. "
                    "Do not claim that you searched files or accessed "
                    "documents unless a search was actually performed. "
                    "If the user asks to find or locate files, explain that "
                    "you can help search their Google Drive."
                ),
            }
        ]

        messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
        )

        return response.choices[0].message.content or ""

    def extract_search_intent(
        self,
        message: str,
        history: list = None,
        last_intent: dict = None,
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

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        context = (
            "\nPrevious search intent:\n"
            + json.dumps(last_intent, ensure_ascii=False)
            if last_intent
            else ""
        )

        messages.append({
            "role": "user",
            "content": message + context,
        })

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return SearchIntent(**data)

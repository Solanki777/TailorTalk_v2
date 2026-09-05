import json

from groq import Groq

from backend.config import GROQ_API_KEY
from backend.schemas.search import SearchIntent
from backend.services.llm.base import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def extract_search_intent(self, message: str) -> SearchIntent:

        prompt = f"""
You are a Google Drive search intent extractor.

Convert the user's request into JSON.

The JSON must contain these fields:

- name
- file_type
- owner
- created_after
- created_before

Use null when a field is not mentioned.

User request:
{message}
"""

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            }
        )

        content = response.choices[0].message.content

        data = json.loads(content)

        return SearchIntent(**data)
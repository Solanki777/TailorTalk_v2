from backend.services.llm.base import LLMProvider


class GroqProvider(LLMProvider):

    def generate(self, prompt: str):
        return f"Groq received: {prompt}"
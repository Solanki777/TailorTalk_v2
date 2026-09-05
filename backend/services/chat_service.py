from backend.services.llm.groq import GroqProvider


class Chatservice:

    def __init__(self):
        self.llm = GroqProvider()

    def process_message(self, message):

        intent = self.llm.extract_search_intent(message)

        return {
            "intent": intent
        }
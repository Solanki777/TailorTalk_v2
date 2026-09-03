from backend.services.llm.groq import GroqProvider


class Chatservice:

    def __init__(self):
        self.llm = GroqProvider()

    def process_message(self, message):

        response = self.llm.generate(message)

        return {
            "response": response
        }
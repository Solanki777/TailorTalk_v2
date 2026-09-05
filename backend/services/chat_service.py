from backend.services.llm.groq import GroqProvider
from backend.services.query_builder import QueryBuilder
from backend.services.drive_service import DriveService


class Chatservice:

    def __init__(self):
        self.llm = GroqProvider()
        self.query_builder = QueryBuilder()
        self.drive_service = DriveService()

    def process_message(self, message):

        intent = self.llm.extract_search_intent(message)

        query = self.query_builder.build(intent)

        files = self.drive_service.search_files(query)

        return {
            "intent": intent,
            "query": query,
            "files": files
        }
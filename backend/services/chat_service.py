from backend.schemas.search import SearchIntent
from backend.services.query_builder import QueryBuilder


class Chatservice:

    def __init__(self):
        self.query_builder = QueryBuilder()

    def process_message(self, message):

        intent = SearchIntent(
            name="project",
            file_type="pdf"
        )

        query = self.query_builder.build(intent)

        return {
            "intent": intent,
            "query": query
        }
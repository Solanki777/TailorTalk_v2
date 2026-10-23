
from backend.services.llm.groq import GroqProvider
from backend.services.query_builder import QueryBuilder
from backend.services.drive_service import DriveService
from backend.utils.history_manager import trim_history


class Chatservice:

    def __init__(self):
        self.llm = GroqProvider()
        self.query_builder = QueryBuilder()
        self.drive_service = DriveService()

    def process_message(self, message, history=None, last_intent=None):
        history = trim_history(history or [])

        # Decide whether this message is asking to search Google Drive.
        search_decision = self.llm.classify_message(message, history)

        if not search_decision["is_search"]:
            reply = self.llm.chat(message, history)

            return {
                "type": "conversation",
                "reply": reply,
                "intent": last_intent,
                "query": None,
                "files": [],
            }

        intent = self.llm.extract_search_intent(
            message,
            history,
            last_intent,
        )

        query = self.query_builder.build(intent)
        files = self.drive_service.search_files(query)

        return {
            "type": "search",
            "reply": (
                f"I found {len(files)} matching file(s)."
                if files
                else "I couldn't find any matching files in your Google Drive."
            ),
            "intent": intent,
            "query": query,
            "files": files,
        }

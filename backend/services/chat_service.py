from backend.services.drive_service import DriveService
from backend.schemas.search import SearchIntent


class Chatservice:

    def __init__(self):
        self.drive_service = DriveService()

    def process_message(self, message):

        intent = SearchIntent(
            name="project",
            file_type="pdf"
        )

        return intent
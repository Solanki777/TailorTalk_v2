from backend.services.drive_service import DriveService


class Chatservice:

    def __init__(self):
        self.drive_service = DriveService()

    # def process_message(self, message):
    #     files = self.drive_service.list_files()

    #     return files
    def process_message(self, message):
        files = self.drive_service.search_files(
            "mimeType = 'application/pdf'"
        )

        return files
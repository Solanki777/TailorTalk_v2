from datetime import date, datetime, time, timedelta

from backend.schemas.search import SearchIntent


class QueryBuilder:

    def build(self, intent: SearchIntent):
        conditions = ["trashed = false"]

        if intent.name:
            name = intent.name.replace("\\", "\\\\").replace("'", "\\'")
            conditions.append(f"name contains '{name}'")

        if intent.file_type == "pdf":
            conditions.append("mimeType = 'application/pdf'")

        elif intent.file_type == "doc":
            conditions.append(
                "mimeType = 'application/vnd.google-apps.document'"
            )

        elif intent.file_type == "spreadsheet":
            conditions.append(
                "mimeType = 'application/vnd.google-apps.spreadsheet'"
            )

        elif intent.file_type == "presentation":
            conditions.append(
                "mimeType = 'application/vnd.google-apps.presentation'"
            )

        if intent.owner == "me":
            conditions.append("'me' in owners")

        if intent.created_after:
            start_date = date.fromisoformat(intent.created_after)
            start = datetime.combine(start_date, time.min)
            conditions.append(
                f"createdTime >= '{start.isoformat()}Z'"
            )

        if intent.created_before:
            end_date = date.fromisoformat(intent.created_before)
            next_day = end_date + timedelta(days=1)
            end = datetime.combine(next_day, time.min)
            conditions.append(
                f"createdTime < '{end.isoformat()}Z'"
            )

        return " and ".join(conditions)
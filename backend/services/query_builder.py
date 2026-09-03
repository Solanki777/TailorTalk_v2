from backend.schemas.search import SearchIntent


class QueryBuilder:

    def build(self, intent: SearchIntent):

        conditions = []

        if intent.name:
            conditions.append(
                f"name contains '{intent.name}'"
            )

        if intent.file_type == "pdf":
            conditions.append(
                "mimeType = 'application/pdf'"
            )

        return " and ".join(conditions)
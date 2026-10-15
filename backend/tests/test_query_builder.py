
from backend.schemas.search import SearchIntent
from backend.services.query_builder import QueryBuilder


def test_pdf_filter():
    intent = SearchIntent(file_type="pdf")

    query = QueryBuilder().build(intent)

    assert "mimeType = 'application/pdf'" in query


def test_excel_filter_includes_google_sheets_and_excel_formats():
    intent = SearchIntent(file_type="excel")

    query = QueryBuilder().build(intent)

    assert "application/vnd.google-apps.spreadsheet" in query
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in query
    )
    assert "application/vnd.ms-excel" in query


def test_date_filters_can_be_combined_with_excel_filter():
    intent = SearchIntent(
        file_type="excel",
        created_after="2026-09-01",
        created_before="2026-09-30",
    )

    query = QueryBuilder().build(intent)

    assert "application/vnd.google-apps.spreadsheet" in query
    assert "createdTime >= '2026-09-01T00:00:00Z'" in query
    assert "createdTime < '2026-10-01T00:00:00Z'" in query


def test_unfiltered_search_excludes_trashed_files():
    intent = SearchIntent()

    query = QueryBuilder().build(intent)

    assert query == "trashed = false"

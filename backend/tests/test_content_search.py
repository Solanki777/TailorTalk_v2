
from backend.services.content_search_service import ContentSearchService


def main():
    searcher = ContentSearchService()

    query = input(
        "What content do you want to find in Google Drive? "
    ).strip()

    if not query:
        print("Please enter a search query.")
        return

    print("\nSearching document content...")
    result = searcher.search(query, max_candidates=100)

    print("\nCandidates checked:", result["candidate_count"])
    print("Matching documents:", result["result_count"])

    for index, file in enumerate(result["results"], start=1):
        print(f"\n{index}. {file['name']}")
        print("   Score:", file["score"])
        print("   Matched terms:", ", ".join(file["matched_terms"]))
        print("   Cached:", file["cached"])
        print("   Evidence:", file["snippet"])
        print("   Drive link:", file.get("webViewLink") or "(not available)")

    if not result["results"]:
        print("\nNo content matches found in the candidates checked.")

    if result["errors"]:
        print("\nFiles that could not be processed:")
        for error in result["errors"]:
            print(f"- {error['file_name']}: {error['error']}")


if __name__ == "__main__":
    main()

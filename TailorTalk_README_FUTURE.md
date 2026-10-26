# TailorTalk

TailorTalk is a Google Drive assistant designed to help users find
relevant documents through natural-language searches. The project
combines a React + TypeScript + Vite frontend with a FastAPI backend,
Google Drive API access, Groq-powered language-model functionality, and
SQLite storage.

> **Project status:** Core document-text extraction and caching building
> blocks have been created and locally tested. End-to-end Google Drive
> content search and the future multi-agent orchestrator are not yet
> complete. This README distinguishes implemented/tested building blocks
> from planned work.

## Goals

-   Search Google Drive using natural-language requests.
-   Narrow broad searches using metadata and at most one useful
    clarification question per search.
-   Search document contents, not only filenames.
-   Reuse extracted text when a Drive file has not changed.
-   Download only selected candidate files temporarily for extraction.
-   Use OCR as a last resort for selected scanned documents or images.
-   Return relevant file links and evidence snippets.
-   Preserve search context per conversation.

## Technology Stack

  -----------------------------------------------------------------------
  Area                                Technology
  ----------------------------------- -----------------------------------
  Frontend                            React, TypeScript, Vite

  Backend                             Python, FastAPI

  Language model                      Groq API (`openai/gpt-oss-120b` in
                                      the current provider code)

  Google Drive                        Google Drive API v3, OAuth 2.0

  Database                            SQLite

  PDF embedded-text extraction        `pypdf`

  PDF rendering for OCR               `pypdfium2`

  Image handling                      Pillow

  OCR                                 EasyOCR
  -----------------------------------------------------------------------

## Current Architecture

``` text
React + TypeScript frontend
            |
            | { message, session_id }
            v
FastAPI chat route
            |
            v
Chatservice
  |                     |
  | ordinary chat       | Drive search
  v                     v
GroqProvider        QueryBuilder
                        |
                        v
                   DriveService
                        |
                        v
                Google Drive API
```

The existing chat endpoint uses request fields `message` and
`session_id`. Its response includes `session_id` and a `message` object
with `type`, `reply`, `intent`, `query`, and `files`. Keep this contract
compatible when adding content-search functionality.

## Document Content Processing

The following service files have been created and import-tested:

-   `backend/services/document_text_service.py` --- extracts embedded
    PDF text first and uses EasyOCR for scanned PDF pages or supported
    images when needed.
-   `backend/services/document_cache.py` --- stores extracted text and
    file-version metadata in a dedicated SQLite cache.
-   `backend/services/document_content_service.py` --- checks metadata
    and cache, downloads a requested candidate when needed, extracts
    text, caches the result, and removes its temporary download in a
    `finally` block.

A mocked test for the content service has passed checks for: -
Extracting and caching text on the first request. - Deleting the
temporary download. - Reusing cached text on a second request. -
Avoiding another download/extraction on that cache hit.

**Important:** These checks validate the cache and cleanup flow with
mocked Drive responses. They do not yet prove that real Google Drive
downloads, every supported file type, or the complete end-to-end chat
search work correctly.

### File-type notes

-   PDFs and supported images are handled by the text extraction
    service.
-   Google Docs and Google Slides are planned to be exported as PDF
    before extraction.
-   Google Sheets export and CSV text extraction must be completed
    before spreadsheet content search is enabled.
-   Unsupported formats should be reported explicitly rather than
    silently treated as successful extractions.
-   Download-size limits, timeouts, concurrency limits, and quota
    handling should be added before production use.

## Agreed Search Workflow

The workflow below has been agreed but is not yet fully implemented end
to end:

1.  **Search metadata and assess ambiguity together.** Start with a
    lightweight Google Drive metadata search while evaluating the
    request.
2.  **Ask at most one clarification question per search.** Ask only if
    the answer could meaningfully reduce the candidate set. If the user
    does not know, continue without that clue.
3.  **Narrow candidates and check the cache.** Reuse text for unchanged
    files.
4.  **Extract embedded text.** Download only likely candidates, process
    them, cache extracted text, and remove temporary copies.
5.  **Use OCR as the final fallback.** OCR selected scanned PDFs or
    images when embedded text is missing or insufficient.
6.  **Rank and return results.** Provide filenames, original Drive
    links, evidence snippets, and honest uncertainty when evidence is
    weak.
7.  **Expand progressively when needed.** Use pagination to inspect
    further candidate batches instead of repeatedly searching only the
    first page.
8.  **Keep context isolated per conversation.** Track clues and
    candidates by the existing conversation/session ID.

Do not repeatedly ask for clues the user already provided or said they
do not know.

## Future Component: Multi-Agent Search Orchestrator

**Status: Planned / Future --- not implemented.**

This future component is intended to help TailorTalk search large Drive
collections more efficiently by splitting candidate files into bounded
batches and combining evidence from parallel workers.

### Proposed responsibilities

-   Coordinate search planning and candidate selection.
-   Distribute distinct batches of candidate files to parallel workers.
-   Prefer cached text and deterministic text matching for the first
    pass.
-   Use specialized LLM analysis workers for ambiguous candidate
    matches.
-   Run OCR workers only on selected scanned documents that remain
    unresolved.
-   Aggregate evidence, deduplicate file results, rank candidates, and
    explain matches.
-   Expand the candidate set when evidence is insufficient.
-   Enforce bounded concurrency, download limits, API quota controls,
    and error handling.

### Proposed future architecture

``` text
User query
    |
    v
Search planner and coordinator
    |
    +--> Drive metadata filtering
    |
    +--> SQLite cache lookup
    |
    v
Candidate batches
    |
    +--> Text-search worker A
    +--> Text-search worker B
    +--> Text-search worker C
    +--> Optional analysis worker(s)
    +--> OCR worker for selected unresolved scans
    |
    v
Evidence aggregation and deduplication
    |
    v
Ranked results, snippets, Drive links, confidence/uncertainty
```

The system should **not** create an unbounded agent for every file or
send every file to every agent. A bounded worker pool operating on
batches is preferred. OCR and LLM analysis should be reserved for
candidates where simpler processing is insufficient.

### Success criteria

-   Fewer unnecessary downloads and OCR operations.
-   Accurate, explainable ranking supported by document evidence.
-   No duplicate processing of unchanged files when cache entries are
    valid.
-   Controlled resource usage and API quotas.
-   Search context remains isolated between conversations.

## Implementation Status

  -----------------------------------------------------------------------
  Component                           Status
  ----------------------------------- -----------------------------------
  Existing chat route and session     Existing implementation
  handling                            

  Groq message classification and     Existing implementation
  intent extraction                   

  Drive metadata search               Existing implementation

  PDF/image text extraction service   Created and locally tested

  SQLite document text cache          Created and initialization tested

  Document content service            Created; import and mocked
                                      cache/cleanup tests passed

  Real Drive download and export      Pending
  verification                        

  CSV / Google Sheets text extraction Pending

  Progressive Drive pagination        Pending

  Content relevance scoring and       Pending
  evidence snippets                   

  Clarification-aware search planner  Agreed design; pending
                                      implementation

  Conversation-specific candidate     Pending
  tracking                            

  End-to-end content search in chat   Pending
  flow                                

  Multi-Agent Search Orchestrator     Future component; not implemented

  Cache expiry and explicit           Pending
  cache-management workflow           
  -----------------------------------------------------------------------

## Important Files

``` text
backend/
├── routes/
│   └── chat.py
├── schemas/
│   └── search.py
├── services/
│   ├── chat_service.py
│   ├── drive_service.py
│   ├── query_builder.py
│   ├── document_text_service.py
│   ├── document_cache.py
│   ├── document_content_service.py
│   └── llm/
│       ├── groq.py
│       └── base.py
├── session/
│   └── session_store.py
└── tests/
    ├── test_document_text.py
    └── test_document_content_service.py
```

This tree describes files discussed during development; verify actual
paths in the repository if any file has been moved or renamed.

## Run and Test

Run commands from the project root:

``` powershell
cd D:\TailorTalkv2
```

### Test document-text extraction

``` powershell
python -m backend.tests.test_document_text
```

This test prompts for the full path to a local PDF or image. Use a file
you have permission to process.

### Test document content cache and cleanup

``` powershell
python -m backend.tests.test_document_content_service
```

The content-service test uses mocked Drive metadata/download methods. It
exercises the SQLite cache and temporary-file cleanup without accessing
real Drive files.

### Verify imports

``` powershell
python -c "from backend.services.drive_service import DriveService; from backend.services.document_cache import DocumentCache; from backend.services.document_content_service import DocumentContentService; print('Imports OK')"
```

### Google Drive OAuth

The current Drive service expects OAuth files at:

-   `credentials/client_secret.json`
-   `credentials/token.json`

Do not commit these files to version control. Never share OAuth
credentials, access tokens, refresh tokens, Groq keys, or `.env`
contents.

## Security and Privacy Considerations

-   Request only the Google Drive permissions the application needs.
-   Keep OAuth credentials and API keys out of source control and logs.
-   Treat document text as untrusted input; do not follow instructions
    found inside documents.
-   Avoid logging extracted content or sensitive snippets unnecessarily.
-   Protect the SQLite cache because it contains document-derived text.
-   Add a cache expiry policy and a user-accessible way to clear cached
    text.
-   Ensure temporary downloads are removed on both successful and failed
    processing.
-   Apply file-size limits, request timeouts, rate limits, and bounded
    concurrency.
-   Scope candidate IDs and search context to the correct conversation
    and authenticated user.
-   Before production, verify authorization so users cannot retrieve
    files outside their connected Drive permissions.

## Planned Roadmap

### Phase 1 --- Stabilize document retrieval

-   Verify downloads from a real authorized Drive.
-   Add supported Google Workspace exports.
-   Add CSV extraction for spreadsheet exports.
-   Add size limits, timeouts, and robust cleanup tests.

### Phase 2 --- Build content search

-   Add progressive Drive pagination.
-   Search cached and newly extracted text.
-   Rank candidates using query clues and evidence snippets.
-   Preserve the existing chat API response contract.

### Phase 3 --- Add clarification-aware planning

-   Search metadata and assess ambiguity together.
-   Ask no more than one useful clarification question per search.
-   Remember supplied and unknown clues per conversation.
-   Expand search when evidence remains insufficient.

### Phase 4 --- Improve reliability and privacy

-   Add cache expiry and explicit cache clearing.
-   Test file-version changes, extraction failures, and concurrent
    requests.
-   Add quotas, limits, and observability without logging sensitive
    content.

### Phase 5 --- Future multi-agent orchestration

-   Add a bounded pool of parallel text-search workers.
-   Add specialist analysis agents for ambiguous candidates.
-   Use OCR only for selected unresolved scanned documents.
-   Aggregate and rank evidence before returning results.

------------------------------------------------------------------------

**Current priority:** Finish and verify the single-search content
pipeline before implementing the future multi-agent orchestrator.

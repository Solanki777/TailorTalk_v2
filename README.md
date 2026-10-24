# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
# TailorTalk

### Conversational Google Drive Search with Progressive OCR

TailorTalk is an AI-powered assistant designed to help users find Google
Drive documents through natural language. It combines conversational
search, deterministic filtering, document text extraction, and
session-scoped search memory.

> **Implementation status:** Progressive OCR search and session OCR
> memory are the planned implementation direction. Do not treat them as
> complete until they are implemented and tested in the repository.

## Overview

Traditional file search often requires users to remember exact filenames
or folder locations. TailorTalk lets users describe what they remember
and refine their search naturally.

Example: 1. User: "Find the document that mentions my internship
stipend." 2. TailorTalk searches filenames and metadata, then checks
text in likely candidate documents. 3. User: "It was from the company
that offered me the internship." 4. TailorTalk reuses the current
conversation's search context and narrows the candidates. 5. TailorTalk
returns relevant documents with supporting snippets and links when
available.

The assistant should ask a clarifying question only when it would
materially improve an ambiguous search.

## Features

### Existing project capabilities

-   Conversational Google Drive search.
-   Groq-powered intent extraction.
-   Deterministic query building and validated filters.
-   Follow-up refinement using conversational context.
-   Ranking and deduplication of results where supported by the existing
    pipeline.
-   Clarifying questions for ambiguous requests.

### Planned progressive OCR capabilities

-   Extract embedded PDF text before using OCR.
-   Use a free local OCR engine for scanned PDFs and images.
-   Extract useful entities and clues such as organizations, dates,
    amounts, and names.
-   Store candidate file IDs, clues, and match evidence in the current
    conversation's search context.
-   Narrow candidates on follow-up messages; expand the search when no
    credible match is found.
-   Cache extracted text by document ID and version so unchanged
    documents are not processed repeatedly.
-   Return evidence snippets and links where available.

## Intended Search Flow

``` mermaid
flowchart TD
    A[User message] --> B[Load conversation search context]
    B --> C{Request clear?}
    C -- No --> D[Ask focused clarification]
    D --> E[Update search clues]
    C -- Yes --> E
    E --> F{Existing candidates?}
    F -- Yes --> G[Filter cached candidates first]
    F -- No --> H[Search Drive metadata and filenames]
    H --> I[Rank likely candidates]
    G --> J[Read cached extracted text]
    I --> K[Extract text from likely candidates]
    K --> L{Embedded text available?}
    L -- Yes --> M[Use embedded text]
    L -- No --> N[Run local OCR]
    M --> O[Extract entities and match evidence]
    N --> O
    J --> O
    O --> P[Rank and return documents]
    P --> Q[Save updated session context]
    Q --> R[User follow-up]
    R --> B
```

### Efficiency rules

1.  Search filenames and metadata before processing document contents.
2.  Reuse cached text for unchanged documents.
3.  Run OCR only when embedded text is missing or insufficient.
4.  Narrow the current candidate set first for relevant follow-up
    messages.
5.  Expand the search when the current candidate set has no credible
    match.
6.  Keep search context isolated by conversation.
7.  Send only relevant snippets to the LLM, not entire document
    collections.

## Architecture

The current project direction uses React + TypeScript + Vite for the
frontend, FastAPI for the backend, SQLite for local persistence, Groq
for language understanding, and Google Drive for file discovery.

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React, TypeScript, Vite Chat interface and
                                                  results

  API                     FastAPI                 Chat endpoint and
                                                  backend coordination

  Language understanding  Groq                    Interpret requests and
                                                  generate responses

  Cloud files             Google Drive API        Search files and
                                                  retrieve
                                                  metadata/content

  Persistence             SQLite                  Conversation data and
                                                  potential OCR/search
                                                  cache

  PDF extraction          PyMuPDF                 Extract embedded PDF
                          (optional/planned)      text

  Local OCR               PaddleOCR or another    Extract text from
                          selected open-source    scanned pages and
                          engine                  images

  Entity extraction       Rules or a selected NLP Identify entities and
                          library                 useful clues
  -----------------------------------------------------------------------

The current installed dependencies and modules must be checked before
adding or replacing an OCR engine. The project's Settings UI has
previously mentioned PaddleOCR; verify whether it is already installed
and wired into the backend.

## Project Structure

This is a logical guide, not a guarantee that every listed module
already exists. Integrate with existing equivalent modules instead of
creating duplicates.

``` text
TailorTalkv2/
├── backend/
│   ├── api/routes/chat.py
│   ├── services/
│   │   ├── document_search.py       # Existing or planned search service
│   │   ├── document_text.py         # Planned text extraction/OCR
│   │   └── search_context.py        # Planned per-conversation context
│   └── data/conversations.db        # If configured here
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       └── ...
├── requirements.txt
└── README.md
```

## Setup

### 1. Open the repository

``` powershell
cd D:\TailorTalkv2
```

### 2. Create a Python virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If dependencies are managed by a backend-specific requirements file,
install from that file instead.

### 3. Configure environment variables

Create or update the `.env` file in the location expected by the backend
configuration. For example:

``` env
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=your_supported_model_name
```

Use the model name expected by your installed Groq integration. Never
commit `.env`, API keys, Google tokens, or other credentials.

### 4. Configure Google Drive access

Use the authentication method already implemented in the repository. If
it uses Google Application Default Credentials, enable the Drive API in
the relevant Google Cloud project and authenticate:

``` bash
gcloud auth application-default login
```

### 5. Start the backend

For a FastAPI app exposed as `app` in `backend/main.py`, the command may
be:

``` powershell
uvicorn backend.main:app --reload --port 8000
```

Confirm the actual entry point in your checkout before running this
command.

### 6. Start the frontend

Open a second terminal:

``` powershell
cd frontend
npm install
npm run dev
```

Use the scripts defined in `frontend/package.json` if they differ.

## API Notes

The existing frontend integration uses a chat endpoint similar to:

``` http
POST /api/v1/chat
Content-Type: application/json
```

Example request:

``` json
{
  "message": "Find the document that mentions my stipend",
  "session_id": "your-conversation-id"
}
```

Keep the actual request/response contract compatible with the current
frontend. Verify the API prefix and schema from the running FastAPI
application or its OpenAPI page before relying on this example.

## Session Memory and OCR Cache

### Conversation search context

Recommended per-conversation state: - Current search intent and
user-provided clues. - Candidate document IDs and ranking information. -
Relevant entities and keywords. - Evidence snippets supporting candidate
matches. - Whether the search was narrowed or broadened. - Document IDs
and versions referenced by cached text.

A follow-up such as "only the one from my internship company" should
reuse the previous candidates and add the new clue rather than restart
an unrelated full search.

### Persistent OCR cache

Cache extracted text by stable document ID plus a version signal, such
as Drive file ID and modification time or checksum. Refresh the cached
text when the document changes.

Keep these concepts separate: - **Session context:** temporary search
state for one conversation. - **Persistent cache:** reusable extracted
text that may serve multiple searches subject to access controls.

Respect Drive permissions and do not expose cached text to users who
cannot access the original document.

## Testing Checklist

-   [ ] Existing filename and metadata search still works.
-   [ ] Text-based PDFs are searched without OCR when embedded text is
    available.
-   [ ] Scanned PDFs invoke local OCR when required.
-   [ ] Supported images can be OCR-processed.
-   [ ] Repeated searches reuse cached extraction output.
-   [ ] Changed documents refresh their cache.
-   [ ] Follow-ups narrow the active candidate set.
-   [ ] Zero-match searches can expand the search.
-   [ ] Context from one conversation does not leak into another.
-   [ ] Results include evidence snippets and links when available.
-   [ ] Missing OCR dependencies produce a clear, graceful error.
-   [ ] The existing chat API and frontend still work.

## Troubleshooting

  -----------------------------------------------------------------------
  Problem                             What to check
  ----------------------------------- -----------------------------------
  Backend cannot start                Virtual environment, dependencies,
                                      environment variables, and actual
                                      FastAPI entry point

  Groq authentication error           Confirm the key is configured where
                                      backend settings expect it

  Google Drive authorization error    Check account permissions and Drive
                                      API configuration

  No text found in a PDF              Check whether it has embedded text
                                      or scanned page images

  OCR runs repeatedly                 Cache using document ID and version

  Follow-up loses earlier clues       Verify context is loaded and saved
                                      using the same session ID

  Incorrect document ranking          Inspect evidence snippets, entity
                                      extraction, and ranking signals
  -----------------------------------------------------------------------

## Security and Privacy

-   Keep API keys and credentials on the backend.
-   Never commit `.env`, token files, or private credentials.
-   Apply Drive access controls to search results and cached text.
-   Isolate search context by conversation.
-   Send only relevant document snippets to the LLM.
-   Treat OCR text as untrusted document content, not instructions to
    the assistant.

## License

The original README refers to MIT. Verify that the repository contains a
matching `LICENSE` file before publishing that license claim.

# TestPilot AI

TestPilot AI is an AI-powered test analysis platform with a FastAPI backend, a
custom Tailwind CSS frontend, and a glassmorphism interface. Files uploaded
through the UI are turned into isolated **workspaces** that move through a
four-stage pipeline — parse, rule engine, AI analysis, report.

```
Upload → Parse → Rule Engine (default or your own rules) → AI Analysis → Report
```

The Rule Engine stage runs a built-in, predefined set of structural checks by
default. If you'd rather run your **own** test rules, you can supply a custom
rules JSON (pasted directly or uploaded as a file) and it's used instead —
see [Custom Rules](#custom-rules-bring-your-own-test-cases) below.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Storage Model](#storage-model)
- [Custom Rules (Bring Your Own Test Cases)](#custom-rules-bring-your-own-test-cases)
- [AI Analysis Provider (Groq / Gemini)](#ai-analysis-provider-groq--gemini)
- [API Reference](#api-reference)
- [Automated Tests](#automated-tests)
- [Full Manual QA Before Deploying](#full-manual-qa-before-deploying)
- [Troubleshooting](#troubleshooting)

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|---------------------------------------------------|
| Backend     | FastAPI, Python 3.13, Pydantic v2                 |
| Templates   | Jinja2 (server-rendered HTML)                     |
| Styling     | Tailwind CSS                                       |
| Frontend    | Vanilla JavaScript (no framework)                  |
| AI          | Groq API (default, free) with Gemini API fallback |
| Reports     | ReportLab (PDF), openpyxl (XLSX)                   |
| Testing     | pytest, FastAPI `TestClient`                      |

No database and no authentication layer — state lives entirely on disk as
per-workspace JSON/report files, which keeps the project simple to run and
reason about.

---

## Project Structure

```
testpilot-ai/
├── app/
│   ├── main.py                    # App factory, lifespan, routers, /health
│   ├── config.py                  # Centralized Pydantic Settings + workspace paths
│   ├── routes/
│   │   ├── pages.py                # /, /features, /settings (HTML)
│   │   ├── upload.py                # /api/v1/upload (legacy single-file upload)
│   │   └── workspace.py             # /api/v1/workspaces (full pipeline)
│   ├── parser/
│   │   └── spec_parser.py           # JSON spec -> validated TestSpec
│   ├── services/
│   │   ├── pipeline_service.py       # Orchestrates Parse -> Rules -> AI -> Report
│   │   ├── rule_engine.py            # Default/predefined structural checks
│   │   ├── custom_rule_engine.py     # User-supplied rules engine
│   │   ├── report_service.py         # PDF + XLSX report generation
│   │   └── storage_service.py
│   ├── ai/
│   │   └── analyzer.py               # Groq (default) / Gemini AI analysis
│   ├── utilities/
│   │   └── file_validation.py
│   ├── models/
│   │   ├── upload.py                 # Legacy upload response models
│   │   └── workspace.py              # TestSpec, RuleEngineResult, CustomRule, etc.
│   ├── templates/                     # Jinja2 HTML templates
│   └── static/                        # CSS (Tailwind) and JS
├── storage/                            # Runtime workspace data (git-ignored except .gitkeep)
├── tests/                              # pytest suite (see below)
├── requirements.txt                    # Production dependencies
├── requirements-dev.txt                # + pytest, httpx for testing
├── pytest.ini
├── render.yaml                          # Render.com deploy config
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.13 (3.10+ generally works, but 3.13 is what this project targets)
- Node.js + npm (for compiling Tailwind CSS)
- A free **Groq API key** (recommended — no billing card required):
  <https://console.groq.com/keys>
- Optionally, a **Gemini API key** as a fallback if you already have one.
  Note that Gemini's free tier commonly stays locked at a 0 quota until a
  Google Cloud billing account is linked, which is why Groq is the default.

---

## Getting Started

### 1. Create a virtual environment and install Python dependencies

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (cmd.exe)**
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Install Node dependencies and build Tailwind CSS

```bash
npm install
npm run build:css
```

Use `npm run watch:css` instead if you're actively editing styles — it
rebuilds `output.css` automatically as you save.

### 3. Configure environment variables

Copy the example file and fill in real values:

```bash
cp .env.example .env        # macOS/Linux
copy .env.example .env      # Windows
```

At minimum, set `GROQ_API_KEY` so the AI Analysis stage actually runs (the
app still starts and works without it — the AI stage is just skipped with a
clear message). See [Environment Variables](#environment-variables) below.

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

- App: <http://127.0.0.1:8000>
- Health check: <http://127.0.0.1:8000/health>
- Interactive API docs (Swagger UI): <http://127.0.0.1:8000/docs>

Drop `--reload` for anything resembling a production run.

---

## Environment Variables

All settings live in `app/config.py` and have sane defaults, so `.env` only
needs to override what's different for your machine.

| Variable            | Default                    | Description                                                     |
|---------------------|-----------------------------|--------------------------------------------------------------------|
| `ENVIRONMENT`        | `development`              | `development` \| `staging` \| `production`                        |
| `HOST`               | `127.0.0.1`                 | Bind address for uvicorn                                            |
| `PORT`               | `8000`                      | Bind port for uvicorn                                                |
| `DEBUG`              | `True`                      | Enables FastAPI debug mode                                           |
| `GROQ_API_KEY`       | *(empty)*                   | Groq API key — **preferred** provider for AI analysis, free, no card required |
| `GROQ_MODEL`         | `llama-3.3-70b-versatile`  | Groq model used for the AI analysis stage                            |
| `GEMINI_API_KEY`     | *(empty)*                   | Gemini API key — only used as a fallback if `GROQ_API_KEY` isn't set |
| `GEMINI_MODEL`       | `gemini-2.0-flash`          | Gemini model used for the AI analysis stage                          |
| `STORAGE_DIR`        | `storage`                    | Root folder for all workspaces                                        |
| `REPORTS_SUBDIR`     | `reports`                    | Shared reports folder under storage                                    |
| `LOGS_DIR`           | `logs`                       | Application log output folder                                          |
| `MAX_FILE_SIZE_MB`   | `50`                         | Max upload size in MB                                                    |

---

## Storage Model

Rather than one flat uploads folder, each analysis run gets its own isolated
**workspace** directory:

```
storage/
    <workspace_id>/
        spec.json           # original uploaded spec
        parsed.json          # output of the parser stage
        rule_engine.json     # rule engine findings (default or custom — see `source` field)
        ai_analysis.json     # Groq/Gemini findings
        report.pdf            # generated report
        report.xlsx            # generated spreadsheet
```

All of `storage/`, `storage/reports/`, `logs/`, and the legacy
`storage/uploads/` folder are created automatically on startup — you never
need to create them by hand.

---

## Custom Rules (Bring Your Own Test Cases)

By default, the Rule Engine stage runs a fixed set of predefined structural
checks (unique IDs/names, valid HTTP methods, well-formed endpoints, valid
status codes, etc. — see `app/services/rule_engine.py`).

On the home page, you can switch **"Default test cases" → "My own test
cases"** to run your own checks instead, either by pasting JSON into the
text box or uploading a rules `.json` file (the file just populates the text
box — whichever is present in the form when you upload gets used).

Each rule targets one field on every test case in your spec, using
dot-notation for nested fields (e.g. `headers.Authorization`,
`request_body.user_id`):

```json
{
  "rules": [
    { "field": "method", "type": "required", "severity": "error" },
    { "field": "expected_status", "type": "range", "min": 100, "max": 599, "severity": "error" },
    { "field": "endpoint", "type": "starts_with", "value": "/", "severity": "warning" },
    { "field": "headers.Authorization", "type": "required", "severity": "info",
      "message": "Consider testing with an Authorization header." }
  ]
}
```

Supported `type`s: `required`, `not_empty`, `equals`, `not_equals`, `in`,
`not_in`, `starts_with`, `ends_with`, `contains`, `regex`, `min`, `max`,
`range`.

The result you get back (`rule_engine.source`) tells you whether `"default"`
or `"custom"` rules were used for that run.

---

## AI Analysis Provider (Groq / Gemini)

The AI Analysis stage (`app/ai/analyzer.py`) sends the parsed spec + rule
engine findings to an LLM and asks for judgment-call findings a
deterministic rule engine can't catch (missing negative-path tests, missing
edge cases, unclear test intent, coverage gaps).

- If `GROQ_API_KEY` is set, Groq is used (default, recommended — free tier,
  no billing card required).
- Otherwise, if `GEMINI_API_KEY` is set, Gemini is used.
- If neither is set, this stage is skipped and the rest of the pipeline
  still completes normally — `ai_analysis.skipped_reason` explains why.

This stage never takes the pipeline down: if the call fails, times out, or
returns something that doesn't parse as JSON, you get a clear
`skipped_reason` in the report instead of a crash.

---

## API Reference

| Method | Path                              | Description                                                        |
|--------|--------------------------------------|------------------------------------------------------------------------|
| GET    | `/`                                 | Home page (drag-and-drop upload UI + custom rules toggle)             |
| GET    | `/features`                         | Pipeline / capabilities page                                             |
| GET    | `/settings`                         | Live configuration readout                                                |
| GET    | `/health`                           | Liveness check — `{status, version, environment}`                        |
| POST   | `/api/v1/upload`                    | Legacy: store a file without running the pipeline (multipart `file`)     |
| POST   | `/api/v1/workspaces`                | Upload a spec and run the full pipeline (see below)                        |
| GET    | `/api/v1/workspaces/{id}`           | Fetch a previously-run workspace's results                                  |
| GET    | `/api/v1/workspaces/{id}/report.pdf`  | Download the generated PDF report                                              |
| GET    | `/api/v1/workspaces/{id}/report.xlsx` | Download the generated XLSX report                                              |
| GET    | `/docs`                             | Swagger UI (interactive API docs)                                                |
| GET    | `/openapi.json`                     | Raw OpenAPI schema                                                                 |

### `POST /api/v1/workspaces`

Multipart form fields:

| Field           | Required | Description                                                                 |
|------------------|----------|---------------------------------------------------------------------------------|
| `file`            | Yes       | The test spec file (JSON)                                                          |
| `custom_rules`    | No        | Custom rules JSON as form text — used instead of default rules if present         |
| `rules_file`      | No        | Custom rules JSON as a file upload — wins over `custom_rules` if both are sent    |

Always returns **200** with a `WorkspaceResponse`. If any stage fails,
`status` is `"failed"` and `error` explains why, rather than a generic 500.

---

## Automated Tests

The `tests/` folder holds a pytest suite covering config, health check, page
rendering, and the legacy upload API — **32 tests** in total. The newer
`/api/v1/workspaces` pipeline (parse → rule engine → custom rules → AI →
report) is exercised manually / via `/docs` today and isn't yet covered by
this suite — see the manual QA checklist below.

| File                    | Covers                                                                         |
|--------------------------|---------------------------------------------------------------------------------|
| `tests/test_config.py`  | Settings defaults, path resolution, workspace helpers, `ensure_directories()` |
| `tests/test_health.py`  | `GET /health` status code and response shape                                  |
| `tests/test_pages.py`   | `/`, `/features`, `/settings` rendering, nav links, `/docs`, 404 handling      |
| `tests/test_upload.py`  | Valid uploads, empty files, oversized files, missing file field, unique filenames, disk writes |

### Install test dependencies

```bash
pip install -r requirements-dev.txt
```

### Run the full suite

```bash
pytest
```

### Run a single file, or with coverage

```bash
pytest tests/test_upload.py -v
pytest --cov=app --cov-report=term-missing
```

Tests use FastAPI's `TestClient` and write uploads to a temporary directory
(via a fixture in `tests/conftest.py`), so running them never touches your
real `storage/` folder or leaves files behind.

---

## Full Manual QA Before Deploying

Automated tests cover the legacy upload path and page rendering; the
checklist below covers everything else — visuals, real browser behavior,
and the full pipeline.

### 1. Fresh install sanity check
- [ ] Delete `venv/`, `node_modules/`, and `storage/` (keep `storage/uploads/.gitkeep`), then follow the [Getting Started](#getting-started) steps on a clean checkout to confirm nothing was undocumented.
- [ ] Confirm `storage/`, `storage/reports/`, and `logs/` are recreated automatically on first run (check the terminal log line `Storage root: ...`).

### 2. Automated tests + linting
- [ ] `pytest` — all tests pass.
- [ ] `pytest --cov=app` — check nothing critical is untested (aim to cover any new route or service you add).
- [ ] Run the app itself and watch the terminal for unhandled exceptions or stack traces during normal use.

### 3. Pages, in a real browser (not just `TestClient`)
- [ ] `/` — drag-and-drop zone accepts a click and a real drag-and-drop; "Default test cases" vs "My own test cases" toggle switches the custom rules panel correctly.
- [ ] `/features` — all pipeline stages render correctly on desktop **and** mobile width (resize to ~375px).
- [ ] `/settings` — values match what's actually in your `.env` (flip `DEBUG` and reload to confirm it updates).
- [ ] Nav bar: Workspace / Features / API Docs / Settings all navigate correctly, and the active page doesn't look broken when revisited.
- [ ] `/docs` — Swagger UI loads and `POST /api/v1/workspaces` can be exercised directly from it ("Try it out"), including with a `rules_file` attached.

### 4. Upload flow, end to end
- [ ] Upload a small valid spec (e.g. a `.json` under 1MB) with default rules — success notification appears, progress bar completes, report downloads work.
- [ ] Switch to "My own test cases", paste a custom rules JSON, and confirm the results badge reads "Custom rules" and findings match your rules.
- [ ] Upload a rules `.json` file instead of pasting — confirm it populates the textarea and is used.
- [ ] Submit invalid custom rules JSON — should fail cleanly with a clear error, not a stack trace.
- [ ] Upload an empty (0-byte) file — should be rejected with a clear error, not a silent failure.
- [ ] Upload a file larger than `MAX_FILE_SIZE_MB` — should be rejected before the full file is read.
- [ ] Cancel a drag mid-way (drag a file over the dropzone, then drag it back out) — UI should not get stuck in a broken state.

### 5. Responsive & accessibility pass
- [ ] Test at common breakpoints: mobile (375px), tablet (768px), desktop (1440px).
- [ ] Tab through the page with keyboard only — dropzone, rules toggle, nav links, and buttons should all be reachable and show a visible focus state.
- [ ] Check color contrast on the dark background, especially status badges on `/settings` and the rules-source badge on the results panel.

### 6. Configuration & secrets
- [ ] Confirm `.env` is in `.gitignore` and was never committed (`git log --all -- .env` should be empty).
- [ ] Run once with both `GROQ_API_KEY` and `GEMINI_API_KEY` unset — `/settings` should clearly flag AI as "Not configured" rather than crashing, and the AI analysis result should show a clear `skipped_reason`.
- [ ] Set `ENVIRONMENT=production` locally and confirm `/health` reflects it and nothing dev-only leaks into the response (stack traces, debug banners).

### 7. Performance / resource sanity
- [ ] Upload a file close to the `MAX_FILE_SIZE_MB` limit and confirm memory stays reasonable (uploads are streamed in 1MB chunks, not loaded fully into memory).
- [ ] Restart the server and confirm startup completes quickly and logs the expected lines (app name, version, environment, storage root).

### 8. Before you actually deploy
- [ ] Set `DEBUG=False` and `ENVIRONMENT=production` in the deployment environment.
- [ ] Tighten `CORS_ALLOW_ORIGINS` in `app/config.py` from `["*"]` to your real frontend origin(s).
- [ ] Double-check `GROQ_API_KEY` (and `GEMINI_API_KEY` if used) is set via your hosting provider's secret manager, not committed anywhere.
- [ ] Confirm the `storage/` directory is on persistent (not ephemeral) storage if you need uploaded workspaces to survive a redeploy.
- [ ] Run `pytest` one last time against the exact commit you're deploying.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'app'` when running pytest**
Run `pytest` from the project root (not from inside `app/` or `tests/`) —
`pytest.ini` sets `pythonpath = .` to make `app` importable.

**Tailwind classes aren't applying**
Run `npm run build:css` again — `output.css` is a build artifact and is
git-ignored, so it won't exist on a fresh checkout until you build it.

**Uploads return 400 "File cannot be empty"**
This is expected for 0-byte files — it's a real validation rule in
`app/utilities/file_validation.py`, not a bug.

**AI analysis says "quota exceeded" or similar**
That's almost always Gemini's free tier, which commonly stays locked at a 0
quota until a Google Cloud billing account is linked. Set `GROQ_API_KEY`
instead — it's free with no billing card required
(<https://console.groq.com/keys>) and is used automatically once set.

**Custom rules aren't being applied**
Confirm you actually selected "My own test cases" on the page (not just
filled in the textarea), and that the JSON is valid — check
`rule_engine.source` in the response: it should read `"custom"`, not
`"default"`.

**Nav links go to a page that doesn't visually update**
Hard-refresh (`Ctrl+Shift+R` / `Cmd+Shift+R`) after rebuilding CSS — browsers
aggressively cache `output.css`.
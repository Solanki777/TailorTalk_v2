# TestPilot AI

TestPilot AI is an AI-powered test analysis platform with a FastAPI backend, a
custom Tailwind CSS frontend, and a glassmorphism interface. Files uploaded
through the UI are turned into isolated **workspaces** that move through a
five-stage pipeline — upload, parse, rule engine, AI analysis, report — with
Google Gemini used for the analysis stage.

```
Upload → Parse → Rule Engine → AI Analysis → Report
```

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Storage Model](#storage-model)
- [API Reference](#api-reference)
- [Automated Tests](#automated-tests)
- [Full Manual QA Before Deploying](#full-manual-qa-before-deploying)
- [Troubleshooting](#troubleshooting)

---

## Tech Stack

| Layer       | Technology                          |
|-------------|--------------------------------------|
| Backend     | FastAPI, Python 3.13, Pydantic v2   |
| Templates   | Jinja2 (server-rendered HTML)       |
| Styling     | Tailwind CSS                        |
| Frontend    | Vanilla JavaScript (no framework)   |
| AI          | Google Gemini API                   |
| Testing     | pytest, FastAPI `TestClient`        |

No database and no authentication layer — state lives entirely on disk as
per-workspace JSON/report files, which keeps the project simple to run and
reason about.

---

## Project Structure

```
testpilot-ai/
├── app/
│   ├── main.py               # App factory, lifespan, routers, /health
│   ├── config.py             # Centralized Pydantic Settings + workspace paths
│   ├── routes/
│   │   ├── pages.py          # /, /features, /settings (HTML)
│   │   └── upload.py         # /api/v1/upload (JSON API)
│   ├── services/
│   │   └── storage_service.py
│   ├── utilities/
│   │   └── file_validation.py
│   ├── parser/                # Parsing stage (in progress)
│   ├── ai/                    # Gemini integration (in progress)
│   ├── models/
│   │   └── upload.py         # Pydantic response models
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS (Tailwind) and JS
├── storage/                   # Runtime workspace data (git-ignored except .gitkeep)
├── tests/                     # pytest suite (see below)
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # + pytest, httpx for testing
├── pytest.ini
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.13 (3.10+ generally works, but 3.13 is what this project targets)
- Node.js + npm (for compiling Tailwind CSS)
- A Google Gemini API key (optional for now — the AI analysis stage is still
  being built, but the app runs fine without a key)

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

Copy the example file and fill in real values (a Gemini key is optional to
start the server, but required for the AI analysis stage):

```bash
cp .env.example .env        # macOS/Linux
copy .env.example .env      # Windows
```

See [Environment Variables](#environment-variables) for what each field does.

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

| Variable            | Default                | Description                                   |
|---------------------|-------------------------|------------------------------------------------|
| `ENVIRONMENT`        | `development`          | `development` \| `staging` \| `production`     |
| `HOST`               | `127.0.0.1`             | Bind address for uvicorn                        |
| `PORT`               | `8000`                  | Bind port for uvicorn                           |
| `DEBUG`              | `True`                  | Enables FastAPI debug mode                      |
| `GEMINI_API_KEY`     | *(empty)*               | Google Gemini API key                           |
| `GEMINI_MODEL`       | `gemini-2.0-flash`      | Model used for the AI analysis stage            |
| `STORAGE_DIR`        | `storage`               | Root folder for all workspaces                  |
| `REPORTS_SUBDIR`     | `reports`               | Shared reports folder under storage             |
| `LOGS_DIR`           | `logs`                  | Application log output folder                   |
| `MAX_FILE_SIZE_MB`   | `50`                    | Max upload size in MB                           |

---

## Storage Model

Rather than one flat uploads folder, each analysis run gets its own isolated
**workspace** directory:

```
storage/
    <workspace_id>/
        spec.json          # original uploaded spec
        parsed.json         # output of the parser stage
        rule_engine.json    # deterministic rule checks
        ai_analysis.json    # Gemini's findings
        report.pdf           # generated report
        report.xlsx          # generated spreadsheet
```

All of `storage/`, `storage/reports/`, `logs/`, and the legacy
`storage/uploads/` folder are created automatically on startup — you never
need to create them by hand.

---

## API Reference

| Method | Path              | Description                                  |
|--------|-------------------|-----------------------------------------------|
| GET    | `/`               | Home page (drag-and-drop upload UI)          |
| GET    | `/features`       | Pipeline / capabilities page                  |
| GET    | `/settings`       | Live configuration readout                    |
| GET    | `/health`         | Liveness check — `{status, version, environment}` |
| POST   | `/api/v1/upload`  | Upload a file (multipart `file` field)        |
| GET    | `/docs`           | Swagger UI (interactive API docs)             |
| GET    | `/openapi.json`   | Raw OpenAPI schema                            |

`/api/v1/upload` responses:

- **200** — file accepted and stored:
  ```json
  {
    "filename": "spec.json",
    "file_size": 1234,
    "saved_path": "/absolute/path/to/storage/uploads/<uuid>_spec.json",
    "status": "success",
    "message": "File uploaded and validated successfully."
  }
  ```
- **400** — validation failed (empty file, oversized file, no filename)
- **422** — request malformed (no `file` field sent at all)

---

## Automated Tests

The `tests/` folder holds a pytest suite covering config, health check, page
rendering, and the upload API — **32 tests** in total.

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

Automated tests cover backend logic; the checklist below covers everything
that needs a human eye — visuals, real browser behavior, and the parts of
the pipeline still being built out.

### 1. Fresh install sanity check
- [ ] Delete `venv/`, `node_modules/`, and `storage/` (keep `storage/uploads/.gitkeep`), then follow the [Getting Started](#getting-started) steps on a clean checkout to confirm nothing was undocumented.
- [ ] Confirm `storage/`, `storage/reports/`, and `logs/` are recreated automatically on first run (check the terminal log line `Storage root: ...`).

### 2. Automated tests + linting
- [ ] `pytest` — all tests pass.
- [ ] `pytest --cov=app` — check nothing critical is untested (aim to cover any new route or service you add).
- [ ] Run the app itself and watch the terminal for unhandled exceptions or stack traces during normal use.

### 3. Pages, in a real browser (not just `TestClient`)
- [ ] `/` — drag-and-drop zone accepts a click and a real drag-and-drop.
- [ ] `/features` — all 5 pipeline stages render correctly on desktop **and** mobile width (resize to ~375px).
- [ ] `/settings` — values match what's actually in your `.env` (flip `DEBUG` and reload to confirm it updates).
- [ ] Nav bar: Workspace / Features / API Docs / Settings all navigate correctly, and the active page doesn't look broken when revisited.
- [ ] `/docs` — Swagger UI loads and `POST /api/v1/upload` can be exercised directly from it ("Try it out").

### 4. Upload flow, end to end
- [ ] Upload a small valid file (e.g. a `.json` under 1MB) — success notification appears, progress bar completes.
- [ ] Upload an empty (0-byte) file — should be rejected with a clear error, not a silent failure.
- [ ] Upload a file larger than `MAX_FILE_SIZE_MB` — should be rejected before the full file is read.
- [ ] Upload two files with the same name back-to-back — confirm both are saved separately (check `storage/uploads/`) and don't overwrite each other.
- [ ] Cancel a drag mid-way (drag a file over the dropzone, then drag it back out) — UI should not get stuck in a broken state.

### 5. Responsive & accessibility pass
- [ ] Test at common breakpoints: mobile (375px), tablet (768px), desktop (1440px).
- [ ] Tab through the page with keyboard only — dropzone, nav links, and buttons should all be reachable and show a visible focus state.
- [ ] Check color contrast on the dark background, especially status badges on `/settings`.

### 6. Configuration & secrets
- [ ] Confirm `.env` is in `.gitignore` and was never committed (`git log --all -- .env` should be empty).
- [ ] Run once with `GEMINI_API_KEY` unset — `/settings` should clearly flag it as "Not configured" rather than crashing.
- [ ] Set `ENVIRONMENT=production` locally and confirm `/health` reflects it and nothing dev-only leaks into the response (stack traces, debug banners).

### 7. Performance / resource sanity
- [ ] Upload a file close to the `MAX_FILE_SIZE_MB` limit and confirm memory stays reasonable (uploads are streamed in 1MB chunks, not loaded fully into memory).
- [ ] Restart the server and confirm startup completes quickly and logs the expected lines (app name, version, environment, storage root).

### 8. Before you actually deploy
- [ ] Set `DEBUG=False` and `ENVIRONMENT=production` in the deployment environment.
- [ ] Tighten `CORS_ALLOW_ORIGINS` in `app/config.py` from `["*"]` to your real frontend origin(s).
- [ ] Double-check `GEMINI_API_KEY` is set via your hosting provider's secret manager, not committed anywhere.
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

**Nav links go to a page that doesn't visually update**
Hard-refresh (`Ctrl+Shift+R` / `Cmd+Shift+R`) after rebuilding CSS — browsers
aggressively cache `output.css`.
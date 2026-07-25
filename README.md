# TestPilot AI

TestPilot AI is a web application with a FastAPI backend and a custom Tailwind CSS frontend, featuring dynamic glassmorphism aesthetics.

## Prerequisites

- Python 3.10+
- Node.js (for Tailwind CSS compilation)

## Getting Started

### 1. Set Up Python Environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies and Compile CSS
```bash
npm install
npm run build:css
```

### 3. Setup Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key (optional for local mock testing):
```bash
copy .env.example .env
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

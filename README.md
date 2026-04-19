# AI Support + Sales Copilot

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Pytest](https://img.shields.io/badge/Tests-Pytest-0A9EDC?logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI_Ready-2088FF?logo=githubactions&logoColor=white)

A production-oriented AI chatbot for support and sales teams. The project combines a FastAPI backend, a Next.js frontend, document ingestion, retrieval, grounded responses, and operator tooling for testing and admin workflows.

## Why This Project Exists

Support and sales teams need answers that are fast, consistent, and grounded in company documentation. This copilot is built to:

- answer customer-facing questions from uploaded knowledge documents
- surface confidence and human-handoff signals
- support internal testing through retrieval and health endpoints
- provide a polished demo-ready interface for both end users and operators

## Core Capabilities

- Grounded chat responses from indexed company documents
- PDF ingestion pipeline with filename sanitization and upload size limits
- Retrieval endpoint for inspecting what the system can find
- Health endpoint that exposes runtime and indexing status
- Human-escalation behavior when confidence is low
- Groq-compatible LLM integration with a local extractive fallback
- Chroma-backed retrieval with a lightweight keyword fallback for local demos and restricted environments

## Architecture

### Backend
- Framework: FastAPI
- Entry point: `backend/app/main.py`
- Chat route: `POST /api/chat`
- Document routes: upload, retrieve, list, delete
- Health route: `GET /api/health`

### Frontend
- Framework: Next.js 16 with React 19
- App directory: `frontend/src/app`
- Includes a customer chat experience and an admin area

### Retrieval Layer
- Primary store: ChromaDB
- Embeddings: `sentence-transformers`
- Local resilience: keyword-based fallback index for smoke tests and constrained environments

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   `-- services/
|   |-- data/
|   |   `-- sample-company-handbook.md
|   `-- tests/
|-- frontend/
|   `-- src/app/
|-- .github/workflows/ci.yml
|-- docker-compose.yml
`-- README.md
```

## Local Setup

### Prerequisites

- Python 3.13
- Node.js 24
- npm

### 1. Clone and install backend dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Configure backend environment

Create `backend/.env` if you want to override defaults:

```env
APP_ENV=development
APP_VERSION=1.0.0
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
MAX_UPLOAD_SIZE_BYTES=10485760
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Notes:

- If `GROQ_API_KEY` is not set, the backend still works and falls back to an extractive answer mode.
- Application data is stored under `backend/data/`.

### 3. Run the backend

```bash
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` for the UI and `http://localhost:8000/docs` for the backend API docs.

## Docker

The repository includes a simple `docker-compose.yml` for the backend service:

```bash
docker compose up --build
```

This currently focuses on the backend runtime. The frontend is still intended to be run locally with `npm run dev`.

## Sample Document and Human-Style Demo

The repo now includes a realistic sample knowledge-base document:

- `backend/data/sample-company-handbook.md`

To run a local smoke test that seeds this document and chats against it with realistic follow-up questions:

```bash
.venv\Scripts\python.exe backend/scripts/demo_chatbot.py
```

The demo script:

- indexes the sample handbook into a local fallback store
- sends a short multi-turn conversation through the FastAPI app
- prints answers, confidence, human-escalation state, and retrieval count

Example topics covered in the scripted conversation:

- Growth-plan onboarding timeline
- Salesforce and Slack integrations
- Workflow overage policy
- EU data residency availability

## Testing

Run the backend test suite:

```bash
.venv\Scripts\pytest.exe backend/tests -q
```

There is also a dedicated sample-chatbot integration test that validates the seeded handbook flow.

## API Summary

### Chat

`POST /api/chat`

Request body:

```json
{
  "message": "Do you support Salesforce?",
  "conversation_history": [],
  "company_id": "startup-demo-001"
}
```

Response fields:

- `answer`
- `needs_human`
- `confidence`
- `retrieval_count`
- `response_time_ms`

### Documents

- `POST /api/documents/upload`
- `POST /api/documents/retrieve`
- `GET /api/documents`
- `DELETE /api/documents/{document_id}`

### Health

- `GET /api/health`

Returns environment, version, model configuration status, and indexed document count.

## CI

GitHub Actions configuration lives in `.github/workflows/ci.yml` and currently runs:

- backend dependency installation and `pytest`
- frontend dependency installation and production build

## Current Production-Oriented Improvements

- typed settings via `pydantic-settings`
- safer upload handling and file sanitization
- structured response metadata for chat latency and confidence
- lazy vector-store initialization for faster backend startup
- local retrieval fallback when Chroma or embeddings are unavailable

## Next Steps

- add authentication and tenant isolation
- move documents and metadata into managed infrastructure
- add background ingestion jobs
- store chat analytics and audit events
- expand automated tests for upload and retrieval edge cases

# AI Support + Sales Copilot

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Pytest](https://img.shields.io/badge/Tests-Pytest-0A9EDC?logo=pytest&logoColor=white)
[![CI/CD Pipeline](https://github.com/JaiEnfer/ai-support-sales-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/JaiEnfer/ai-support-sales-copilot/actions/workflows/ci.yml)

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
- Request tracing with `X-Request-ID` for easier debugging across logs and clients
- Optional API-key protection for chat and admin/document endpoints
- Trusted-host and production docs controls for safer public deployment
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
- Includes a customer chat experience, an admin area, and an embeddable website widget

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

Create `backend/.env` from `backend/.env.example` if you want to override defaults:

```env
APP_ENV=development
APP_VERSION=1.0.0
ENABLE_API_DOCS=true
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
DEFAULT_COMPANY_ID=startup-demo-001
ADMIN_API_KEY=change-me-admin-key
CHAT_API_KEY=
REQUIRE_COMPANY_ID=true
MAX_CHAT_HISTORY_MESSAGES=12
MAX_CHAT_MESSAGE_LENGTH=4000
MAX_UPLOAD_SIZE_BYTES=10485760
TRUSTED_HOSTS=["localhost","127.0.0.1","testserver"]
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Notes:

- If `GROQ_API_KEY` is not set, the backend still works and falls back to an extractive answer mode.
- Application data is stored under `backend/data/`.
- Set `ADMIN_API_KEY` before exposing document-management endpoints outside local development.
- Set `CHAT_API_KEY` if you want to protect public chat traffic behind a shared key or gateway.

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

Create `frontend/.env.local` from `frontend/.env.example` if you want the frontend to send tenant and API-key headers automatically during local development.

## Docker

The repository includes a production-shaped `Dockerfile` and `docker-compose.yml` for the backend service:

```bash
docker compose up --build
```

The compose service now uses a built image, restart policy, environment file, and a liveness healthcheck. The frontend is still intended to be run locally with `npm run dev`.

## Multi-Company Product Flow

This project now supports a basic white-label model:

- each company uses a unique `company_id`
- uploads, retrieval, and chat responses are scoped to that company
- the admin dashboard can be pointed at a specific tenant/company workspace
- the website widget can be embedded on any client site and tied to that company
- the admin dashboard can also scrape a client website and index a few same-domain pages for demos
- scraped websites now generate a structured summary layer before raw page text is indexed, improving demo answer quality
- each company can use its own chatbot tone: `sales`, `support`, or `portfolio`

### Tenant onboarding

1. Pick a `company_id` such as `acme-dental`
2. Open the admin dashboard and set that company ID
3. Upload that company’s PDFs and knowledge files
4. Embed the widget script on that company’s website

For faster demos, you can also paste a client website URL into the admin dashboard and let the app ingest the homepage plus a few linked pages.

### Website embed snippet

Serve the frontend publicly, then place this on a client website:

```html
<script
  src="https://your-frontend-domain.com/widget.js"
  data-company="acme-dental"
  data-title="Acme Dental Assistant"
  data-subtitle="Ask us about services, bookings, pricing, or insurance."
  data-api-key="public-chat-key-if-used"
  data-button-label="Chat with Acme Dental"
></script>
```

The script injects a floating chat button and loads an iframe-backed assistant from `/embed`.

### Admin tenant workflow

- use `X-Company-ID` or the admin page tenant field to scope uploads
- use `ADMIN_API_KEY` to protect document-management endpoints
- use `CHAT_API_KEY` if you want the embeddable widget to call chat through a shared key

For real production deployments, replace shared chat keys with a gateway or token-based auth layer.

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

Optional headers:

- `X-API-Key` for chat protection when `CHAT_API_KEY` is configured
- `X-Company-ID` to pass tenant/company context from an API gateway or frontend
- `X-Request-ID` to supply your own trace identifier

Response fields:

- `answer`
- `needs_human`
- `confidence`
- `retrieval_count`
- `response_time_ms`
- `company_id`
- `request_id`

### Documents

- `POST /api/documents/upload`
- `POST /api/documents/retrieve`
- `GET /api/documents`
- `DELETE /api/documents/{document_id}`

When `ADMIN_API_KEY` is configured, document endpoints require `X-API-Key`.
All document endpoints are company-scoped through `X-Company-ID` or the configured default company.

### Health

- `GET /api/health`
- `GET /api/health/live`
- `GET /api/health/ready`

Returns environment, version, model configuration status, request ID, readiness checks, and indexed document count.

## CI

GitHub Actions configuration lives in `.github/workflows/ci.yml` and currently runs:

- backend dependency installation and `pytest`
- frontend dependency installation and production build

## Current Production-Oriented Improvements

- typed settings via `pydantic-settings`
- safer upload handling and file sanitization
- structured response metadata for chat latency and confidence
- request tracing and safer operational response metadata
- optional API-key enforcement for chat and document administration
- company-aware tenant scoping for uploads, retrieval, and chat
- trusted-host controls and production docs disabling support
- lazy vector-store initialization for faster backend startup
- local retrieval fallback when Chroma or embeddings are unavailable
- Docker image build and compose healthcheck for cleaner deployments
- embeddable website widget via `frontend/src/app/widget.js/route.ts`

## Next Steps

- replace shared API keys with JWT/OIDC auth and role-based access control
- move documents and metadata into managed infrastructure
- add background ingestion jobs
- store chat analytics and audit events
- add per-tenant branding, analytics, CRM capture, and custom domains
- expand automated tests for upload and retrieval edge cases

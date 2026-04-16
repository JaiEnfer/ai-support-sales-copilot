# AI Support + Sales Copilot

A production-oriented RAG copilot for startup support and sales teams.

## What it does
- Answers customer questions from uploaded company documents
- Shows sources, confidence, and human-escalation signals
- Lets operators upload PDFs, test retrieval, and monitor runtime health
- Provides a polished customer-facing chat UI and an admin console

## Tech Stack
- Backend: FastAPI
- Frontend: Next.js 16 + React 19 + Tailwind CSS 4
- Retrieval: ChromaDB + sentence-transformers
- LLM gateway: Groq-compatible OpenAI client

## Production-oriented improvements in this version
- Typed environment-driven app configuration
- Safer document ingestion with filename sanitization and upload-size limits
- Health endpoint with environment, model, and indexed-document visibility
- Structured chat metadata including confidence, retrieval count, and latency
- More polished frontend UI suitable for demos and early client delivery

## Core environment variables
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `APP_ENV`
- `APP_VERSION`
- `MAX_UPLOAD_SIZE_BYTES`
- `ALLOWED_ORIGINS`

## Next steps for enterprise readiness
- Add authentication and tenant isolation
- Store documents and metadata in managed infrastructure
- Add audit logs and analytics
- Add background jobs for ingestion and re-indexing
- Add automated backend tests in a dedicated virtual environment

"""FastAPI application bootstrap and cross-cutting middleware setup."""

from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.dependencies import REQUEST_ID_HEADER, assign_request_id
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.company_profile import router as company_profile_router
from backend.app.api.documents import router as documents_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.enable_api_docs and not settings.is_production else None,
    redoc_url="/redoc" if settings.enable_api_docs and not settings.is_production else None,
    openapi_url="/openapi.json" if settings.enable_api_docs and not settings.is_production else None,
    description=(
        "Production-oriented API for a startup support and sales copilot. "
        "It handles document ingestion, retrieval, and grounded chat responses."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.trusted_hosts:
    # Restrict host headers in production-style deployments to reduce abuse.
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Attach lightweight request tracing and latency metadata to every response."""
    started_at = perf_counter()
    request_id = assign_request_id(request)
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = str(int((perf_counter() - started_at) * 1000))
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return a stable error shape for unexpected server failures."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error.",
            "error_type": exc.__class__.__name__,
            "request_id": getattr(request.state, "request_id", None),
        },
    )

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(company_profile_router)
app.include_router(documents_router)


@app.get("/")
def read_root():
    """Simple root endpoint for smoke checks and basic environment discovery."""
    return {
        "message": "Backend is running",
        "product": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "capabilities": [
            "grounded-chat",
            "document-upload",
            "semantic-retrieval",
            "human-handoff-flags",
        ],
    }

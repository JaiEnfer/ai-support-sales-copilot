from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = str(int((perf_counter() - started_at) * 1000))
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error.",
            "error_type": exc.__class__.__name__,
        },
    )

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/")
def read_root():
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

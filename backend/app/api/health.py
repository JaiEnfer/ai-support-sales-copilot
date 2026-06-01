from fastapi import APIRouter, Request

from backend.app.api.dependencies import get_request_id
from backend.app.core.config import CHROMA_DIR, UPLOAD_DIR
from backend.app.core.config import settings
from backend.app.models.schemas import HealthResponse
from backend.app.services.document_registry import load_documents

router = APIRouter(prefix="/api", tags=["health"])


def _build_checks() -> dict[str, str]:
    checks = {
        "uploads_dir": "ok" if UPLOAD_DIR.exists() else "missing",
        "vector_store_dir": "ok" if CHROMA_DIR.exists() else "missing",
        "llm_provider": "configured" if settings.groq_api_key else "fallback",
    }
    return checks


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request):
    checks = _build_checks()
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        version=settings.app_version,
        llm_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
        documents_indexed=len(load_documents()),
        request_id=get_request_id(request),
        checks=checks,
    )


@router.get("/health/live", response_model=HealthResponse)
def liveness_check(request: Request):
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        version=settings.app_version,
        llm_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
        documents_indexed=0,
        request_id=get_request_id(request),
        checks={"app": "alive"},
    )


@router.get("/health/ready", response_model=HealthResponse)
def readiness_check(request: Request):
    checks = _build_checks()
    is_ready = all(value in {"ok", "configured", "fallback"} for value in checks.values())

    return HealthResponse(
        status="ok" if is_ready else "degraded",
        environment=settings.app_env,
        version=settings.app_version,
        llm_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
        documents_indexed=len(load_documents()),
        request_id=get_request_id(request),
        checks=checks,
    )

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.models.schemas import HealthResponse
from backend.app.services.document_registry import load_documents

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        version=settings.app_version,
        llm_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
        documents_indexed=len(load_documents()),
    )

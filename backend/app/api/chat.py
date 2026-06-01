from fastapi import APIRouter, Depends, Request

from backend.app.api.dependencies import get_request_id, require_chat_api_key, resolve_company_id
from backend.app.core.config import settings
from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.services.chat_service import generate_chat_response
from backend.app.services.company_profile_service import get_company_profile

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    http_request: Request,
    _: None = Depends(require_chat_api_key),
    company_id: str = Depends(resolve_company_id),
):
    effective_company_id = request.company_id or company_id
    company_profile = get_company_profile(effective_company_id)
    sanitized_request = request.model_copy(
        update={
            "company_id": effective_company_id,
            "conversation_history": request.conversation_history[-settings.max_chat_history_messages :],
        }
    )
    return generate_chat_response(
        sanitized_request,
        answer_mode=company_profile.answer_mode,
        request_id=get_request_id(http_request),
    )

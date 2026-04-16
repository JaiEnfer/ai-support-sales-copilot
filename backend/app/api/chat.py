from fastapi import APIRouter
from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.services.chat_service import generate_chat_response

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return generate_chat_response(request)

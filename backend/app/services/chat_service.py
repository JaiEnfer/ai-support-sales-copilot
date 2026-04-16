from backend.app.models.schemas import ChatRequest, ChatResponse, SourceItem


def generate_demo_chat_response(request: ChatRequest) -> ChatResponse:
    user_message = request.message.strip().lower()

    if "price" in user_message or "pricing" in user_message:
        return ChatResponse(
            answer="Our startup plan includes chatbot setup, website integration, and basic analytics.",
            sources=[
                SourceItem(
                    title="Pricing Overview",
                    snippet="Startup plan includes setup, integration, and analytics."
                )
            ],
            needs_human=False
        )

    if "human" in user_message or "agent" in user_message:
        return ChatResponse(
            answer="I can connect you to a human teammate for a detailed follow-up.",
            sources=[],
            needs_human=True
        )

    return ChatResponse(
        answer=(
            "Thanks for your question. This is the demo chat response layer. "
            "In the next steps, this will be connected to document retrieval and RAG."
        ),
        sources=[
            SourceItem(
                title="Demo Knowledge Base",
                snippet="This reply is currently generated from the demo service layer."
            )
        ],
        needs_human=False
    )
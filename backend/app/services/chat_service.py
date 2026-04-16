from backend.app.models.schemas import ChatRequest, ChatResponse, SourceItem
from backend.app.services.vector_store import search_chunks


def generate_demo_chat_response(request: ChatRequest) -> ChatResponse:
    results = search_chunks(request.message, top_k=3)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return ChatResponse(
            answer=(
                "I could not find relevant information in the uploaded knowledge base yet. "
                "Please upload documents or ask a human teammate."
            ),
            sources=[],
            needs_human=True
        )

    sources = []
    for doc, metadata in zip(documents, metadatas):
        snippet = doc[:220].replace("\n", " ").strip()
        sources.append(
            SourceItem(
                title=f"{metadata['filename']} (chunk {metadata['chunk_index']})",
                snippet=snippet
            )
        )

    answer = (
        "I found relevant information in the uploaded documents. "
        "Right now I am returning retrieval-grounded snippets. "
        "In the next step, we will turn these retrieved chunks into a polished RAG answer."
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        needs_human=False
    )
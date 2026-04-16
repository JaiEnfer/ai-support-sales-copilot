from time import perf_counter

from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.services.vector_store import search_chunks
from backend.app.services.llm_service import (
    _extract_query_terms,
    _score_text,
    generate_grounded_answer,
)

MIN_RETRIEVED_CHUNKS = 2
CHAT_RETRIEVAL_LIMIT = 8
LLM_CONTEXT_LIMIT = 4


def _rank_retrieved_chunks(user_question: str, retrieved_chunks: list[dict]) -> list[dict]:
    query_terms = _extract_query_terms(user_question)
    if not query_terms:
        return retrieved_chunks

    ranked_chunks = sorted(
        retrieved_chunks,
        key=lambda item: _score_text(item["content"], query_terms),
        reverse=True,
    )
    return ranked_chunks


def _dedupe_retrieved_chunks(retrieved_chunks: list[dict]) -> list[dict]:
    unique_chunks: list[dict] = []
    seen_keys: set[tuple[str, int]] = set()

    for item in retrieved_chunks:
        chunk_key = (item["filename"], item["chunk_index"])
        if chunk_key in seen_keys:
            continue
        seen_keys.add(chunk_key)
        unique_chunks.append(item)

    return unique_chunks


def generate_chat_response(request: ChatRequest) -> ChatResponse:
    started_at = perf_counter()
    results = search_chunks(request.message, top_k=CHAT_RETRIEVAL_LIMIT)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return ChatResponse(
            answer=(
                "I could not find relevant information in the knowledge base. "
                "Please ask a human teammate for help."
            ),
            needs_human=True,
            confidence="low",
            retrieval_count=0,
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    retrieved_chunks = []

    for doc, metadata in zip(documents, metadatas):
        retrieved_chunks.append(
            {
                "content": doc,
                "filename": metadata["filename"],
                "chunk_index": metadata["chunk_index"],
            }
        )

    retrieved_chunks = _dedupe_retrieved_chunks(retrieved_chunks)
    retrieved_chunks = _rank_retrieved_chunks(request.message, retrieved_chunks)

    if len(retrieved_chunks) < MIN_RETRIEVED_CHUNKS:
        return ChatResponse(
            answer=(
                "I found some information, but not enough to answer confidently. "
                "Please ask a human teammate for confirmation."
            ),
            needs_human=True,
            confidence="low",
            retrieval_count=len(retrieved_chunks),
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    try:
        answer = generate_grounded_answer(
            user_question=request.message,
            retrieved_chunks=retrieved_chunks[:LLM_CONTEXT_LIMIT],
            conversation_history=request.conversation_history,
        )
    except Exception:
        return ChatResponse(
            answer=(
                "I found relevant information, but the answer service is temporarily unavailable. "
                "Please retry or escalate to a human teammate."
            ),
            needs_human=True,
            confidence="low",
            retrieval_count=len(retrieved_chunks),
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    low_confidence_markers = [
        "not confident",
        "insufficient",
        "not enough information",
        "please ask a human",
        "human teammate",
        "cannot determine",
    ]

    answer_lower = answer.lower()
    needs_human = any(marker in answer_lower for marker in low_confidence_markers)
    confidence = "low" if needs_human else "high"

    return ChatResponse(
        answer=answer,
        needs_human=needs_human,
        confidence=confidence,
        retrieval_count=len(retrieved_chunks),
        response_time_ms=int((perf_counter() - started_at) * 1000),
    )

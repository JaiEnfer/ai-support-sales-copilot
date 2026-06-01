"""Chat orchestration layer.

This module keeps the route thin by handling retrieval, chunk ranking, answer
generation, and the final confidence/handoff decision in one place.
"""

import re
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
SINGLE_CHUNK_CONFIDENCE_SCORE = 8
SUMMARY_BOOST_SCORE = 10
PROFILE_QUERY_HINTS = {
    "about",
    "experience",
    "intro",
    "introduction",
    "key",
    "role",
    "skill",
    "skills",
    "who",
}


def _rank_retrieved_chunks(user_question: str, retrieved_chunks: list[dict]) -> list[dict]:
    """Re-rank chunks lexically to improve answer quality before generation."""
    query_terms = _extract_query_terms(user_question)
    if not query_terms:
        return retrieved_chunks

    question_tokens = {token.lower() for token in re.findall(r"[A-Za-z0-9]+", user_question)}
    scored_chunks = []
    for item in retrieved_chunks:
        base_score = _score_text(item["content"], query_terms)
        content_lower = item["content"].lower()

        if content_lower.startswith("website summary"):
            base_score += SUMMARY_BOOST_SCORE

        if question_tokens & PROFILE_QUERY_HINTS and (
            "primary roles:" in content_lower
            or "key skills:" in content_lower
            or "profile highlights:" in content_lower
        ):
            base_score += SUMMARY_BOOST_SCORE

        scored_chunks.append(
            {
                **item,
                "relevance_score": base_score,
            }
        )

    ranked_chunks = sorted(
        scored_chunks,
        key=lambda item: item.get("relevance_score", 0),
        reverse=True,
    )
    return ranked_chunks


def _dedupe_retrieved_chunks(retrieved_chunks: list[dict]) -> list[dict]:
    """Remove duplicate chunks while preserving the highest-ranked order."""
    unique_chunks: list[dict] = []
    seen_keys: set[tuple[str, int]] = set()

    for item in retrieved_chunks:
        chunk_key = (item["filename"], item["chunk_index"])
        if chunk_key in seen_keys:
            continue
        seen_keys.add(chunk_key)
        unique_chunks.append(item)

    return unique_chunks


def generate_chat_response(
    request: ChatRequest,
    answer_mode: str = "sales",
    request_id: str | None = None,
) -> ChatResponse:
    """Turn a chat request into a grounded response with safe fallbacks."""
    started_at = perf_counter()
    try:
        results = search_chunks(
            request.message,
            top_k=CHAT_RETRIEVAL_LIMIT,
            company_id=request.company_id,
        )
    except Exception:
        return ChatResponse(
            answer=(
                "The retrieval service is temporarily unavailable. "
                "Please retry or ask a human teammate for help."
            ),
            needs_human=True,
            confidence="low",
            retrieval_count=0,
            company_id=request.company_id,
            answer_mode=answer_mode,
            request_id=request_id,
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

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
            company_id=request.company_id,
            answer_mode=answer_mode,
            request_id=request_id,
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    retrieved_chunks = []

    for doc, metadata in zip(documents, metadatas):
        if not doc:
            continue
        retrieved_chunks.append(
            {
                "content": doc,
                "filename": metadata.get("filename", "unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
            }
        )

    retrieved_chunks = _dedupe_retrieved_chunks(retrieved_chunks)
    # Ranking after dedupe keeps the LLM context focused on the best evidence.
    retrieved_chunks = _rank_retrieved_chunks(request.message, retrieved_chunks)

    strongest_chunk_score = retrieved_chunks[0].get("relevance_score", 0) if retrieved_chunks else 0
    has_enough_evidence = len(retrieved_chunks) >= MIN_RETRIEVED_CHUNKS or (
        len(retrieved_chunks) == 1 and strongest_chunk_score >= SINGLE_CHUNK_CONFIDENCE_SCORE
    )

    if not has_enough_evidence:
        return ChatResponse(
            answer=(
                "I found some information, but not enough to answer confidently. "
                "Please ask a human teammate for confirmation."
            ),
            needs_human=True,
            confidence="low",
            retrieval_count=len(retrieved_chunks),
            company_id=request.company_id,
            answer_mode=answer_mode,
            request_id=request_id,
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    try:
        answer = generate_grounded_answer(
            user_question=request.message,
            retrieved_chunks=retrieved_chunks[:LLM_CONTEXT_LIMIT],
            conversation_history=request.conversation_history,
            answer_mode=answer_mode,
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
            company_id=request.company_id,
            answer_mode=answer_mode,
            request_id=request_id,
            response_time_ms=int((perf_counter() - started_at) * 1000),
        )

    # We inspect the generated answer so the LLM/fallback can explicitly signal
    # a human handoff without adding another model pass.
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
        company_id=request.company_id,
        answer_mode=answer_mode,
        request_id=request_id,
        response_time_ms=int((perf_counter() - started_at) * 1000),
    )

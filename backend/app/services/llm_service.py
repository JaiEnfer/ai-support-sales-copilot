import re
from functools import lru_cache

from openai import OpenAI

from backend.app.core.config import GROQ_API_KEY, GROQ_MODEL
from backend.app.models.schemas import ChatMessage

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "been",
    "being",
    "between",
    "could",
    "does",
    "from",
    "have",
    "into",
    "just",
    "more",
    "only",
    "over",
    "please",
    "than",
    "that",
    "their",
    "them",
    "they",
    "this",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
}


def _normalize_token(token: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "", token.lower())
    if len(cleaned) > 4 and cleaned.endswith("ing"):
        cleaned = cleaned[:-3]
    elif len(cleaned) > 3 and cleaned.endswith("ed"):
        cleaned = cleaned[:-2]
    elif len(cleaned) > 3 and cleaned.endswith("es"):
        cleaned = cleaned[:-2]
    elif len(cleaned) > 3 and cleaned.endswith("s"):
        cleaned = cleaned[:-1]
    return cleaned


def _extract_query_terms(user_question: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z0-9]+", user_question.lower())
    query_terms: list[str] = []
    for term in raw_terms:
        normalized = _normalize_token(term)
        if len(normalized) < 3 or normalized in STOPWORDS:
            continue
        if normalized not in query_terms:
            query_terms.append(normalized)
    return query_terms


def _score_text(text: str, query_terms: list[str]) -> int:
    normalized_words = [_normalize_token(word) for word in re.findall(r"[A-Za-z0-9]+", text)]
    score = 0

    for term in query_terms:
        if term in normalized_words:
            score += 6
            continue

        for word in normalized_words:
            if not word:
                continue
            if word.startswith(term) or term.startswith(word):
                score += 3
                break
            if len(term) >= 5 and term in word:
                score += 2
                break

    return score


@lru_cache(maxsize=1)
def get_groq_client() -> OpenAI:
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


def _build_extractive_fallback_answer(
    user_question: str,
    retrieved_chunks: list[dict],
) -> str:
    query_terms = _extract_query_terms(user_question)
    if not query_terms:
        query_terms = [_normalize_token(user_question)]

    ranked_highlights: list[tuple[int, str]] = []
    for item in retrieved_chunks:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", item["content"].replace("\n", " "))
            if sentence.strip()
        ]
        if not sentences:
            sentences = [item["content"].strip()]

        for sentence in sentences:
            score = _score_text(sentence, query_terms)
            if score <= 0:
                continue
            ranked_highlights.append((score, sentence.strip()[:240].rstrip(". ")))

    if not ranked_highlights:
        return (
            "I could not find a clear answer to that exact question in the uploaded documents. "
            "If you want, I can help narrow it down with a more specific question."
        )

    ranked_highlights.sort(key=lambda item: item[0], reverse=True)

    unique_highlights: list[str] = []
    for _, highlight in ranked_highlights:
        if highlight not in unique_highlights:
            unique_highlights.append(highlight)

    summary_lines = unique_highlights[:2]

    if len(summary_lines) == 1:
        summary_text = summary_lines[0]
    elif len(summary_lines) == 2:
        summary_text = f"{summary_lines[0]}. {summary_lines[1]}"
    else:
        summary_text = f"{summary_lines[0]}. {summary_lines[1]}. {summary_lines[2]}"

    return summary_text.strip()


def generate_grounded_answer(
    user_question: str,
    retrieved_chunks: list[dict],
    conversation_history: list[ChatMessage] | None = None
) -> str:
    if not GROQ_API_KEY:
        return _build_extractive_fallback_answer(user_question, retrieved_chunks)

    context_blocks = []
    for index, item in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[Context {index}]\n{item['content']}"
        )

    combined_context = "\n\n".join(context_blocks)

    history_text = ""
    if conversation_history:
        rendered_history = []
        for msg in conversation_history[-6:]:
            rendered_history.append(f"{msg.role.upper()}: {msg.content}")
        history_text = "\n".join(rendered_history)

    client = get_groq_client()

    prompt = f"""
You are an AI customer support and sales copilot for a startup company.

Answer the user's question using ONLY the provided context.
Use prior conversation only to understand the user's intent, but never use it as factual evidence.
If the context is insufficient, say clearly that you are not confident and suggest human follow-up.
Do not invent policies, pricing, guarantees, or features.
Write like a real customer support teammate: clear, natural, helpful, and direct.
Do not mention source numbers, chunk numbers, or filenames in the final answer unless the user explicitly asks.
Prefer a short paragraph over bullets unless bullets are clearly better for readability.

Conversation history:
{history_text if history_text else "No prior conversation."}

User question:
{user_question}

Context:
{combined_context}
""".strip()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You answer only from the provided retrieved context. "
                    "Reply in a natural, human support style that directly answers the user's question."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.35
    )

    return response.choices[0].message.content.strip()

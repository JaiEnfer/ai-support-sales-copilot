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
SOURCE_PREFIXES = (
    "business overview:",
    "contact signals:",
    "entity name:",
    "key skills:",
    "meta description:",
    "page title:",
    "primary roles:",
    "products or platforms:",
    "profile highlights:",
    "services and offerings:",
    "source pages:",
    "source url:",
    "website summary",
)


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


def _clean_answer_fragment(text: str) -> str:
    """Remove summary labels and source metadata from extracted snippets."""
    cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip(" -:;,.")
    lowered = cleaned.lower()

    for prefix in SOURCE_PREFIXES:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip(" -:;,.")
            lowered = cleaned.lower()

    cleaned = re.sub(r"Source URL:\s*\S+", "", cleaned, flags=re.IGNORECASE).strip(" -:;,.")
    cleaned = re.sub(r"Page title:\s*", "", cleaned, flags=re.IGNORECASE).strip(" -:;,.")
    return cleaned


def _format_direct_answer(user_question: str, summary_lines: list[str]) -> str:
    """Format extracted evidence into a polished chatbot-style answer."""
    cleaned_lines = [_clean_answer_fragment(line) for line in summary_lines]
    cleaned_lines = [line for line in cleaned_lines if line]
    if not cleaned_lines:
        return (
            "I could not find a clear answer to that exact question in the uploaded documents. "
            "If you want, I can help narrow it down with a more specific question."
        )

    if len(cleaned_lines) == 1:
        primary = cleaned_lines[0].rstrip(".")
        if primary.lower().startswith(("yes", "no")):
            return f"{primary}."
        if "key skill" in user_question.lower() or "skills" in user_question.lower():
            return f"Key skills include {primary[0].lower() + primary[1:] if len(primary) > 1 else primary}."
        return primary[0].upper() + primary[1:] + "."

    question = user_question.lower()
    first_line = cleaned_lines[0].rstrip(".")
    second_line = cleaned_lines[1].rstrip(".")

    if question.startswith(("who is", "who's")):
        return f"{first_line[0].upper() + first_line[1:]}. {second_line}."

    if "key skill" in question or "skills" in question:
        return f"{first_line[0].upper() + first_line[1:]}. Key skills include {second_line[0].lower() + second_line[1:]}."

    if "service" in question or "offer" in question or "provide" in question:
        return f"{first_line[0].upper() + first_line[1:]}. They also {second_line[0].lower() + second_line[1:]}."

    return f"{first_line[0].upper() + first_line[1:]}. {second_line}."


def _apply_answer_mode(answer: str, answer_mode: str) -> str:
    """Shape a grounded answer for the selected company tone."""
    normalized = answer.strip()
    if not normalized:
        return normalized

    if answer_mode == "support":
        return normalized

    if answer_mode == "portfolio":
        if normalized.lower().startswith(("he ", "she ", "they ", "jai ", "the company ")):
            return normalized
        return f"{normalized}"

    # sales mode is the default: sound confident and outcome-oriented.
    if answer_mode == "sales" and not normalized.lower().startswith(("yes", "no")):
        return normalized

    return normalized


def _system_tone_instructions(answer_mode: str) -> str:
    """Return tone instructions used by both fallback and LLM responses."""
    if answer_mode == "support":
        return (
            "Write in a calm, helpful support tone. Be direct, reassuring, and practical. "
            "Focus on what the user needs to know right now."
        )

    if answer_mode == "portfolio":
        return (
            "Write in a polished professional profile tone. Highlight roles, experience, skills, "
            "projects, and credibility in a concise way."
        )

    return (
        "Write in a polished sales-demo tone. Lead with the answer clearly, sound confident, "
        "and emphasize value, expertise, services, or outcomes when supported by context."
    )


@lru_cache(maxsize=1)
def get_groq_client() -> OpenAI:
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


def _build_extractive_fallback_answer(
    user_question: str,
    retrieved_chunks: list[dict],
    answer_mode: str = "sales",
) -> str:
    """Build a readable answer from the best matching retrieved evidence."""
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
            cleaned_sentence = _clean_answer_fragment(sentence)
            if sentence != cleaned_sentence:
                score -= 3
            if cleaned_sentence.lower().startswith(("page title", "source url")):
                score -= 6
            if score <= 0:
                continue
            ranked_highlights.append((score, cleaned_sentence[:240].rstrip(". ")))

    if not ranked_highlights:
        return _apply_answer_mode(
            (
            "I could not find a clear answer to that exact question in the uploaded documents. "
            "If you want, I can help narrow it down with a more specific question."
            ),
            answer_mode,
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

    return _apply_answer_mode(_format_direct_answer(user_question, summary_lines), answer_mode)


def generate_grounded_answer(
    user_question: str,
    retrieved_chunks: list[dict],
    conversation_history: list[ChatMessage] | None = None,
    answer_mode: str = "sales",
) -> str:
    """Generate an LLM answer when available, else degrade to local extraction."""
    if not GROQ_API_KEY:
        return _build_extractive_fallback_answer(user_question, retrieved_chunks, answer_mode=answer_mode)

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
{_system_tone_instructions(answer_mode)}
Lead with the answer directly instead of repeating the question.

Conversation history:
{history_text if history_text else "No prior conversation."}

User question:
{user_question}

Context:
{combined_context}
""".strip()

    try:
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
        return _apply_answer_mode(response.choices[0].message.content.strip(), answer_mode)
    except Exception:
        # Demos should still produce a grounded answer even if the external
        # model provider is unavailable or the key is invalid.
        return _build_extractive_fallback_answer(user_question, retrieved_chunks, answer_mode=answer_mode)

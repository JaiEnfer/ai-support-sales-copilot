from openai import OpenAI
from backend.app.core.config import GROQ_API_KEY, GROQ_MODEL


def generate_grounded_answer(user_question: str, retrieved_chunks: list[dict]) -> str:
    if not GROQ_API_KEY:
        return (
            "The language model is not configured yet. "
            "Please set the GROQ_API_KEY environment variable."
        )

    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

    context_blocks = []

    for index, item in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[Source {index}] Filename: {item['filename']} | Chunk: {item['chunk_index']}\n"
            f"{item['content']}"
        )

    combined_context = "\n\n".join(context_blocks)

    prompt = f"""
You are an AI customer support and sales copilot for a startup company.

Answer the user's question using ONLY the provided context.
If the context is insufficient, say clearly that you are not confident and suggest human follow-up.
Do not invent policies, pricing, guarantees, or features.
Be concise and professional.
After the answer, add a short section called "Sources" listing the source numbers you relied on.

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
                "content": "You answer only from the provided retrieved context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
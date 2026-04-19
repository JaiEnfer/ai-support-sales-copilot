import sys
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from backend.app.models.schemas import ChatMessage
from backend.app.services import llm_service, vector_store
from backend.app.services.vector_store import add_document_chunks

SAMPLE_DOC_PATH = Path(__file__).resolve().parent.parent / "data" / "sample-company-handbook.md"


def _force_local_demo_mode(temp_dir: Path) -> None:
    vector_store.FALLBACK_INDEX_PATH = temp_dir / "fallback_chunks.json"
    vector_store.get_chroma_client.cache_clear()
    vector_store.get_embedding_function.cache_clear()
    vector_store.get_collection.cache_clear()
    llm_service.get_groq_client.cache_clear()
    llm_service.GROQ_API_KEY = None

    def _disabled_collection():
        raise RuntimeError("Semantic index disabled for local demo mode.")

    vector_store.get_collection = _disabled_collection


def _build_demo_chunks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def run_demo() -> None:
    demo_runtime_dir = ROOT_DIR / "backend" / "data" / "_demo_runtime"
    shutil.rmtree(demo_runtime_dir, ignore_errors=True)
    demo_runtime_dir.mkdir(parents=True, exist_ok=True)

    _force_local_demo_mode(demo_runtime_dir)

    sample_text = SAMPLE_DOC_PATH.read_text(encoding="utf-8")
    chunks = _build_demo_chunks(sample_text)
    add_document_chunks(
        document_id="brightpath-demo-doc",
        filename=SAMPLE_DOC_PATH.name,
        chunks=chunks,
    )

    client = TestClient(app)
    conversation_history: list[ChatMessage | dict[str, str]] = []
    questions = [
        "Hey, I'm looking at BrightPath AI. How long does onboarding usually take on the Growth plan?",
        "Nice. Do you integrate with Salesforce and Slack on that plan?",
        "What happens if we go over the monthly workflow limit?",
        "One more thing: is EU data residency already included, or would we need something extra?",
    ]

    print("Sample document:", SAMPLE_DOC_PATH.name)
    print()

    for question in questions:
        response = client.post(
            "/api/chat",
            json={
                "message": question,
                "conversation_history": conversation_history,
                "company_id": "brightpath-demo",
            },
        )
        payload = response.json()
        answer = payload["answer"]

        print(f"User: {question}")
        print(f"Assistant: {answer}")
        print(
            "Metadata:",
            {
                "confidence": payload["confidence"],
                "needs_human": payload["needs_human"],
                "retrieval_count": payload["retrieval_count"],
            },
        )
        print()

        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    run_demo()

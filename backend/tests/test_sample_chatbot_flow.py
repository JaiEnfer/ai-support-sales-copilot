from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import llm_service, vector_store
from backend.app.services.vector_store import add_document_chunks

SAMPLE_DOC_PATH = Path(__file__).resolve().parent.parent / "data" / "sample-company-handbook.md"
client = TestClient(app)


def _disable_semantic_index(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vector_store, "FALLBACK_INDEX_PATH", tmp_path / "fallback_chunks.json")
    vector_store.get_chroma_client.cache_clear()
    vector_store.get_embedding_function.cache_clear()
    vector_store.get_collection.cache_clear()
    llm_service.get_groq_client.cache_clear()
    monkeypatch.setattr(llm_service, "GROQ_API_KEY", None)

    def _disabled_collection():
        raise RuntimeError("Semantic index disabled for deterministic tests.")

    monkeypatch.setattr(vector_store, "get_collection", _disabled_collection)


def _build_demo_chunks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def test_sample_chatbot_flow(monkeypatch):
    runtime_dir = Path(__file__).resolve().parent / ".tmp_sample_chatbot"
    shutil.rmtree(runtime_dir, ignore_errors=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    _disable_semantic_index(monkeypatch, runtime_dir)

    sample_text = SAMPLE_DOC_PATH.read_text(encoding="utf-8")
    chunks = _build_demo_chunks(sample_text)
    add_document_chunks(
        document_id="sample-doc",
        filename=SAMPLE_DOC_PATH.name,
        chunks=chunks,
    )

    onboarding_response = client.post(
        "/api/chat",
        json={
            "message": "For the Growth plan, when do customers usually launch during onboarding?",
            "conversation_history": [],
            "company_id": "demo-company",
        },
    )
    assert onboarding_response.status_code == 200
    onboarding_data = onboarding_response.json()
    assert "5 to 10 business days" in onboarding_data["answer"]
    assert onboarding_data["retrieval_count"] >= 1

    follow_up_response = client.post(
        "/api/chat",
        json={
            "message": "And do you already include EU data residency on that plan?",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "For the Growth plan, when do customers usually launch during onboarding?",
                },
                {
                    "role": "assistant",
                    "content": onboarding_data["answer"],
                },
            ],
            "company_id": "demo-company",
        },
    )
    assert follow_up_response.status_code == 200
    follow_up_data = follow_up_response.json()
    assert (
        "EU data residency is not included by default" in follow_up_data["answer"]
        or "EU data residency add-on" in follow_up_data["answer"]
    )

    shutil.rmtree(runtime_dir, ignore_errors=True)

from io import BytesIO

from fastapi.testclient import TestClient

from backend.app.api import company_profile as company_profile_api
from backend.app.api import company_access as company_access_api
from backend.app.api import documents as documents_api
from backend.app.services import chat_service
from backend.app.services.company_admin_auth import create_company_admin_token, hash_company_access_key
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.schemas import CompanyProfile

client = TestClient(app)


def _admin_headers(company_id: str = "startup-demo-001") -> dict[str, str]:
    headers = {"X-Company-ID": company_id}
    if settings.admin_api_key:
        headers["X-API-Key"] = settings.admin_api_key
    return headers


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "AI Support + Sales Copilot"


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "request_id" in response.json()
    assert response.headers["X-Request-ID"]


def test_chat_without_documents():
    payload = {
        "message": "What does your pricing include?",
        "conversation_history": [],
        "company_id": "startup-demo-001"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "needs_human" in data


def test_upload_non_pdf_rejected():
    fake_file = BytesIO(b"hello world")
    response = client.post(
        "/api/documents/upload",
        headers=_admin_headers(),
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported right now."


def test_retrieve_request_validation():
    response = client.post(
        "/api/documents/retrieve",
        headers=_admin_headers(),
        json={"query": "pricing", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "pricing"
    assert "results" in data


def test_list_documents():
    response = client.get("/api/documents", headers=_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data

def test_chat_with_conversation_history():
    payload = {
        "message": "Can you clarify that?",
        "conversation_history": [
            {"role": "user", "content": "What does your pricing include?"},
            {"role": "assistant", "content": "It includes setup and analytics."}
        ],
        "company_id": "startup-demo-001"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "needs_human" in data
    assert data["company_id"] == "startup-demo-001"


def test_documents_require_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "secret-admin-key")

    response = client.get("/api/documents")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing company admin credentials."

    authorized_response = client.get(
        "/api/documents",
        headers={"X-API-Key": "secret-admin-key"},
    )
    assert authorized_response.status_code == 200

    monkeypatch.setattr(settings, "admin_api_key", None)


def test_chat_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "chat_api_key", "secret-chat-key")

    response = client.post(
        "/api/chat",
        json={"message": "hello", "conversation_history": [], "company_id": "tenant-1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."

    authorized_response = client.post(
        "/api/chat",
        headers={"X-API-Key": "secret-chat-key", "X-Company-ID": "tenant-1"},
        json={"message": "hello", "conversation_history": []},
    )
    assert authorized_response.status_code == 200
    assert authorized_response.json()["company_id"] == "tenant-1"

    monkeypatch.setattr(settings, "chat_api_key", None)


def test_company_admin_login_returns_scoped_session(monkeypatch):
    monkeypatch.setattr(settings, "company_admin_token_secret", "token-secret")
    monkeypatch.setattr(
        company_access_api,
        "get_company_profile_record",
        lambda company_id: {
            "company_id": company_id,
            "company_access_key_hash": hash_company_access_key("tenant-secret-key"),
        },
    )
    monkeypatch.setattr(
        company_access_api,
        "get_company_profile",
        lambda company_id: CompanyProfile(
            company_id=company_id,
            display_name="Tenant Portal",
            answer_mode="support",
            chatbot_title="Tenant Assistant",
            chatbot_subtitle="Ask for help.",
        ),
    )

    response = client.post(
        "/api/company-access/login",
        json={"company_id": "tenant-login", "company_access_key": "tenant-secret-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == "tenant-login"
    assert payload["access_token"]
    assert payload["profile"]["display_name"] == "Tenant Portal"


def test_company_bearer_token_is_scoped_to_matching_company(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", None)
    monkeypatch.setattr(settings, "company_admin_token_secret", "token-secret")
    scoped_token = create_company_admin_token("tenant-portal")
    monkeypatch.setattr(documents_api, "load_documents", lambda: [])

    authorized_response = client.get(
        "/api/documents",
        headers={
            "Authorization": f"Bearer {scoped_token}",
            "X-Company-ID": "tenant-portal",
        },
    )
    assert authorized_response.status_code == 200

    wrong_company_response = client.get(
        "/api/documents",
        headers={
            "Authorization": f"Bearer {scoped_token}",
            "X-Company-ID": "another-tenant",
        },
    )
    assert wrong_company_response.status_code == 401


def test_document_list_is_scoped_to_company_header(monkeypatch):
    monkeypatch.setattr(
        documents_api,
        "load_documents",
        lambda: [
            {
                "company_id": "tenant-1",
                "document_id": "doc-1",
                "filename": "tenant-1.pdf",
                "chunks_created": 3,
                "created_at": "2026-01-01T00:00:00+00:00",
                "file_size_bytes": 123,
                "status": "ready",
            },
            {
                "company_id": "tenant-2",
                "document_id": "doc-2",
                "filename": "tenant-2.pdf",
                "chunks_created": 4,
                "created_at": "2026-01-02T00:00:00+00:00",
                "file_size_bytes": 456,
                "status": "ready",
            },
        ],
    )

    response = client.get("/api/documents", headers=_admin_headers("tenant-1"))
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["company_id"] == "tenant-1"


def test_chat_search_uses_company_scope(monkeypatch):
    captured: dict[str, str | None] = {"company_id": None}

    def _fake_search(query: str, top_k: int = 4, company_id: str | None = None):
        captured["company_id"] = company_id
        return {"documents": [[]], "metadatas": [[]]}

    monkeypatch.setattr(chat_service, "search_chunks", _fake_search)

    response = client.post(
        "/api/chat",
        headers={"X-Company-ID": "tenant-search"},
        json={"message": "hello", "conversation_history": []},
    )

    assert response.status_code == 200
    assert captured["company_id"] == "tenant-search"


def test_chat_can_answer_from_single_strong_chunk(monkeypatch):
    def _fake_search(query: str, top_k: int = 4, company_id: str | None = None):
        return {
            "documents": [[
                "Acme Dental offers emergency dental care, implants, whitening, and same-day appointments."
            ]],
            "metadatas": [[
                {
                    "filename": "website-acme-dental.txt",
                    "chunk_index": 0,
                }
            ]],
        }

    monkeypatch.setattr(chat_service, "search_chunks", _fake_search)
    monkeypatch.setattr(
        chat_service,
        "generate_grounded_answer",
        lambda user_question, retrieved_chunks, conversation_history, answer_mode="sales": "Acme Dental offers emergency care, implants, whitening, and same-day appointments.",
    )

    response = client.post(
        "/api/chat",
        headers={"X-Company-ID": "tenant-one-chunk"},
        json={"message": "What services does Acme Dental offer?", "conversation_history": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["needs_human"] is False
    assert "same-day appointments" in payload["answer"]


def test_profile_queries_prefer_summary_chunks(monkeypatch):
    def _fake_search(query: str, top_k: int = 4, company_id: str | None = None):
        return {
            "documents": [[
                "Page title: Jai Prakash - DATA SCIENTIST | MACHINE LEARNING ENGINEER | AI ENGINEER Source URL: https://portfolio.example.com Company Overview FlowTask AI is a SaaS platform.",
                "Website Summary\nEntity name: Jai Prakash\nPrimary roles: Data Scientist, Machine Learning Engineer, Ai Engineer\nKey skills: Python, Machine Learning, Generative Ai, Automation\nProfile highlights:\n- Jai Prakash is a Data Scientist and Machine Learning Engineer.\n- He builds AI assistants and automation systems.",
            ]],
            "metadatas": [[
                {"filename": "website-profile.txt", "chunk_index": 1},
                {"filename": "website-profile.txt", "chunk_index": 0},
            ]],
        }

    def _fake_answer(user_question: str, retrieved_chunks: list[dict], conversation_history, answer_mode="sales"):
        return retrieved_chunks[0]["content"]

    monkeypatch.setattr(chat_service, "search_chunks", _fake_search)
    monkeypatch.setattr(chat_service, "generate_grounded_answer", _fake_answer)

    response = client.post(
        "/api/chat",
        headers={"X-Company-ID": "tenant-profile"},
        json={"message": "Who is Jai and what are his key skills?", "conversation_history": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("Website Summary")


def test_scrape_website_indexes_company_content(monkeypatch):
    captured: dict[str, str | int | None] = {"company_id": None, "chunks_created": None}

    async def _fake_scrape(url: str, max_pages: int):
        return [
            {
                "url": "https://example.com",
                "title": "Example Home",
                "content": "We offer onboarding, pricing help, and Slack integrations.",
            }
        ]

    def _fake_add_document_chunks(
        document_id: str,
        company_id: str,
        filename: str,
        chunks: list[str],
    ) -> int:
        captured["company_id"] = company_id
        captured["chunks_created"] = len(chunks)
        return len(chunks)

    monkeypatch.setattr(documents_api, "scrape_website_text", _fake_scrape)
    monkeypatch.setattr(documents_api, "add_document_chunks", _fake_add_document_chunks)
    monkeypatch.setattr(documents_api, "add_document_record", lambda record: None)

    response = client.post(
        "/api/documents/scrape",
        headers=_admin_headers("tenant-web"),
        json={"url": "https://example.com", "max_pages": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == "tenant-web"
    assert payload["pages_scraped"] == 1
    assert captured["company_id"] == "tenant-web"
    assert isinstance(captured["chunks_created"], int)


def test_company_profile_can_be_read_and_updated(monkeypatch):
    monkeypatch.setattr(
        company_profile_api,
        "get_company_profile",
        lambda company_id: CompanyProfile(
            company_id=company_id,
            display_name="Tenant Profile",
            answer_mode="sales",
            chatbot_title="AI Assistant",
            chatbot_subtitle="Ask anything.",
        ),
    )

    updated_profile = CompanyProfile(
        company_id="tenant-profile",
        display_name="Tenant Profile",
        answer_mode="portfolio",
        chatbot_title="Portfolio Assistant",
        chatbot_subtitle="Ask about work and skills.",
    )

    monkeypatch.setattr(
        company_profile_api,
        "upsert_company_profile",
        lambda company_id, updates: updated_profile,
    )

    get_response = client.get("/api/company-profile", headers=_admin_headers("tenant-profile"))
    assert get_response.status_code == 200
    assert get_response.json()["answer_mode"] == "sales"

    put_response = client.put(
        "/api/company-profile",
        headers=_admin_headers("tenant-profile") | {"Content-Type": "application/json"},
        json={
            "answer_mode": "portfolio",
            "chatbot_title": "Portfolio Assistant",
            "chatbot_subtitle": "Ask about work and skills.",
        },
    )
    assert put_response.status_code == 200
    assert put_response.json()["answer_mode"] == "portfolio"


def test_clear_company_documents_removes_all_tenant_records(monkeypatch):
    monkeypatch.setattr(
        documents_api,
        "delete_company_documents",
        lambda company_id: [
            {
                "company_id": company_id,
                "document_id": "doc-1",
                "filename": "one.pdf",
                "stored_filename": None,
            },
            {
                "company_id": company_id,
                "document_id": "doc-2",
                "filename": "two.pdf",
                "stored_filename": None,
            },
        ],
    )

    deleted_ids: list[str] = []
    monkeypatch.setattr(
        documents_api,
        "delete_document_chunks",
        lambda document_id, company_id=None: deleted_ids.append(document_id),
    )

    response = client.delete("/api/documents", headers=_admin_headers("tenant-clear"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == "tenant-clear"
    assert payload["deleted_documents"] == 2
    assert payload["status"] == "cleared"
    assert deleted_ids == ["doc-1", "doc-2"]

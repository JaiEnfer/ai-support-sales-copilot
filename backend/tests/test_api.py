from io import BytesIO
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "AI Support + Sales Copilot"


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported right now."


def test_retrieve_request_validation():
    response = client.post(
        "/api/documents/retrieve",
        json={"query": "pricing", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "pricing"
    assert "results" in data


def test_list_documents():
    response = client.get("/api/documents")
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

from typing import List, Optional

from pydantic import BaseModel, Field

ANSWER_MODE_VALUES = ("sales", "support", "portfolio")


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str = Field(..., min_length=1, examples=["What does your pricing include?"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, examples=["Do you offer integrations with Slack?"])
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    company_id: Optional[str] = Field(default=None, examples=["startup-demo-001"])


class ChatResponse(BaseModel):
    answer: str
    needs_human: bool = False
    confidence: str = "low"
    retrieval_count: int = 0
    response_time_ms: int = 0
    company_id: Optional[str] = None
    answer_mode: Optional[str] = None
    request_id: Optional[str] = None


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    company_id: Optional[str] = None
    document_id: Optional[str] = None
    chunks_created: Optional[int] = None
    uploaded_at: Optional[str] = None
    file_size_bytes: Optional[int] = None


class WebsiteScrapeRequest(BaseModel):
    url: str = Field(..., min_length=8, examples=["https://example.com"])
    max_pages: int = Field(default=4, ge=1, le=12)


class WebsiteScrapeResponse(BaseModel):
    document_id: str
    company_id: str
    status: str
    message: str
    source_url: str
    pages_scraped: int
    chunks_created: int


class DeleteDocumentResponse(BaseModel):
    company_id: str
    document_id: str
    filename: str
    status: str
    message: str


class ClearTenantResponse(BaseModel):
    company_id: str
    deleted_documents: int
    status: str
    message: str


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)


class RetrievedChunk(BaseModel):
    content: str
    filename: str
    chunk_index: int


class RetrieveResponse(BaseModel):
    query: str
    results: List[RetrievedChunk] = Field(default_factory=list)
    total_results: int = 0
    request_id: Optional[str] = None


class DocumentRecord(BaseModel):
    company_id: str
    document_id: str
    filename: str
    chunks_created: int
    created_at: str
    file_size_bytes: int
    status: str = "ready"


class DocumentListResponse(BaseModel):
    documents: List[DocumentRecord] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    company_id: str
    display_name: str
    answer_mode: str = Field(default="sales", pattern="^(sales|support|portfolio)$")
    chatbot_title: str = "AI Assistant"
    chatbot_subtitle: str = "Ask anything about this business."


class CompanyProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    answer_mode: Optional[str] = Field(default=None, pattern="^(sales|support|portfolio)$")
    chatbot_title: Optional[str] = None
    chatbot_subtitle: Optional[str] = None


class CompanyAdminLoginRequest(BaseModel):
    company_id: str = Field(..., min_length=1, examples=["acme-dental"])
    company_access_key: str = Field(..., min_length=8, examples=["acme-super-secret-key"])


class CompanyAdminSessionResponse(BaseModel):
    company_id: str
    access_token: str
    expires_in_seconds: int
    profile: CompanyProfile


class CompanyAdminProvisionRequest(BaseModel):
    company_id: str = Field(..., min_length=1, examples=["acme-dental"])
    company_access_key: str = Field(..., min_length=8, examples=["acme-super-secret-key"])
    display_name: Optional[str] = None
    answer_mode: Optional[str] = Field(default=None, pattern="^(sales|support|portfolio)$")
    chatbot_title: Optional[str] = None
    chatbot_subtitle: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    llm_configured: bool
    model: str
    documents_indexed: int
    request_id: Optional[str] = None
    checks: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    request_id: Optional[str] = None

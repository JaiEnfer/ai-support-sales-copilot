from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str = Field(..., min_length=1, examples=["What does your pricing include?"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Do you offer integrations with Slack?"])
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    company_id: Optional[str] = Field(default=None, examples=["startup-demo-001"])


class ChatResponse(BaseModel):
    answer: str
    needs_human: bool = False
    confidence: str = "low"
    retrieval_count: int = 0
    response_time_ms: int = 0


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    document_id: Optional[str] = None
    chunks_created: Optional[int] = None
    uploaded_at: Optional[str] = None
    file_size_bytes: Optional[int] = None


class DeleteDocumentResponse(BaseModel):
    document_id: str
    filename: str
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


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    created_at: str
    file_size_bytes: int
    status: str = "ready"


class DocumentListResponse(BaseModel):
    documents: List[DocumentRecord] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    llm_configured: bool
    model: str
    documents_indexed: int

from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str = Field(..., min_length=1, examples=["What does your pricing include?"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Do you offer integrations with Slack?"])
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    company_id: Optional[str] = Field(default=None, examples=["startup-demo-001"])


class SourceItem(BaseModel):
    title: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
    needs_human: bool = False


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    document_id: Optional[str] = None
    chunks_created: Optional[int] = None


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
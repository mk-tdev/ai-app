"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Role(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message model."""
    role: Role
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    use_rag: bool = Field(False, description="Whether to use RAG for context")


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    conversation_id: str
    sources: Optional[list[str]] = None


class StreamEvent(BaseModel):
    """SSE stream event model."""
    event: str
    data: str


class DocumentRequest(BaseModel):
    """Document ingestion request."""
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Optional[dict] = Field(default_factory=dict, description="Document metadata")


class DocumentResponse(BaseModel):
    """Document ingestion response."""
    id: str
    message: str


class DocumentUploadResponse(BaseModel):
    """Response for document file upload."""
    id: str
    filename: str
    status: str  # "uploaded", "duplicate", "error"
    message: str
    chunks_created: int = 0


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: list[dict]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool


class SessionMessage(BaseModel):
    """Message in a conversation session."""
    role: str
    content: str
    timestamp: str


class ConversationHistory(BaseModel):
    """Conversation history for a session."""
    session_id: str
    messages: list[SessionMessage]
    total_messages: int

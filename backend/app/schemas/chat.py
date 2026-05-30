from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ─── Conversation Schemas ─────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


# ─── Chat Request/Response ────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None   # None = new conversation
    device_id: Optional[str] = None         # for routing commands


class ChatResponse(BaseModel):
    conversation_id: int
    message: MessageResponse
    intent: Optional[str] = None            # detected intent type
    command: Optional[dict] = None          # if action was dispatched

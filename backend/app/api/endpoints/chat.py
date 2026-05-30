"""
IRIS AI — Chat Endpoints
HTTP-based chat API (WebSocket is used for real-time streaming).
Handles conversation management and LLM interaction.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    ConversationResponse, ConversationListItem, MessageResponse,
)
from app.services.llm import llm_service
from app.services.memory import memory_manager
from app.services.automation_service import automation_service
from app.api.deps import get_current_user

router = APIRouter()


def _get_conversation_history(conversation: Conversation) -> List[dict]:
    """Convert DB messages to LLM-compatible history format."""
    return [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
    ]


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to IRIS. Creates or continues a conversation.
    Returns LLM response + any dispatched device commands.
    """
    # ── Get or create conversation ────────────────────────────────────────────
    if body.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == body.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        # Auto-title: first 60 chars of the message
        title = body.message[:60] + ("..." if len(body.message) > 60 else "")
        conversation = Conversation(user_id=current_user.id, title=title)
        db.add(conversation)
        db.flush()

    # ── Save user message ─────────────────────────────────────────────────────
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    db.flush()

    # ── Build context ─────────────────────────────────────────────────────────
    history = _get_conversation_history(conversation)
    memory_ctx = memory_manager.build_context_string(current_user.id, body.message)
    user_info = f"Name: {current_user.full_name or current_user.email}"

    # ── LLM call ──────────────────────────────────────────────────────────────
    result = llm_service.generate_response(
        user_message=body.message,
        conversation_history=history,
        memory_context=memory_ctx,
        user_info=user_info,
    )

    # ── Save assistant message ────────────────────────────────────────────────
    ai_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["content"],
        tokens_used=result.get("tokens_used"),
        model_used=result.get("model_used"),
    )
    db.add(ai_msg)

    # ── Store interaction in long-term memory ─────────────────────────────────
    memory_manager.add_memory(
        user_id=current_user.id,
        text=f"User said: {body.message}\nIRIS replied: {result['content']}",
        metadata={"type": "conversation", "conversation_id": str(conversation.id)},
    )

    # ── Dispatch device command if detected ───────────────────────────────────
    dispatch_result = None
    if result.get("command") and result.get("intent"):
        dispatch_result = await automation_service.dispatch_command(
            user_id=current_user.id,
            intent=result["intent"],
            command=result["command"],
            target_device_id=body.device_id,
        )

    db.commit()
    db.refresh(ai_msg)

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(ai_msg),
        intent=result.get("intent"),
        command=dispatch_result,
    )


@router.get("/conversations", response_model=List[ConversationListItem])
def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the current user."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for c in conversations:
        result.append(ConversationListItem(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        ))
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a conversation with full message history."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conversation)
    db.commit()
